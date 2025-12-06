"""
RAG (Retrieval-Augmented Generation) Chatbot Service
Handles query processing, context retrieval, and response generation
"""

import time
import json
from typing import Dict, List, Optional
from utils.ollama_client import get_ollama_client
from services.knowledge_base import get_knowledge_base_service


class RAGChatbot:
    """RAG-based chatbot for querying trading notes"""
    
    def __init__(self):
        """Initialize RAG chatbot"""
        from config.knowledge_base import config
        
        self.ollama = get_ollama_client()
        self.kb_service = get_knowledge_base_service()
        self.config = config
        self.temperature = config.LLM_TEMPERATURE
        self.max_context_chunks = config.RAG_TOP_K_RESULTS
        self.max_tokens = config.LLM_MAX_TOKENS
        
    def query(self, user_query: str, include_sources: bool = True) -> Dict:
        """
        Process user query and generate response
        
        Args:
            user_query: User's question
            include_sources: Whether to include source references
            
        Returns:
            Dict with response, sources, and metadata
        """
        start_time = time.time()
        
        # Validate Ollama availability
        print(f"[RAG] Checking Ollama availability...")
        if not self.ollama.is_available():
            print(f"[RAG] ERROR: Ollama not available")
            return {
                'status': 'error',
                'message': 'Ollama server is not running. Please start Ollama to use the chatbot.',
                'response': None
            }
        print(f"[RAG] Ollama is ready")
        
        # Step 1: Retrieve relevant context from vector store
        print(f"[RAG] Searching ChromaDB for relevant chunks (top {self.max_context_chunks})...")
        relevant_chunks = self.kb_service.search_similar(
            user_query,
            n_results=self.max_context_chunks
        )
        
        if not relevant_chunks:
            print(f"[RAG] No relevant chunks found in knowledge base")
            return {
                'status': 'success',
                'response': "I don't have information about this in the trading notes. Please make sure you've uploaded your notes PDF first.",
                'sources': [],
                'response_time': time.time() - start_time
            }
        
        print(f"[RAG] Found {len(relevant_chunks)} relevant chunks")
        
        # Step 2: Build context from retrieved chunks
        print(f"[RAG] Building context from chunks...")
        context = self._build_context(relevant_chunks)
        print(f"[RAG] Context built ({len(context)} characters)")
        
        # Step 3: Create prompt with strict instructions
        print(f"[RAG] Creating prompt with temperature={self.temperature}...")
        prompt = self._create_prompt(user_query, context)
        
        # Step 4: Generate response using LLM
        print(f"[RAG] Calling LLM ({self.config.OLLAMA_LLM_MODEL}) for response generation...")
        llm_start = time.time()
        
        llm_response = self.ollama.generate(
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            model=self.config.OLLAMA_LLM_MODEL
        )
        
        llm_time = time.time() - llm_start
        print(f"[RAG] LLM responded in {llm_time:.2f}s")
        
        if llm_response['status'] != 'success':
            print(f"[RAG] ERROR: LLM generation failed")
            return {
                'status': 'error',
                'message': llm_response.get('message', 'Failed to generate response'),
                'response': None
            }
        
        response_text = llm_response['response']
        print(f"[RAG] Generated response ({len(response_text)} characters)")
        
        # Step 5: Extract sources if needed
        sources = []
        if include_sources:
            print(f"[RAG] Formatting source references...")
            sources = self._format_sources(relevant_chunks)
            print(f"[RAG] Added {len(sources)} source references")
        
        response_time = time.time() - start_time
        print(f"[RAG] Total query time: {response_time:.2f}s")
        
        return {
            'status': 'success',
            'response': response_text,
            'sources': sources,
            'response_time': round(response_time, 2),
            'chunks_used': len(relevant_chunks)
        }
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """
        Build context string from retrieved chunks
        
        Args:
            chunks: List of relevant chunks
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for idx, chunk in enumerate(chunks, 1):
            pages = chunk.get('pages', [])
            pages_str = ', '.join(str(p) for p in pages if p) if pages else 'Unknown'
            doc_name = chunk.get('document_name', 'Trading Notes')
            text = chunk.get('text', '')
            
            context_parts.append(
                f"[Source {idx} - {doc_name}, Page(s): {pages_str}]\n{text}"
            )
        
        return "\n\n---\n\n".join(context_parts)
    
    def _create_prompt(self, user_query: str, context: str) -> str:
        """
        Create prompt with strict instructions for accurate responses
        
        Args:
            user_query: User's question
            context: Retrieved context
            
        Returns:
            Formatted prompt
        """
        prompt = f"""You are a helpful assistant for swing trading education. Your role is to answer questions based STRICTLY on the provided context from trading class notes.

CONTEXT FROM TRADING NOTES:
{context}

QUESTION:
{user_query}

INSTRUCTIONS:
1. Answer ONLY using the information provided in the context above
2. If the context doesn't contain enough information to answer the question, clearly state: "I don't have enough information about this in the trading notes."
3. Be precise and accurate - do not make assumptions or add information not in the context
4. When possible, mention which page(s) the information comes from
5. Keep your answer concise and focused on the question
6. Use clear, educational language suitable for learning trading concepts

ANSWER:"""
        
        return prompt
    
    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """
        Format source references for display
        
        Args:
            chunks: Retrieved chunks
            
        Returns:
            List of formatted source references
        """
        sources = []
        
        for idx, chunk in enumerate(chunks, 1):
            pages = chunk.get('pages', [])
            # Filter out empty strings and convert to int
            pages_list = [int(p) for p in pages if p and str(p).strip()]
            
            sources.append({
                'index': idx,
                'document_name': chunk.get('document_name', 'Trading Notes'),
                'pages': sorted(pages_list),
                'relevance_score': chunk.get('relevance_score'),
                'excerpt': chunk.get('text', '')[:200] + '...' if len(chunk.get('text', '')) > 200 else chunk.get('text', '')
            })
        
        return sources
    
    def validate_response(self, response_text: str, context: str) -> bool:
        """
        Validate that response is grounded in context
        (Simple heuristic - can be enhanced)
        
        Args:
            response_text: Generated response
            context: Original context
            
        Returns:
            True if response appears grounded
        """
        # If response indicates lack of information, that's valid
        no_info_phrases = [
            "don't have information",
            "don't have enough information",
            "not mentioned in",
            "no information about"
        ]
        
        if any(phrase in response_text.lower() for phrase in no_info_phrases):
            return True
        
        # Check if key terms from response appear in context
        # This is a simple heuristic
        response_words = set(response_text.lower().split())
        context_words = set(context.lower().split())
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
        response_words -= common_words
        context_words -= common_words
        
        # Check overlap
        overlap = len(response_words.intersection(context_words))
        total = len(response_words)
        
        # At least 30% overlap is reasonable
        return (overlap / total) > 0.3 if total > 0 else False
    
    def chat_with_history(
        self,
        user_query: str,
        conversation_history: List[Dict],
        include_sources: bool = True
    ) -> Dict:
        """
        Query with conversation history for context
        
        Args:
            user_query: Current question
            conversation_history: Previous Q&A pairs
            include_sources: Include source references
            
        Returns:
            Response dict
        """
        # For now, just use the current query
        # Can be enhanced to consider history for follow-up questions
        return self.query(user_query, include_sources)
    
    def suggest_questions(self, num_suggestions: int = 3) -> List[str]:
        """
        Suggest sample questions based on available content
        
        Args:
            num_suggestions: Number of suggestions
            
        Returns:
            List of suggested questions
        """
        default_suggestions = [
            "What is support and resistance?",
            "How do I identify a trend?",
            "What are the key chart patterns?",
            "Explain entry and exit strategies",
            "What is risk management in swing trading?",
            "How to use moving averages?",
            "What are candlestick patterns?",
            "Explain volume analysis"
        ]
        
        return default_suggestions[:num_suggestions]


# Global instance
rag_chatbot = RAGChatbot()


def get_rag_chatbot() -> RAGChatbot:
    """Get the global RAG chatbot instance"""
    return rag_chatbot


