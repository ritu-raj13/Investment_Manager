"""
Knowledge Base Configuration
Centralized configuration for models and parameters
"""

import os
from dotenv import load_dotenv

load_dotenv()


class KnowledgeBaseConfig:
    """Configuration for knowledge base and RAG system"""
    
    # ============================================================================
    # LLM Configuration (Ollama)
    # ============================================================================
    
    # Ollama server URL
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # LLM model for text generation (chatbot responses, content analysis)
    # Options: 'gpt-oss:20b', 'mistral', 'llama2', 'phi', etc.
    OLLAMA_LLM_MODEL = os.getenv('OLLAMA_LLM_MODEL', 'gpt-oss:20b')
    
    # Temperature for LLM responses (0.0-1.0, lower = more deterministic)
    # For educational/factual content, keep low (0.1-0.3)
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.15'))
    
    # Maximum tokens for LLM responses
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '500'))
    
    # ============================================================================
    # Embedding Configuration
    # ============================================================================
    
    # Embedding provider: 'ollama' or 'sentence-transformers'
    EMBEDDING_PROVIDER = os.getenv('EMBEDDING_PROVIDER', 'ollama')
    
    # Ollama embedding model (if EMBEDDING_PROVIDER='ollama')
    # Options: 'nomic-embed-text:latest', 'all-minilm', etc.
    OLLAMA_EMBEDDING_MODEL = os.getenv('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text:latest')
    
    # Sentence-transformers model (if EMBEDDING_PROVIDER='sentence-transformers')
    # Options: 'all-MiniLM-L6-v2', 'all-mpnet-base-v2', etc.
    SENTENCE_TRANSFORMER_MODEL = os.getenv('SENTENCE_TRANSFORMER_MODEL', 'all-MiniLM-L6-v2')
    
    # ============================================================================
    # Vector Database Configuration (ChromaDB)
    # ============================================================================
    
    # ChromaDB storage directory
    CHROMA_DB_DIR = os.getenv('CHROMA_DB_DIR', 'chroma_db')
    
    # Collection name for trading notes
    CHROMA_COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'trading_notes')
    
    # Number of results to retrieve for RAG
    RAG_TOP_K_RESULTS = int(os.getenv('RAG_TOP_K_RESULTS', '5'))
    
    # ============================================================================
    # PDF Processing Configuration
    # ============================================================================
    
    # Directory for uploaded PDFs
    PDF_UPLOAD_DIR = os.getenv('PDF_UPLOAD_DIR', 'uploads/pdfs')
    
    # Directory for extracted images
    IMAGE_UPLOAD_DIR = os.getenv('IMAGE_UPLOAD_DIR', 'uploads/images')
    
    # Text chunking parameters
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '500'))  # Characters per chunk
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '100'))  # Overlap between chunks
    
    # ============================================================================
    # Content Organization Configuration
    # ============================================================================
    
    # Maximum number of proposals to generate per document
    MAX_PROPOSALS_PER_DOC = int(os.getenv('MAX_PROPOSALS_PER_DOC', '10'))
    
    # Temperature for content organization analysis (higher = more creative)
    ORGANIZATION_TEMPERATURE = float(os.getenv('ORGANIZATION_TEMPERATURE', '0.2'))
    
    # ============================================================================
    # Performance Configuration
    # ============================================================================
    
    # Request timeout for Ollama (seconds)
    OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '120'))
    
    # Enable/disable verbose logging
    VERBOSE_LOGGING = os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true'
    
    @classmethod
    def get_config_summary(cls):
        """Get a summary of current configuration"""
        return {
            'llm_model': cls.OLLAMA_LLM_MODEL,
            'embedding_provider': cls.EMBEDDING_PROVIDER,
            'embedding_model': cls.OLLAMA_EMBEDDING_MODEL if cls.EMBEDDING_PROVIDER == 'ollama' else cls.SENTENCE_TRANSFORMER_MODEL,
            'temperature': cls.LLM_TEMPERATURE,
            'chunk_size': cls.CHUNK_SIZE,
            'rag_top_k': cls.RAG_TOP_K_RESULTS,
            'ollama_url': cls.OLLAMA_BASE_URL
        }
    
    @classmethod
    def validate_config(cls):
        """Validate configuration and check if models are available"""
        issues = []
        
        # Check if Ollama is reachable
        try:
            import requests
            response = requests.get(f"{cls.OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code != 200:
                issues.append(f"Ollama server not reachable at {cls.OLLAMA_BASE_URL}")
            else:
                # Check if configured models are available
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if cls.OLLAMA_LLM_MODEL not in model_names:
                    issues.append(f"LLM model '{cls.OLLAMA_LLM_MODEL}' not found in Ollama. Available: {', '.join(model_names)}")
                
                if cls.EMBEDDING_PROVIDER == 'ollama' and cls.OLLAMA_EMBEDDING_MODEL not in model_names:
                    issues.append(f"Embedding model '{cls.OLLAMA_EMBEDDING_MODEL}' not found in Ollama. Available: {', '.join(model_names)}")
        except Exception as e:
            issues.append(f"Cannot connect to Ollama: {str(e)}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'config': cls.get_config_summary()
        }


# Export configuration class
config = KnowledgeBaseConfig

