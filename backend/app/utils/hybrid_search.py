"""
Recherche hybride combinant BM25 (lexical) et recherche sémantique
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from app.models import Message, ChatSession
from app.utils.logger import get_logger
import math

logger = get_logger()

# Tentative d'import rank_bm25
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    BM25Okapi = None


class HybridSearch:
    """Service de recherche hybride BM25 + Sémantique"""
    
    def __init__(self):
        self.bm25_available = BM25_AVAILABLE
        if not BM25_AVAILABLE:
            logger.warning("rank_bm25 not available, using fallback BM25 implementation")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenise le texte pour BM25
        
        Args:
            text: Texte à tokeniser
        
        Returns:
            Liste de tokens
        """
        # Tokenisation simple (peut être améliorée avec NLTK ou spaCy)
        import re
        # Supprimer la ponctuation et convertir en minuscules
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Diviser en mots
        tokens = text.split()
        # Filtrer les mots vides (stop words basiques)
        stop_words = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'à', 'dans', 'sur', 'pour', 'avec', 'par', 'est', 'sont', 'être', 'avoir', 'a', 'ce', 'cette', 'ces', 'que', 'qui', 'quoi', 'comment', 'pourquoi', 'quand', 'où'}
        return [token for token in tokens if token not in stop_words and len(token) > 2]
    
    def _build_bm25_index(self, documents: List[str]) -> Optional[Any]:
        """
        Construit un index BM25 à partir des documents
        
        Args:
            documents: Liste de textes de documents
        
        Returns:
            Index BM25 ou None
        """
        if not documents:
            return None
        
        # Tokeniser tous les documents
        tokenized_docs = [self._tokenize(doc) for doc in documents]
        
        if BM25_AVAILABLE:
            try:
                return BM25Okapi(tokenized_docs)
            except Exception as e:
                logger.error(f"Error building BM25 index: {e}")
                return None
        else:
            # Fallback: implémentation BM25 simple
            return self._build_simple_bm25(tokenized_docs)
    
    def _build_simple_bm25(self, tokenized_docs: List[List[str]]) -> Dict[str, Any]:
        """
        Implémentation simple de BM25 (fallback)
        
        Args:
            tokenized_docs: Documents tokenisés
        
        Returns:
            Index BM25 simple
        """
        # Calculer les fréquences de termes
        doc_freqs = {}
        doc_lengths = []
        term_freqs = []
        
        for doc in tokenized_docs:
            doc_lengths.append(len(doc))
            term_freq = {}
            for term in doc:
                term_freq[term] = term_freq.get(term, 0) + 1
                doc_freqs[term] = doc_freqs.get(term, 0) + 1
            term_freqs.append(term_freq)
        
        avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0
        num_docs = len(tokenized_docs)
        
        return {
            "term_freqs": term_freqs,
            "doc_freqs": doc_freqs,
            "doc_lengths": doc_lengths,
            "avg_doc_length": avg_doc_length,
            "num_docs": num_docs
        }
    
    def _bm25_score(self, query_tokens: List[str], doc_index: int, bm25_index: Any) -> float:
        """
        Calcule le score BM25 pour un document
        
        Args:
            query_tokens: Tokens de la requête
            doc_index: Index du document
            bm25_index: Index BM25
        
        Returns:
            Score BM25
        """
        if BM25_AVAILABLE and hasattr(bm25_index, 'get_scores'):
            try:
                scores = bm25_index.get_scores(query_tokens)
                return scores[doc_index] if doc_index < len(scores) else 0.0
            except Exception:
                return 0.0
        else:
            # Fallback: calcul BM25 simple
            return self._simple_bm25_score(query_tokens, doc_index, bm25_index)
    
    def _simple_bm25_score(self, query_tokens: List[str], doc_index: int, bm25_index: Dict[str, Any]) -> float:
        """
        Calcul BM25 simple (fallback)
        
        Args:
            query_tokens: Tokens de la requête
            doc_index: Index du document
            bm25_index: Index BM25 simple
        
        Returns:
            Score BM25
        """
        k1 = 1.5
        b = 0.75
        
        score = 0.0
        term_freqs = bm25_index["term_freqs"]
        doc_freqs = bm25_index["doc_freqs"]
        doc_lengths = bm25_index["doc_lengths"]
        avg_doc_length = bm25_index["avg_doc_length"]
        num_docs = bm25_index["num_docs"]
        
        if doc_index >= len(term_freqs):
            return 0.0
        
        doc_term_freq = term_freqs[doc_index]
        doc_length = doc_lengths[doc_index]
        
        for term in query_tokens:
            if term not in doc_term_freq:
                continue
            
            tf = doc_term_freq[term]
            df = doc_freqs.get(term, 0)
            
            if df == 0:
                continue
            
            idf = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
            
            score += idf * (numerator / denominator)
        
        return score
    
    def _semantic_search(self, query: str, messages: List[Message], k: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche sémantique basée sur les embeddings
        
        Args:
            query: Requête de recherche
            messages: Liste de messages à rechercher
            k: Nombre de résultats
        
        Returns:
            Liste de résultats avec scores sémantiques
        """
        try:
            from app.services.rag_service import RAGService
            rag_service = RAGService()
            
            if not rag_service.embeddings or not rag_service.vectorstore:
                return []
            
            # Créer des embeddings pour la requête
            query_embedding = rag_service.embeddings.embed_query(query)
            
            # Recherche dans le vectorstore
            # Note: Cette implémentation nécessite que les messages soient dans le vectorstore
            # Pour une implémentation complète, il faudrait mapper les messages aux chunks
            
            # Pour l'instant, retourner une recherche basique
            results = []
            for message in messages:
                # Calculer une similarité simple (peut être améliorée)
                similarity = self._simple_similarity(query.lower(), message.content.lower())
                results.append({
                    "message": message,
                    "semantic_score": similarity
                })
            
            # Trier par score et retourner les top k
            results.sort(key=lambda x: x["semantic_score"], reverse=True)
            return results[:k]
        except Exception as e:
            logger.error(f"Error in semantic search: {e}", exc_info=e)
            return []
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """
        Similarité simple basée sur les mots communs
        
        Args:
            text1: Premier texte
            text2: Deuxième texte
        
        Returns:
            Score de similarité (0-1)
        """
        words1 = set(self._tokenize(text1))
        words2 = set(self._tokenize(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def hybrid_search(
        self,
        db: Session,
        user_id: int,
        query: str,
        k: int = 10,
        bm25_weight: float = 0.4,
        semantic_weight: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Recherche hybride combinant BM25 et recherche sémantique
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            query: Requête de recherche
            k: Nombre de résultats à retourner
            bm25_weight: Poids du score BM25 (défaut: 0.4)
            semantic_weight: Poids du score sémantique (défaut: 0.6)
        
        Returns:
            Liste de résultats avec scores hybrides
        """
        try:
            # Récupérer tous les messages de l'utilisateur
            messages = db.query(Message).join(ChatSession).filter(
                ChatSession.user_id == user_id
            ).all()
            
            if not messages:
                return []
            
            # Préparer les documents pour BM25
            documents = [msg.content for msg in messages]
            
            # Construire l'index BM25
            bm25_index = self._build_bm25_index(documents)
            if not bm25_index:
                logger.warning("BM25 index not available, using semantic search only")
                bm25_weight = 0.0
                semantic_weight = 1.0
            
            # Tokeniser la requête
            query_tokens = self._tokenize(query)
            
            # Calculer les scores BM25
            bm25_scores = {}
            if bm25_index and bm25_weight > 0:
                for i, message in enumerate(messages):
                    score = self._bm25_score(query_tokens, i, bm25_index)
                    bm25_scores[message.id] = score
            
            # Normaliser les scores BM25
            if bm25_scores:
                max_bm25 = max(bm25_scores.values()) if bm25_scores.values() else 1.0
                if max_bm25 > 0:
                    bm25_scores = {msg_id: score / max_bm25 for msg_id, score in bm25_scores.items()}
            
            # Recherche sémantique
            semantic_results = self._semantic_search(query, messages, k=k*2)  # Récupérer plus pour combiner
            semantic_scores = {r["message"].id: r["semantic_score"] for r in semantic_results}
            
            # Normaliser les scores sémantiques
            if semantic_scores:
                max_semantic = max(semantic_scores.values()) if semantic_scores.values() else 1.0
                if max_semantic > 0:
                    semantic_scores = {msg_id: score / max_semantic for msg_id, score in semantic_scores.items()}
            
            # Combiner les scores
            hybrid_results = []
            all_message_ids = set(bm25_scores.keys()) | set(semantic_scores.keys())
            
            for msg_id in all_message_ids:
                message = next((m for m in messages if m.id == msg_id), None)
                if not message:
                    continue
                
                bm25_score = bm25_scores.get(msg_id, 0.0) * bm25_weight
                semantic_score = semantic_scores.get(msg_id, 0.0) * semantic_weight
                hybrid_score = bm25_score + semantic_score
                
                hybrid_results.append({
                    "message_id": message.id,
                    "session_id": message.session_id,
                    "content": message.content,
                    "role": message.role,
                    "module_type": message.module_type,
                    "created_at": message.created_at.isoformat(),
                    "bm25_score": bm25_scores.get(msg_id, 0.0),
                    "semantic_score": semantic_scores.get(msg_id, 0.0),
                    "hybrid_score": hybrid_score
                })
            
            # Trier par score hybride et retourner les top k
            hybrid_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
            
            logger.info(
                f"Hybrid search completed",
                extra_data={"query": query[:50], "results_count": len(hybrid_results[:k]), "user_id": user_id}
            )
            
            return hybrid_results[:k]
        
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}", exc_info=e)
            return []

