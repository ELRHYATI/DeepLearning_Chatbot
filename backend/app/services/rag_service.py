"""
RAG (Retrieval-Augmented Generation) Service
Provides document retrieval and context enhancement for QA
"""
from typing import List, Dict, Optional, Tuple
import os
import json
import re
from collections import defaultdict
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

from app.utils.logger import get_logger

logger = get_logger()


class RAGService:
    """Service for Retrieval-Augmented Generation"""
    
    def __init__(self):
        self.embedding_model = None
        self.knowledge_base = {}
        self.user_documents = {}  # user_id -> list of documents
        self.document_embeddings = {}  # document_id -> embedding
        self.chunk_embeddings = {}  # chunk_id -> embedding
        self._load_embedding_model()
        self._initialize_knowledge_base()
    
    def _load_embedding_model(self):
        """Load embedding model for semantic search"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use multilingual model for French
                self.embedding_model = SentenceTransformer(
                    'paraphrase-multilingual-MiniLM-L12-v2'
                )
                logger.info("RAG embedding model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load embedding model: {e}")
                self.embedding_model = None
        else:
            logger.warning("sentence-transformers not available for RAG")
    
    def _initialize_knowledge_base(self):
        """Initialize academic knowledge base with common topics"""
        self.knowledge_base = {
            'sciences': [
                {
                    'id': 'kb_sci_photosynthèse',
                    'title': 'Photosynthèse',
                    'content': """La photosynthèse est un processus biologique fondamental par lequel les plantes, les algues et certaines bactéries convertissent l'énergie lumineuse en énergie chimique utilisable. Ce processus utilise le dioxyde de carbone (CO2) présent dans l'atmosphère et l'eau (H2O) absorbée par les racines pour produire du glucose (C6H12O6), une molécule énergétique, et de l'oxygène (O2) comme sous-produit. La photosynthèse se déroule principalement dans les chloroplastes des cellules végétales, organites contenant la chlorophylle, le pigment vert qui capture l'énergie lumineuse.""",
                    'domain': 'sciences',
                    'tags': ['biologie', 'plante', 'énergie', 'CO2', 'oxygène']
                },
                {
                    'id': 'kb_sci_respiration',
                    'title': 'Respiration cellulaire',
                    'content': """La respiration cellulaire est le processus par lequel les cellules produisent de l'énergie (ATP) à partir du glucose et d'autres molécules organiques. Elle se déroule en trois étapes principales : la glycolyse dans le cytoplasme, le cycle de Krebs (cycle de l'acide citrique) dans la matrice mitochondriale, et la chaîne de transport d'électrons dans la membrane interne des mitochondries. La respiration cellulaire nécessite de l'oxygène (respiration aérobie) et produit du dioxyde de carbone, de l'eau et de l'ATP.""",
                    'domain': 'sciences',
                    'tags': ['biologie', 'cellule', 'ATP', 'énergie', 'mitochondrie']
                },
                {
                    'id': 'kb_sci_adn',
                    'title': 'Structure de l\'ADN',
                    'content': """L'ADN (acide désoxyribonucléique) est une molécule qui contient l'information génétique de tous les organismes vivants. L'ADN a une structure en double hélice, formée de deux brins complémentaires qui s'enroulent l'un autour de l'autre. Chaque brin est composé d'une chaîne de nucléotides, qui sont les unités de base de l'ADN. Chaque nucleotide contient trois composants : un groupe phosphate, un sucre désoxyribose, et une base azotée. Il existe quatre types de bases azotées dans l'ADN : l'adénine (A), la thymine (T), la guanine (G), et la cytosine (C).""",
                    'domain': 'sciences',
                    'tags': ['biologie', 'génétique', 'ADN', 'double hélice', 'nucléotide']
                }
            ],
            'littérature': [
                {
                    'id': 'kb_lit_romantisme',
                    'title': 'Le romantisme en littérature',
                    'content': """Le romantisme est un mouvement littéraire et artistique qui émerge en Europe à la fin du 18e siècle et domine le 19e siècle. Il privilégie l'expression des sentiments, l'individualité, l'imagination, et la nature. Les romantiques rejettent le rationalisme des Lumières et valorisent l'émotion, le mystère, et le sublime. En France, les principaux représentants du romantisme incluent Victor Hugo, Alphonse de Lamartine, et Alfred de Musset. Le mouvement influence profondément la poésie, le roman, et le théâtre de l'époque.""",
                    'domain': 'littérature',
                    'tags': ['romantisme', '19e siècle', 'Victor Hugo', 'poésie', 'roman']
                }
            ],
            'histoire': [
                {
                    'id': 'kb_hist_revolution',
                    'title': 'La révolution française de 1789',
                    'content': """La révolution française de 1789 est un événement majeur de l'histoire de France et de l'Europe. Les causes principales incluent les difficultés financières de la monarchie, les inégalités sociales profondes, l'influence des idées des Lumières, et les mauvaises récoltes. La révolution commence avec la convocation des États généraux en mai 1789, suivie de la prise de la Bastille le 14 juillet 1789. Elle conduit à l'abolition de la monarchie absolue, à la Déclaration des droits de l'homme et du citoyen, et à l'établissement de la Première République.""",
                    'domain': 'histoire',
                    'tags': ['révolution', '1789', 'France', 'monarchie', 'république']
                }
            ],
            'philosophie': [
                {
                    'id': 'kb_philo_ethique',
                    'title': 'Éthique et morale en philosophie',
                    'content': """L'éthique et la morale sont deux concepts distincts en philosophie. La morale désigne l'ensemble des règles et valeurs qui régissent le comportement humain dans une société donnée. L'éthique, quant à elle, est la réflexion philosophique sur la morale, l'étude critique des principes moraux et des valeurs. L'éthique examine les fondements de la morale, les critères du bien et du mal, et les principes qui devraient guider l'action humaine. Les principales théories éthiques incluent l'éthique déontologique (Kant), l'éthique conséquentialiste (utilitarisme), et l'éthique de la vertu (Aristote).""",
                    'domain': 'philosophie',
                    'tags': ['éthique', 'morale', 'philosophie', 'Kant', 'Aristote']
                }
            ],
            'informatique': [
                {
                    'id': 'kb_info_ia',
                    'title': 'Intelligence artificielle',
                    'content': """L'intelligence artificielle (IA) est un domaine interdisciplinaire de l'informatique qui vise à créer des systèmes capables d'effectuer des tâches qui nécessitent normalement l'intelligence humaine. Les applications de l'IA incluent la reconnaissance vocale et visuelle, la vision par ordinateur, le traitement du langage naturel (NLP), la robotique autonome, l'apprentissage automatique (machine learning), et l'apprentissage profond (deep learning). L'IA utilise des algorithmes complexes et des réseaux de neurones artificiels pour apprendre à partir de grandes quantités de données.""",
                    'domain': 'informatique',
                    'tags': ['IA', 'intelligence artificielle', 'machine learning', 'deep learning', 'NLP']
                }
            ]
        }
    
    def add_user_document(
        self,
        user_id: str,
        document_id: str,
        content: str,
        title: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Add a user document to the RAG system
        
        Args:
            user_id: User identifier
            document_id: Unique document identifier
            content: Document content
            title: Document title (optional)
            metadata: Additional metadata (optional)
        """
        if user_id not in self.user_documents:
            self.user_documents[user_id] = []
        
        document = {
            'id': document_id,
            'title': title or f'Document {document_id}',
            'content': content,
            'metadata': metadata or {},
            'user_id': user_id
        }
        
        self.user_documents[user_id].append(document)
        
        # Chunk the document and create embeddings
        chunks = self._chunk_text(content)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            if self.embedding_model:
                try:
                    embedding = self.embedding_model.encode(chunk)
                    self.chunk_embeddings[chunk_id] = {
                        'embedding': embedding,
                        'text': chunk,
                        'document_id': document_id,
                        'user_id': user_id
                    }
                except Exception as e:
                    logger.warning(f"Could not create embedding for chunk {chunk_id}: {e}")
        
        logger.info(f"Added document {document_id} for user {user_id} with {len(chunks)} chunks")
    
    def process_document(
        self,
        file_path: str,
        file_type: str,
        user_id: str,
        document_id: str,
        title: Optional[str] = None
    ) -> bool:
        """
        Process a document file: extract text and add to RAG system
        
        Args:
            file_path: Path to the document file
            file_type: Type of file (pdf, docx, txt, etc.)
            user_id: User identifier
            document_id: Document identifier
            title: Optional document title
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Import DocumentProcessor here to avoid circular imports
            from app.services.document_processor import DocumentProcessor
            processor = DocumentProcessor()
            
            # Extract text from document
            extracted_text = processor.extract_text_from_document(file_path, file_type)
            
            if not extracted_text or len(extracted_text.strip()) < 10:
                logger.warning(f"Could not extract meaningful text from document {file_path}")
                return False
            
            # Use filename as title if not provided
            if not title:
                import os
                title = os.path.basename(file_path)
            
            # Add document to RAG system
            self.add_user_document(
                user_id=str(user_id),
                document_id=str(document_id),
                content=extracted_text,
                title=title,
                metadata={
                    'file_path': file_path,
                    'file_type': file_type
                }
            )
            
            logger.info(f"Successfully processed document {document_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return False
    
    def _chunk_text(self, text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
        """
        Chunk text into smaller pieces for better retrieval
        
        Args:
            text: Text to chunk
            chunk_size: Maximum words per chunk
            overlap: Number of words to overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Split by sentences first
        sentences = re.split(r'[.!?]+\s+', text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            words = sentence.split()
            sentence_size = len(words)
            
            if current_size + sentence_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                # Start new chunk with overlap
                overlap_words = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_words + words
                current_size = len(current_chunk)
            else:
                current_chunk.extend(words)
                current_size += sentence_size
        
        # Add last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [text]
    
    def search(
        self,
        query: str,
        user_documents: Optional[List[str]] = None,
        domain: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Search for relevant documents/chunks
        
        Args:
            query: Search query
            user_documents: List of user document IDs to search in (optional)
            domain: Domain to search in knowledge base (optional)
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with scores
        """
        results = []
        
        # Search in user documents if provided
        if user_documents:
            user_results = self._search_user_documents(query, user_documents, top_k)
            results.extend(user_results)
        
        # Search in knowledge base
        kb_results = self._search_knowledge_base(query, domain, top_k)
        results.extend(kb_results)
        
        # Sort by relevance score and return top_k
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results[:top_k]
    
    def _search_user_documents(
        self,
        query: str,
        document_ids: List[str],
        top_k: int
    ) -> List[Dict]:
        """Search in user documents"""
        if not self.embedding_model:
            # Fallback to keyword search
            return self._keyword_search(query, document_ids, top_k)
        
        try:
            query_embedding = self.embedding_model.encode(query)
            results = []
            
            # Search in chunks from specified documents
            for chunk_id, chunk_data in self.chunk_embeddings.items():
                if chunk_data['document_id'] in document_ids:
                    chunk_embedding = chunk_data['embedding']
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                    
                    results.append({
                        'text': chunk_data['text'],
                        'score': float(similarity),
                        'source': 'user_document',
                        'document_id': chunk_data['document_id'],
                        'chunk_id': chunk_id
                    })
            
            # Sort and return top_k
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return self._keyword_search(query, document_ids, top_k)
    
    def _search_knowledge_base(
        self,
        query: str,
        domain: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict]:
        """Search in knowledge base"""
        results = []
        
        # Search in specific domain or all domains
        domains_to_search = [domain] if domain and domain in self.knowledge_base else list(self.knowledge_base.keys())
        
        if self.embedding_model:
            try:
                query_embedding = self.embedding_model.encode(query)
                
                for domain_name in domains_to_search:
                    for doc in self.knowledge_base.get(domain_name, []):
                        doc_embedding = self.embedding_model.encode(doc['content'])
                        similarity = self._cosine_similarity(query_embedding, doc_embedding)
                        
                        results.append({
                            'text': doc['content'],
                            'title': doc.get('title', ''),
                            'score': float(similarity),
                            'source': 'knowledge_base',
                            'domain': domain_name,
                            'doc_id': doc['id']
                        })
            except Exception as e:
                logger.error(f"Error in knowledge base semantic search: {e}")
                return self._keyword_search_kb(query, domain, top_k)
        else:
            return self._keyword_search_kb(query, domain, top_k)
        
        # Sort and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _keyword_search(
        self,
        query: str,
        document_ids: List[str],
        top_k: int
    ) -> List[Dict]:
        """Fallback keyword search in user documents"""
        query_words = set(query.lower().split())
        results = []
        
        for user_id, documents in self.user_documents.items():
            for doc in documents:
                if doc['id'] in document_ids:
                    content_lower = doc['content'].lower()
                    matches = sum(1 for word in query_words if word in content_lower)
                    if matches > 0:
                        score = matches / len(query_words) if query_words else 0
                        results.append({
                            'text': doc['content'][:500],  # First 500 chars
                            'score': score,
                            'source': 'user_document',
                            'document_id': doc['id']
                        })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _keyword_search_kb(
        self,
        query: str,
        domain: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict]:
        """Fallback keyword search in knowledge base"""
        query_words = set(query.lower().split())
        results = []
        
        domains_to_search = [domain] if domain and domain in self.knowledge_base else list(self.knowledge_base.keys())
        
        for domain_name in domains_to_search:
            for doc in self.knowledge_base.get(domain_name, []):
                content_lower = doc['content'].lower()
                matches = sum(1 for word in query_words if word in content_lower)
                if matches > 0:
                    score = matches / len(query_words) if query_words else 0
                    results.append({
                        'text': doc['content'],
                        'title': doc.get('title', ''),
                        'score': score,
                        'source': 'knowledge_base',
                        'domain': domain_name,
                        'doc_id': doc['id']
                    })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    def get_context_for_qa(
        self,
        question: str,
        user_id: Optional[str] = None,
        domain: Optional[str] = None,
        max_chunks: int = 5
    ) -> str:
        """
        Get relevant context for QA from RAG
        
        Args:
            question: The question
            user_id: User ID to search in their documents (optional)
            domain: Domain to search in knowledge base (optional)
            max_chunks: Maximum number of chunks to return
            
        Returns:
            Combined context string
        """
        # Get user document IDs if user_id provided
        user_doc_ids = None
        if user_id and user_id in self.user_documents:
            user_doc_ids = [doc['id'] for doc in self.user_documents[user_id]]
        
        # Search for relevant chunks
        results = self.search(
            query=question,
            user_documents=user_doc_ids,
            domain=domain,
            top_k=max_chunks
        )
        
        if not results:
            return ""
        
        # Combine chunks into context
        context_parts = []
        for result in results:
            text = result.get('text', '')
            if text:
                context_parts.append(text)
        
        context = "\n\n".join(context_parts)
        
        # Limit context length (keep most relevant parts)
        if len(context) > 2000:
            # Keep first 2000 characters (most relevant)
            context = context[:2000]
            # Try to end at sentence boundary
            last_period = context.rfind('.')
            if last_period > 1500:
                context = context[:last_period + 1]
        
        return context
