"""
Content Organization Service
AI-assisted analysis and organization of PDF content
"""

import json
import re
from typing import List, Dict, Optional
from collections import defaultdict
from utils.ollama_client import get_ollama_client


class ContentOrganizer:
    """Service for analyzing and organizing scattered PDF content"""
    
    def __init__(self):
        """Initialize content organizer"""
        from config.knowledge_base import config
        
        self.ollama = get_ollama_client()
        self.config = config
    
    def analyze_content_structure(
        self,
        pages_data: List[Dict],
        document_name: str,
        use_llm: bool = True
    ) -> Dict:
        """
        Analyze PDF content to identify topics and suggest organization
        
        Args:
            pages_data: List of dicts with page_number and text
            document_name: Name of the document
            use_llm: Whether to use LLM for intelligent analysis (default: True)
            
        Returns:
            Dict with analysis results and organization proposals
        """
        print(f"[INFO] Analyzing content structure for: {document_name}")
        
        try:
            # First, extract potential topics from each page
            topics_by_page = self._extract_topics_from_pages(pages_data)
            print(f"[INFO] Extracted topics from {len(topics_by_page)} pages")
            
            # Identify duplicate/similar topics across pages
            topic_clusters = self._cluster_similar_topics(topics_by_page)
            print(f"[INFO] Found {len(topic_clusters)} topic clusters")
            
            # Try LLM-based intelligent analysis if requested and available
            if use_llm and self.ollama.is_available():
                print(f"[INFO] Using LLM for intelligent analysis...")
                proposals = self._generate_llm_proposals(
                    topic_clusters,
                    pages_data,
                    document_name
                )
                print(f"[INFO] Generated {len(proposals)} LLM-based proposals")
            else:
                if use_llm:
                    print(f"[WARN] LLM not available, using simple proposals")
                proposals = self._generate_simple_proposals(pages_data, document_name)
                print(f"[INFO] Generated {len(proposals)} simple proposals")
                
        except Exception as e:
            print(f"[ERROR] Analysis failed: {str(e)}")
            # Fallback to simple proposals
            proposals = self._generate_simple_proposals(pages_data, document_name)
        
        return {
            'status': 'success',
            'proposals': proposals
        }
    
    def _generate_simple_proposals(
        self,
        pages_data: List[Dict],
        document_name: str
    ) -> List[Dict]:
        """
        Generate simple proposals without LLM (Fallback)
        Creates one proposal per document
        """
        if not pages_data:
            return []
        
        # Extract document title
        doc_title = document_name.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        
        # Get page numbers
        page_numbers = [p['page_number'] for p in pages_data]
        
        # Create proposal
        proposal = {
            'type': 'section',
            'title': doc_title,
            'description': f'Add "{doc_title}" as a chapter ({len(pages_data)} pages)',
            'affected_pages': ','.join(map(str, page_numbers)),
            'confidence': 'medium'
        }
        
        return [proposal]
    
    def _generate_llm_proposals(
        self,
        topic_clusters: List[Dict],
        pages_data: List[Dict],
        document_name: str
    ) -> List[Dict]:
        """
        Use LLM to generate intelligent organization proposals
        Analyzes topics, suggests merges, and proposes structure
        
        Args:
            topic_clusters: Clustered topics from pages
            pages_data: Original page data
            document_name: Document name
            
        Returns:
            List of organization proposals
        """
        proposals = []
        
        # Analyze top topic clusters with LLM
        for cluster in topic_clusters[:10]:  # Top 10 most frequent topics
            try:
                # Get text snippets from pages with this topic
                affected_texts = []
                for page_num in cluster['pages'][:5]:  # Max 5 pages per cluster
                    page_info = next((p for p in pages_data if p['page_number'] == page_num), None)
                    if page_info:
                        text = page_info['text'][:400]  # First 400 chars
                        affected_texts.append(f"Page {page_num}: {text}")
                
                if not affected_texts:
                    continue
                
                context = "\n\n".join(affected_texts)
                
                # Build LLM prompt for analysis
                prompt = f"""You are analyzing swing trading educational notes. A topic appears on multiple pages.

Topic: "{cluster['normalized_topic']}"
Pages: {', '.join(map(str, cluster['pages']))}

Sample content from these pages:
{context}

Analyze this scattered content and suggest organization:
1. Should these pages be merged into one comprehensive section?
2. What should be the final section title?
3. What's the main learning objective?
4. Any suggested ordering?

Respond in JSON format:
{{
    "action": "merge",
    "title": "suggested section title",
    "description": "brief description of why and what this section covers",
    "learning_objective": "what students will learn",
    "confidence": "high/medium/low"
}}"""

                # Call LLM
                response = self.ollama.generate(
                    prompt=prompt,
                    temperature=0.3,  # Low temperature for factual analysis
                    max_tokens=300
                )
                
                # Parse LLM response
                response_text = response.get('response', '').strip()
                
                # Try to extract JSON from response
                try:
                    json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                    if json_match:
                        import json as json_module
                        suggestion = json_module.loads(json_match.group(0))
                        
                        # Create proposal from LLM suggestion
                        proposals.append({
                            'type': 'merge',
                            'title': suggestion.get('title', cluster['normalized_topic']),
                            'description': suggestion.get('description', f"Merge content about {cluster['normalized_topic']}"),
                            'affected_pages': ','.join(map(str, cluster['pages'])),
                            'confidence': suggestion.get('confidence', 'medium'),
                            'learning_objective': suggestion.get('learning_objective', ''),
                            'source': 'llm'
                        })
                    else:
                        # LLM didn't return JSON, create basic proposal
                        proposals.append({
                            'type': 'merge',
                            'title': cluster['normalized_topic'],
                            'description': f"Topic appears on pages {', '.join(map(str, cluster['pages']))}. Consider merging.",
                            'affected_pages': ','.join(map(str, cluster['pages'])),
                            'confidence': 'medium',
                            'source': 'llm_fallback'
                        })
                except Exception as parse_error:
                    print(f"[WARN] JSON parsing failed: {str(parse_error)}")
                    # Fallback proposal without JSON parsing
                    proposals.append({
                        'type': 'merge',
                        'title': cluster['normalized_topic'],
                        'description': f"Topic appears on pages {', '.join(map(str, cluster['pages']))}.",
                        'affected_pages': ','.join(map(str, cluster['pages'])),
                        'confidence': 'medium',
                        'source': 'parse_error_fallback'
                    })
                    
            except Exception as e:
                print(f"[WARN] LLM analysis failed for cluster '{cluster.get('normalized_topic')}': {str(e)}")
                # Add basic proposal without LLM
                proposals.append({
                    'type': 'merge',
                    'title': cluster['normalized_topic'],
                    'description': f"Topic appears on multiple pages. Consider organizing.",
                    'affected_pages': ','.join(map(str, cluster['pages'])),
                    'confidence': 'low',
                    'source': 'error_fallback'
                })
                continue
        
        # If no LLM proposals generated, fall back to simple
        if not proposals:
            print("[WARN] No LLM proposals generated, falling back to simple")
            return self._generate_simple_proposals(pages_data, document_name)
        
        return proposals
    
    def _extract_topics_from_pages(self, pages_data: List[Dict]) -> Dict[int, List[str]]:
        """
        Extract topics/sections from each page using pattern matching
        
        Args:
            pages_data: Page information
            
        Returns:
            Dict mapping page numbers to list of topics
        """
        topics_by_page = {}
        
        # Common patterns for section headers in notes
        header_patterns = [
            r'^([A-Z][A-Za-z\s&-]+)[:]\s*$',  # Topic: format
            r'^([0-9]+\.\s*[A-Z][A-Za-z\s&-]+)',  # 1. Topic format
            r'^([A-Z][A-Z\s&-]+)$',  # ALL CAPS headers
            r'^#+\s*([A-Za-z\s&-]+)',  # Markdown headers
        ]
        
        for page_info in pages_data:
            page_num = page_info['page_number']
            text = page_info['text']
            topics = []
            
            if not text:
                topics_by_page[page_num] = []
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or len(line) < 3:
                    continue
                
                # Check against patterns
                for pattern in header_patterns:
                    match = re.match(pattern, line)
                    if match:
                        topic = match.group(1).strip()
                        if len(topic) > 3 and len(topic) < 100:
                            topics.append(topic)
                        break
                
                # Also look for lines with key trading terms
                trading_keywords = [
                    'support', 'resistance', 'trend', 'chart', 'pattern',
                    'indicator', 'moving average', 'volume', 'breakout',
                    'reversal', 'momentum', 'fibonacci', 'candlestick',
                    'swing', 'trading', 'entry', 'exit', 'stop loss'
                ]
                
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in trading_keywords):
                    if len(line) < 100 and len(line) > 10:
                        # This might be a topic
                        topics.append(line)
            
            # Deduplicate topics for this page
            topics_by_page[page_num] = list(set(topics))[:10]  # Limit to top 10 per page
        
        return topics_by_page
    
    def _cluster_similar_topics(self, topics_by_page: Dict[int, List[str]]) -> List[Dict]:
        """
        Cluster similar topics that appear on different pages
        
        Args:
            topics_by_page: Topics extracted from each page
            
        Returns:
            List of topic clusters with pages
        """
        # Flatten all topics with their pages
        all_topics = []
        for page_num, topics in topics_by_page.items():
            for topic in topics:
                all_topics.append({
                    'topic': topic,
                    'page': page_num,
                    'normalized': self._normalize_topic(topic)
                })
        
        # Group by normalized topic
        clusters = defaultdict(list)
        for topic_info in all_topics:
            clusters[topic_info['normalized']].append(topic_info)
        
        # Format clusters
        formatted_clusters = []
        for normalized, instances in clusters.items():
            if len(instances) >= 2:  # Only include topics that appear on multiple pages
                formatted_clusters.append({
                    'normalized_topic': normalized,
                    'variations': [inst['topic'] for inst in instances],
                    'pages': sorted(set(inst['page'] for inst in instances)),
                    'occurrence_count': len(instances)
                })
        
        # Sort by occurrence count
        formatted_clusters.sort(key=lambda x: x['occurrence_count'], reverse=True)
        
        return formatted_clusters
    
    def _normalize_topic(self, topic: str) -> str:
        """Normalize topic string for comparison"""
        # Remove numbers, special chars, lowercase, trim
        normalized = re.sub(r'[^a-zA-Z\s]', '', topic.lower())
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        return normalized
    
    def _generate_organization_proposals(
        self,
        topic_clusters: List[Dict],
        pages_data: List[Dict],
        document_name: str
    ) -> List[Dict]:
        """
        Use LLM to generate organization proposals
        
        Args:
            topic_clusters: Clustered topics
            pages_data: Original page data
            document_name: Document name
            
        Returns:
            List of organization proposals
        """
        proposals = []
        
        if not self.ollama.is_available():
            # Fallback: create basic proposals without LLM
            for cluster in topic_clusters[:10]:  # Top 10 clusters
                proposals.append({
                    'type': 'merge',
                    'title': f"Merge: {cluster['normalized_topic']}",
                    'description': f"This topic appears on pages {', '.join(map(str, cluster['pages']))}. Consider merging into a single comprehensive section.",
                    'affected_pages': ','.join(map(str, cluster['pages'])),
                    'confidence': 'medium'
                })
            return proposals
        
        # Use LLM for intelligent proposals
        for cluster in topic_clusters[:5]:  # Top 5 for LLM analysis (to save time)
            try:
                # Gather text from affected pages
                affected_texts = []
                for page_num in cluster['pages']:
                    page_info = next((p for p in pages_data if p['page_number'] == page_num), None)
                    if page_info:
                        # Get snippet around the topic
                        text = page_info['text'][:500]  # First 500 chars
                        affected_texts.append(f"Page {page_num}: {text}")
                
                context = "\n\n".join(affected_texts[:3])  # Limit to 3 pages
                
                prompt = f"""You are analyzing swing trading class notes. The topic "{cluster['normalized_topic']}" appears on multiple pages: {', '.join(map(str, cluster['pages']))}.

Context from these pages:
{context}

Based on this scattered content, suggest how to organize it. Should it be:
1. Merged into one comprehensive section
2. Split into subtopics
3. Reorganized with clear progression

Respond in JSON format:
{{
    "action": "merge|split|reorganize",
    "title": "Brief title for the organized section",
    "description": "One sentence explanation of the organization",
    "confidence": "high|medium|low"
}}"""

                response = self.ollama.generate(
                    prompt=prompt,
                    temperature=self.config.ORGANIZATION_TEMPERATURE,
                    max_tokens=200,
                    model=self.config.OLLAMA_LLM_MODEL
                )
                
                if response['status'] == 'success':
                    # Try to parse JSON from response
                    response_text = response['response'].strip()
                    
                    # Extract JSON if wrapped in markdown
                    json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
                    if json_match:
                        try:
                            import json as json_module
                            suggestion = json_module.loads(json_match.group(0))
                            
                            proposals.append({
                                'type': suggestion.get('action', 'merge'),
                                'title': suggestion.get('title', cluster['normalized_topic']),
                                'description': suggestion.get('description', 'AI-suggested organization'),
                                'affected_pages': ','.join(map(str, cluster['pages'])),
                                'confidence': suggestion.get('confidence', 'medium'),
                                'ai_generated': True
                            })
                        except json.JSONDecodeError:
                            # Fallback to basic proposal
                            self._add_basic_proposal(proposals, cluster)
                    else:
                        self._add_basic_proposal(proposals, cluster)
                else:
                    self._add_basic_proposal(proposals, cluster)
                    
            except Exception as e:
                print(f"Error generating proposal for {cluster['normalized_topic']}: {str(e)}")
                self._add_basic_proposal(proposals, cluster)
        
        # Add basic proposals for remaining clusters
        for cluster in topic_clusters[5:10]:
            self._add_basic_proposal(proposals, cluster)
        
        return proposals
    
    def _add_basic_proposal(self, proposals: List[Dict], cluster: Dict):
        """Add a basic merge proposal without LLM"""
        proposals.append({
            'type': 'merge',
            'title': f"Merge: {cluster['normalized_topic'].title()}",
            'description': f"This topic appears on {len(cluster['pages'])} pages. Consider merging into a single section.",
            'affected_pages': ','.join(map(str, cluster['pages'])),
            'confidence': 'medium',
            'ai_generated': False
        })
    
    def apply_organization(
        self,
        proposal: Dict,
        pages_data: List[Dict]
    ) -> Dict:
        """
        Apply an approved organization proposal
        
        Args:
            proposal: The approved proposal
            pages_data: Original page data
            
        Returns:
            Dict with organized content
        """
        affected_pages = [int(p) for p in proposal['affected_pages'].split(',')]
        
        # Gather content from affected pages
        combined_content = []
        for page_num in affected_pages:
            page_info = next((p for p in pages_data if p['page_number'] == page_num), None)
            if page_info:
                combined_content.append({
                    'page': page_num,
                    'text': page_info['text']
                })
        
        if proposal['type'] == 'merge':
            # Combine all content
            merged_text = "\n\n".join([
                f"[From Page {item['page']}]\n{item['text']}"
                for item in combined_content
            ])
            
            return {
                'status': 'success',
                'title': proposal['title'],
                'content': merged_text,
                'pages': ','.join(map(str, affected_pages)),
                'type': 'merged_section'
            }
        
        # For split/reorganize, return sections as-is for now
        return {
            'status': 'success',
            'title': proposal['title'],
            'content': json.dumps(combined_content),
            'pages': ','.join(map(str, affected_pages)),
            'type': 'reorganized_section'
        }


    def merge_into_existing_book(self, new_pages_data: List[Dict], existing_book_id: int, document_name: str) -> Dict:
        """
        Analyze new PDF content and suggest how to merge into existing book
        
        Args:
            new_pages_data: List of page data from new PDF
            existing_book_id: ID of book to merge into
            document_name: Name of new document
            
        Returns:
            Dict with merge proposals
        """
        try:
            # Import here to avoid circular dependency
            from app import KnowledgeBook, KnowledgeSection
            
            # Get existing book structure
            book = KnowledgeBook.query.get(existing_book_id)
            if not book:
                return {'status': 'error', 'message': 'Book not found'}
            
            # Get existing sections
            existing_sections = KnowledgeSection.query.filter_by(book_id=existing_book_id).order_by(KnowledgeSection.section_order).all()
            
            if not existing_sections:
                # No sections yet - treat as new organization
                return self.analyze_content_structure(new_pages_data, document_name)
            
            # Extract topics from new content
            new_topics = self._extract_topics_from_pages(new_pages_data)
            
            # Build summaries for LLM
            new_summary = '\n'.join([
                f"Page {p['page_number']}: {p['text'][:300]}..."
                for p in new_pages_data[:5]
            ])
            
            existing_summary = '\n'.join([
                f"- {s.title} ({s.section_type})"
                for s in existing_sections[:20]
            ])
            
            # Generate simple merge proposals
            proposals = [{
                'action': 'create_new',
                'new_section_title': f'Content from {document_name}',
                'pages': ','.join(str(p['page_number']) for p in new_pages_data),
                'rationale': 'Add as new section for manual organization',
                'section_type': 'section'
            }]
            
            return {
                'status': 'success',
                'book_id': existing_book_id,
                'book_title': book.title,
                'merge_proposals': proposals
            }
            
        except Exception as e:
            print(f"[ERROR] Merge analysis failed: {str(e)}")
            return {'status': 'error', 'message': str(e)}


# Global instance
content_organizer = ContentOrganizer()


def get_content_organizer() -> ContentOrganizer:
    """Get the global content organizer instance"""
    return content_organizer


