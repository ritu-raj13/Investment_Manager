"""
Content Synthesis Service
Transforms raw PDF chunks into coherent educational book content
"""

from utils.ollama_client import get_ollama_client
import re
import json


class ContentSynthesizer:
    """Synthesizes clean educational content from raw PDF extracts"""
    
    def __init__(self):
        from config.knowledge_base import config
        self.ollama = get_ollama_client()
        self.config = config
    
    def synthesize_chapter_content(self, chapter_title: str, sections_data: list) -> dict:
        """
        Synthesize multiple sections into coherent chapter content
        
        Args:
            chapter_title: Title of the chapter
            sections_data: List of section dicts with raw content
            
        Returns:
            Dict with synthesized chapter intro and cleaned sections
        """
        print(f"\n[SYNTHESIZER] Processing chapter: {chapter_title}")
        print(f"[SYNTHESIZER] Input: {len(sections_data)} sections")
        
        # Group similar content
        merged_content = self._merge_similar_sections(sections_data)
        
        # Synthesize each merged section
        synthesized_sections = []
        for idx, merged_section in enumerate(merged_content):
            print(f"[SYNTHESIZER] Synthesizing section {idx+1}/{len(merged_content)}: {merged_section['topic']}")
            
            clean_section = self._synthesize_section(
                chapter_title=chapter_title,
                topic=merged_section['topic'],
                raw_content=merged_section['combined_text']
            )
            
            synthesized_sections.append(clean_section)
        
        # Create chapter introduction
        chapter_intro = self._create_chapter_intro(chapter_title, synthesized_sections)
        
        print(f"[SYNTHESIZER] Chapter complete: {len(synthesized_sections)} sections")
        
        return {
            'chapter_title': chapter_title,
            'introduction': chapter_intro,
            'sections': synthesized_sections
        }
    
    def _merge_similar_sections(self, sections_data: list) -> list:
        """Merge sections with similar topics"""
        
        if not sections_data:
            return []
        
        # Simple grouping by topic keywords
        topic_groups = {}
        
        for section in sections_data:
            title = section.get('title', '').lower()
            content = section.get('content', '')
            
            # Extract main topic
            topic = self._extract_main_topic(title, content)
            
            if topic not in topic_groups:
                topic_groups[topic] = {
                    'topic': topic,
                    'sections': [],
                    'combined_text': ''
                }
            
            topic_groups[topic]['sections'].append(section)
            topic_groups[topic]['combined_text'] += f"\n\n{content}"
        
        return list(topic_groups.values())
    
    def _extract_main_topic(self, title: str, content: str) -> str:
        """Extract main topic from title/content"""
        
        # Common patterns
        patterns = [
            r'(hammer|doji|dragonfly|engulfing|harami|morning star|evening star)',
            r'(support|resistance|demand|supply|zone)',
            r'(breakout|breakdown|pullback|reversal|trend)',
            r'(wedge|triangle|rectangle|cup|handle|pattern)',
            r'(profit|booking|exit|entry)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1).title()
        
        # Fallback: use first significant word
        words = title.split()
        for word in words:
            if len(word) > 4 and word not in ['understanding', 'chart', 'pattern']:
                return word.title()
        
        return title.title() if title else "Trading Concepts"
    
    def _synthesize_section(self, chapter_title: str, topic: str, raw_content: str) -> dict:
        """Use LLM to synthesize clean educational content"""
        
        # Clean raw content first
        cleaned_text = self._clean_raw_text(raw_content)
        
        # Build synthesis prompt
        prompt = f"""You are writing a professional swing trading educational book.

Chapter: {chapter_title}
Section Topic: {topic}

Raw notes (from handwritten scanned PDFs):
{cleaned_text[:2000]}

Task: Rewrite these notes as a clear, educational section for a trading textbook.

Requirements:
1. Write in clear, professional prose (not bullet points unless listing steps)
2. Start with a brief introduction to the concept
3. Explain WHY this concept matters in swing trading
4. Describe HOW to apply it practically
5. Include key points to remember
6. Remove all page references and fragmentary text
7. Make it flow naturally like a book chapter

Output format:
{{
  "section_title": "Descriptive title (e.g., 'Understanding Hammer Candlestick Pattern')",
  "content": "Clean markdown-formatted educational text (3-5 paragraphs)"
}}

Respond ONLY with valid JSON."""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                temperature=0.4,
                max_tokens=1000,
                model=self.config.OLLAMA_LLM_MODEL
            )
            
            if response['status'] == 'success':
                # Parse JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response['response'])
                if json_match:
                    import json as json_module
                    parsed = json_module.loads(json_match.group(0))
                    
                    return {
                        'title': parsed.get('section_title', topic),
                        'content': parsed.get('content', cleaned_text[:500]),
                        'synthesized': True
                    }
        
        except Exception as e:
            print(f"[SYNTHESIZER] LLM synthesis failed: {e}")
        
        # Fallback: basic cleanup
        return {
            'title': f"{topic} in Swing Trading",
            'content': cleaned_text[:500] + "...",
            'synthesized': False
        }
    
    def _clean_raw_text(self, raw_text: str) -> str:
        """Clean raw text by removing markers and formatting"""
        
        # Remove page markers
        text = re.sub(r'\[From Page \d+\]', '', raw_text)
        text = re.sub(r'\(Pages?: [\d,]+\)', '', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove repeated headers
        lines = text.split('\n')
        cleaned_lines = []
        prev_line = None
        
        for line in lines:
            line = line.strip()
            if line and line != prev_line:
                cleaned_lines.append(line)
                prev_line = line
        
        return '\n'.join(cleaned_lines)
    
    def _create_chapter_intro(self, chapter_title: str, sections: list) -> str:
        """Create chapter introduction"""
        
        section_topics = [s['title'] for s in sections]
        
        prompt = f"""Write a 2-3 paragraph introduction for this chapter in a swing trading textbook:

Chapter: {chapter_title}

This chapter covers:
{chr(10).join(['- ' + topic for topic in section_topics])}

Write a professional, engaging introduction that:
1. Explains what this chapter covers
2. Why these concepts are important for swing traders
3. What the reader will learn

Keep it concise and educational."""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=300,
                model=self.config.OLLAMA_LLM_MODEL
            )
            
            if response['status'] == 'success':
                return response['response'].strip()
        
        except Exception as e:
            print(f"[SYNTHESIZER] Chapter intro generation failed: {e}")
        
        # Fallback
        return f"This chapter covers essential concepts in {chapter_title.lower()}, including {', '.join(section_topics[:3])} and more."


def get_content_synthesizer():
    """Get singleton instance"""
    if not hasattr(get_content_synthesizer, 'instance'):
        get_content_synthesizer.instance = ContentSynthesizer()
    return get_content_synthesizer.instance

