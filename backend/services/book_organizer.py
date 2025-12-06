"""
Book Smart Organization Service
Analyzes sections and creates logical chapter hierarchy
"""

from typing import List, Dict
from utils.ollama_client import get_ollama_client
import json


class BookOrganizer:
    """Service for organizing book sections into logical hierarchy"""
    
    def __init__(self):
        """Initialize book organizer"""
        from config.knowledge_base import config
        
        self.ollama = get_ollama_client()
        self.config = config
    
    def analyze_and_organize_book(self, book_title: str, sections: List[Dict]) -> Dict:
        """
        Analyze all sections and suggest logical chapter organization
        
        Args:
            book_title: Book title
            sections: List of section dicts with title, content, etc.
            
        Returns:
            Dict with proposed chapter structure
        """
        print(f"\n[BOOK_ORG] Analyzing {len(sections)} sections for '{book_title}'")
        
        # Build section summaries for LLM
        section_summaries = []
        for idx, section in enumerate(sections):
            summary = {
                'id': section['id'],
                'title': section['title'],
                'preview': section.get('content', '')[:300],  # First 300 chars
                'pages': section.get('page_numbers', ''),
                'current_order': idx
            }
            section_summaries.append(summary)
        
        # Create LLM prompt for organization
        prompt = self._build_organization_prompt(book_title, section_summaries)
        
        print(f"[BOOK_ORG] Sending to LLM for analysis...")
        
        # Call LLM
        response = self.ollama.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=2000,
            model=self.config.OLLAMA_LLM_MODEL
        )
        
        if response['status'] == 'success':
            print(f"[BOOK_ORG] LLM analysis complete")
            
            # Parse LLM response
            organization = self._parse_organization_response(response['response'], sections)
            
            return {
                'status': 'success',
                'organization': organization
            }
        else:
            print(f"[BOOK_ORG] LLM failed, using fallback organization")
            # Fallback: basic categorization
            return {
                'status': 'success',
                'organization': self._create_fallback_organization(sections)
            }
    
    def _build_organization_prompt(self, book_title: str, sections: List[Dict]) -> str:
        """Build prompt for LLM to organize sections"""
        
        sections_text = "\n".join([
            f"{i+1}. {s['title']} (Pages: {s['pages']}) - {s['preview'][:150]}..."
            for i, s in enumerate(sections)
        ])
        
        prompt = f"""You are organizing a swing trading educational book titled "{book_title}".

Current sections (unsorted):
{sections_text}

Organize these into a logical learning flow with major chapters:
1. Generic Trading Concepts (basics, terminology, market overview)
2. Market Psychology (trader mindset, emotional control, psychological warfare)
3. Fundamental Analysis (economic indicators, market trends)
4. Technical Analysis:
   - Candlestick Patterns (doji, hammer, engulfing, etc.)
   - Chart Patterns (support/resistance, trends, breakouts)
   - Indicators & Tools
5. Trading Strategy (entry/exit rules, zone drawing, demand/supply)
6. Risk Management (stop loss, position sizing)
7. Profit Booking (exit strategies, target setting)

For each section above, assign the appropriate sections by their numbers.
Respond in JSON format:

{{
  "chapters": [
    {{
      "title": "Generic Trading Concepts",
      "order": 1,
      "sections": [1, 3, 5]
    }},
    {{
      "title": "Market Psychology",  
      "order": 2,
      "sections": [2, 15]
    }}
  ]
}}

Only include chapters that have matching sections. Use logical learning progression."""

        return prompt
    
    def _parse_organization_response(self, llm_response: str, sections: List[Dict]) -> Dict:
        """Parse LLM JSON response and build organization structure"""
        
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            
            if json_match:
                import json as json_module
                parsed = json_module.loads(json_match.group(0))
                
                # Build chapter structure
                chapters = []
                for chapter_def in parsed.get('chapters', []):
                    chapter = {
                        'title': chapter_def.get('title', 'Untitled Chapter'),
                        'order': chapter_def.get('order', 999),
                        'section_ids': chapter_def.get('sections', []),
                        'type': 'chapter'
                    }
                    chapters.append(chapter)
                
                # Sort by order
                chapters.sort(key=lambda x: x['order'])
                
                print(f"[BOOK_ORG] Parsed {len(chapters)} chapters from LLM response")
                
                return {
                    'chapters': chapters,
                    'method': 'llm'
                }
            
        except Exception as e:
            print(f"[BOOK_ORG] Failed to parse LLM response: {str(e)}")
        
        # Fallback
        return self._create_fallback_organization(sections)
    
    def _create_fallback_organization(self, sections: List[Dict]) -> Dict:
        """Create basic organization when LLM fails"""
        
        print(f"[BOOK_ORG] Using fallback organization")
        
        # Simple categorization by keywords
        categories = {
            'Introduction & Basics': ['intro', 'basic', 'overview', 'concept'],
            'Market Psychology': ['psycholog', 'warfare', 'mindset', 'emotion', 'operator'],
            'Candlestick Patterns': ['candle', 'doji', 'hammer', 'engulf'],
            'Chart Patterns': ['chart', 'pattern', 'bullish', 'bearish'],
            'Support & Resistance': ['support', 'resistance', 's&r', 's/r'],
            'Demand & Supply': ['demand', 'supply', 'zone', 'drawing'],
            'Breakouts & Trends': ['breakout', 'trend', 'reversal', 'pullback'],
            'Profit & Exit Strategy': ['profit', 'booking', 'exit', 'target']
        }
        
        chapters = []
        chapter_order = 1
        
        for chapter_title, keywords in categories.items():
            matching_sections = []
            
            for idx, section in enumerate(sections):
                title_lower = section['title'].lower()
                if any(keyword in title_lower for keyword in keywords):
                    matching_sections.append(idx + 1)  # 1-indexed
            
            if matching_sections:
                chapters.append({
                    'title': chapter_title,
                    'order': chapter_order,
                    'section_ids': matching_sections,
                    'type': 'chapter'
                })
                chapter_order += 1
        
        print(f"[BOOK_ORG] Created {len(chapters)} chapters via fallback")
        
        return {
            'chapters': chapters,
            'method': 'fallback'
        }


def get_book_organizer():
    """Get singleton instance of book organizer"""
    if not hasattr(get_book_organizer, 'instance'):
        get_book_organizer.instance = BookOrganizer()
    return get_book_organizer.instance

