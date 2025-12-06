"""
Knowledge Base Service
Handles PDF extraction, chunking, and ChromaDB vector store management
"""

import os
import re
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pdfplumber
from werkzeug.utils import secure_filename
import chromadb
from chromadb.config import Settings
import hashlib
from PIL import Image
import io


class KnowledgeBaseService:
    """Service for managing PDF knowledge base and vector store"""
    
    def __init__(self, upload_folder: Optional[str] = None, chroma_dir: Optional[str] = None):
        """
        Initialize Knowledge Base Service
        
        Args:
            upload_folder: Directory to store uploaded PDFs (defaults to config)
            chroma_dir: Directory for ChromaDB persistent storage (defaults to config)
        """
        from config.knowledge_base import config
        
        self.upload_folder = upload_folder or config.PDF_UPLOAD_DIR
        self.chroma_dir = chroma_dir or config.CHROMA_DB_DIR
        self.image_folder = config.IMAGE_UPLOAD_DIR
        self.config = config
        
        # Create directories if they don't exist
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.chroma_dir, exist_ok=True)
        os.makedirs(self.image_folder, exist_ok=True)
        
        # Initialize ChromaDB client with persistent storage
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_dir)
        
        # Determine embedding function based on configuration
        embedding_function = self._get_embedding_function()
        
        # Try to get existing collection first
        try:
            self.collection = self.chroma_client.get_collection(
                name=config.CHROMA_COLLECTION_NAME
            )
            print(f"[INFO] Using existing ChromaDB collection: {config.CHROMA_COLLECTION_NAME}")
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.chroma_client.create_collection(
                name=config.CHROMA_COLLECTION_NAME,
                metadata={
                    "description": "Swing trading class notes",
                    "embedding_provider": config.EMBEDDING_PROVIDER,
                    "embedding_model": config.OLLAMA_EMBEDDING_MODEL if config.EMBEDDING_PROVIDER == 'ollama' else config.SENTENCE_TRANSFORMER_MODEL
                },
                embedding_function=embedding_function if config.EMBEDDING_PROVIDER == 'ollama' else None
            )
            print(f"[INFO] Created new ChromaDB collection: {config.CHROMA_COLLECTION_NAME}")
        
        # Initialize sentence-transformers model if using that provider
        if config.EMBEDDING_PROVIDER == 'sentence-transformers':
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(config.SENTENCE_TRANSFORMER_MODEL)
            except ImportError:
                print("Warning: sentence-transformers not installed. Using Ollama embeddings as fallback.")
                config.EMBEDDING_PROVIDER = 'ollama'
                self.collection = self.chroma_client.get_or_create_collection(
                    name=config.CHROMA_COLLECTION_NAME,
                    embedding_function=self._get_embedding_function()
                )
        else:
            self.embedding_model = None
    
    def _get_embedding_function(self):
        """Get ChromaDB embedding function based on configuration"""
        from config.knowledge_base import config
        
        if config.EMBEDDING_PROVIDER == 'ollama':
            # Use Ollama embeddings
            from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
            
            return OllamaEmbeddingFunction(
                url=f"{config.OLLAMA_BASE_URL}/api/embeddings",
                model_name=config.OLLAMA_EMBEDDING_MODEL
            )
        else:
            # Let ChromaDB use default or we'll handle it manually
            return None
        
    def extract_images_from_pdf(self, pdf_path: str, document_id: int) -> List[Dict]:
        """
        Extract images from PDF and save to disk
        
        Args:
            pdf_path: Path to PDF file
            document_id: Database document ID
            
        Returns:
            List of dicts with image metadata: [{page, image_path, width, height}]
        """
        images_data = []
        
        # Create document-specific image directory
        doc_image_dir = os.path.join(self.image_folder, str(document_id))
        os.makedirs(doc_image_dir, exist_ok=True)
        
        try:
            import warnings
            warnings.filterwarnings('ignore', message='.*invalid float value.*')
            warnings.filterwarnings('ignore', message='.*non-stroke color.*')
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    try:
                        # Extract images from the page
                        if hasattr(page, 'images') and page.images:
                            for img_idx, img in enumerate(page.images):
                                try:
                                    # Get image from page
                                    image_obj = page.within_bbox((
                                        img['x0'], img['top'], img['x1'], img['bottom']
                                    )).to_image()
                                    
                                    # Save image
                                    image_filename = f"page_{page_num}_img_{img_idx}.png"
                                    image_path = os.path.join(doc_image_dir, image_filename)
                                    
                                    # Convert to PIL Image and save
                                    pil_image = image_obj.original
                                    pil_image.save(image_path, 'PNG')
                                    
                                    # Store relative path for database
                                    relative_path = os.path.join('uploads', 'images', str(document_id), image_filename)
                                    
                                    images_data.append({
                                        'page': page_num,
                                        'image_path': relative_path,
                                        'width': int(img['width']),
                                        'height': int(img['height']),
                                        'index': img_idx
                                    })
                                    
                                    print(f"[INFO] Extracted image {img_idx} from page {page_num}")
                                    
                                except Exception as img_error:
                                    print(f"[WARN] Failed to extract image {img_idx} from page {page_num}: {str(img_error)}")
                                    continue
                    
                    except Exception as page_error:
                        print(f"[WARN] Failed to process images on page {page_num}: {str(page_error)}")
                        continue
            
            print(f"[INFO] Extracted {len(images_data)} images total from document {document_id}")
            return images_data
            
        except Exception as e:
            print(f"[ERROR] Failed to extract images from PDF: {str(e)}")
            return []
    
    def extract_text_from_pdf(self, pdf_path: str, document_id: Optional[int] = None) -> Tuple[str, int, List[Dict]]:
        """
        Extract text and images from PDF file
        
        Args:
            pdf_path: Path to PDF file
            document_id: Optional document ID for image extraction
            
        Returns:
            Tuple of (full_text, total_pages, pages_data)
            pages_data is list of dicts with page number, text, and image references
        """
        full_text = ""
        pages_data = []
        
        # Extract images if document_id provided
        images_by_page = {}
        if document_id:
            images = self.extract_images_from_pdf(pdf_path, document_id)
            for img in images:
                page_num = img['page']
                if page_num not in images_by_page:
                    images_by_page[page_num] = []
                images_by_page[page_num].append(img)
        
        try:
            # Suppress pdfplumber warnings about invalid color values
            import warnings
            warnings.filterwarnings('ignore', message='.*invalid float value.*')
            warnings.filterwarnings('ignore', message='.*non-stroke color.*')
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    try:
                        # Extract text with error handling for problematic pages
                        page_text = page.extract_text() or ""
                    except Exception as page_error:
                        # If extraction fails for this page, log and continue
                        print(f"[WARN] Failed to extract text from page {page_num}: {str(page_error)}")
                        page_text = f"[Page {page_num} - Text extraction failed]"
                    
                    full_text += f"\n\n--- Page {page_num} ---\n\n{page_text}"
                    
                    pages_data.append({
                        'page_number': page_num,
                        'text': page_text,
                        'images': images_by_page.get(page_num, []),
                        'char_count': len(page_text)
                    })
                
                return full_text, total_pages, pages_data
                
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def chunk_text(
        self, 
        text: str, 
        page_data: List[Dict],
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> List[Dict]:
        """
        Split text into overlapping chunks for better context retrieval
        
        Args:
            text: Full text to chunk
            page_data: Page information for source tracking
            chunk_size: Target size of each chunk in characters (defaults to config)
            overlap: Overlap between chunks in characters (defaults to config)
            
        Returns:
            List of chunk dictionaries with text, metadata
        """
        chunk_size = chunk_size or self.config.CHUNK_SIZE
        overlap = overlap or self.config.CHUNK_OVERLAP
        
        chunks = []
        
        # Create a mapping of text positions to page numbers
        page_positions = []
        current_pos = 0
        for page_info in page_data:
            page_text = page_info['text']
            page_positions.append({
                'page_num': page_info['page_number'],
                'start': current_pos,
                'end': current_pos + len(page_text)
            })
            current_pos += len(page_text) + len(f"\n\n--- Page {page_info['page_number']} ---\n\n")
        
        # Split by sentences for better chunking
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        current_chunk_start_pos = 0
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    # Determine which page(s) this chunk belongs to
                    chunk_pages = self._find_pages_for_chunk(
                        current_chunk_start_pos,
                        current_chunk_start_pos + len(current_chunk),
                        page_positions
                    )
                    
                    chunks.append({
                        'text': current_chunk.strip(),
                        'pages': chunk_pages,
                        'char_count': len(current_chunk)
                    })
                
                # Start new chunk with overlap
                current_chunk = current_chunk[-overlap:] + sentence + " " if len(current_chunk) > overlap else sentence + " "
                current_chunk_start_pos += len(current_chunk) - overlap if len(current_chunk) > overlap else 0
        
        # Add the last chunk
        if current_chunk:
            chunk_pages = self._find_pages_for_chunk(
                current_chunk_start_pos,
                current_chunk_start_pos + len(current_chunk),
                page_positions
            )
            chunks.append({
                'text': current_chunk.strip(),
                'pages': chunk_pages,
                'char_count': len(current_chunk)
            })
        
        return chunks
    
    def _find_pages_for_chunk(self, start_pos: int, end_pos: int, page_positions: List[Dict]) -> List[int]:
        """Find which pages a text chunk spans"""
        pages = []
        for page_info in page_positions:
            if (start_pos >= page_info['start'] and start_pos <= page_info['end']) or \
               (end_pos >= page_info['start'] and end_pos <= page_info['end']) or \
               (start_pos <= page_info['start'] and end_pos >= page_info['end']):
                pages.append(page_info['page_num'])
        return sorted(set(pages))
    
    def add_to_vector_store(
        self,
        chunks: List[Dict],
        document_id: int,
        document_name: str
    ) -> Dict:
        """
        Add text chunks to ChromaDB vector store
        
        Args:
            chunks: List of text chunks with metadata
            document_id: Database ID of the document
            document_name: Name of the document
            
        Returns:
            Dict with status and statistics
        """
        try:
            documents = []
            metadatas = []
            ids = []
            
            for idx, chunk in enumerate(chunks):
                chunk_id = f"doc{document_id}_chunk{idx}"
                
                documents.append(chunk['text'])
                metadatas.append({
                    'document_id': document_id,
                    'document_name': document_name,
                    'pages': ','.join(map(str, chunk['pages'])),
                    'chunk_index': idx,
                    'char_count': chunk['char_count']
                })
                ids.append(chunk_id)
            
            # Add to collection (ChromaDB will automatically generate embeddings)
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                'status': 'success',
                'chunks_added': len(chunks),
                'document_id': document_id
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to add to vector store: {str(e)}"
            }
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search for similar text chunks in the vector store
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of similar chunks with metadata and relevance scores
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            formatted_results = []
            if results and results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0] if results.get('metadatas') else []
                distances = results['distances'][0] if results.get('distances') else []
                
                for idx, doc in enumerate(documents):
                    metadata = metadatas[idx] if idx < len(metadatas) else {}
                    distance = distances[idx] if idx < len(distances) else None
                    
                    formatted_results.append({
                        'text': doc,
                        'document_id': metadata.get('document_id'),
                        'document_name': metadata.get('document_name'),
                        'pages': metadata.get('pages', '').split(','),
                        'relevance_score': 1 - distance if distance is not None else None,
                        'chunk_index': metadata.get('chunk_index')
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []
    
    def delete_document_from_store(self, document_id: int) -> Dict:
        """
        Remove all chunks of a document from vector store
        
        Args:
            document_id: Document ID to remove
            
        Returns:
            Dict with status
        """
        try:
            # Get all IDs for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results and results.get('ids'):
                self.collection.delete(ids=results['ids'])
                return {
                    'status': 'success',
                    'chunks_deleted': len(results['ids'])
                }
            
            return {
                'status': 'success',
                'chunks_deleted': 0,
                'message': 'No chunks found for this document'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Failed to delete from vector store: {str(e)}"
            }
    
    def reindex_all(self, documents_data: List[Dict]) -> Dict:
        """
        Rebuild entire vector store from document data
        
        Args:
            documents_data: List of dicts with document info and file paths
            
        Returns:
            Dict with reindexing results
        """
        try:
            # Clear existing collection
            self.chroma_client.delete_collection("trading_notes")
            self.collection = self.chroma_client.create_collection(
                name="trading_notes",
                metadata={"description": "Swing trading class notes"}
            )
            
            results = {
                'total_documents': len(documents_data),
                'processed': 0,
                'total_chunks': 0,
                'errors': []
            }
            
            for doc_data in documents_data:
                try:
                    # Extract and chunk (with images if document_id provided)
                    doc_id = doc_data.get('document_id')
                    full_text, total_pages, pages_data = self.extract_text_from_pdf(
                        doc_data['file_path'],
                        doc_id
                    )
                    chunks = self.chunk_text(full_text, pages_data)
                    
                    # Add to vector store
                    add_result = self.add_to_vector_store(
                        chunks,
                        doc_data['id'],
                        doc_data['filename']
                    )
                    
                    if add_result['status'] == 'success':
                        results['processed'] += 1
                        results['total_chunks'] += add_result['chunks_added']
                    else:
                        results['errors'].append({
                            'document': doc_data['filename'],
                            'error': add_result.get('message', 'Unknown error')
                        })
                        
                except Exception as e:
                    results['errors'].append({
                        'document': doc_data.get('filename', 'Unknown'),
                        'error': str(e)
                    })
            
            results['status'] = 'success' if results['processed'] > 0 else 'error'
            return results
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Reindexing failed: {str(e)}"
            }
    
    def save_uploaded_file(self, file, document_id: int) -> str:
        """
        Save uploaded PDF file
        
        Args:
            file: File object from request
            document_id: Database document ID
            
        Returns:
            File path where the file was saved
        """
        filename = secure_filename(file.filename)
        # Add document ID to filename to avoid conflicts
        name, ext = os.path.splitext(filename)
        new_filename = f"{name}_{document_id}{ext}"
        file_path = os.path.join(self.upload_folder, new_filename)
        
        file.save(file_path)
        return file_path
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the vector store"""
        try:
            count = self.collection.count()
            return {
                'total_chunks': count,
                'collection_name': self.collection.name
            }
        except Exception as e:
            return {
                'error': str(e)
            }


# Global instance
knowledge_base_service = KnowledgeBaseService()


def get_knowledge_base_service() -> KnowledgeBaseService:
    """Get the global knowledge base service instance"""
    return knowledge_base_service


