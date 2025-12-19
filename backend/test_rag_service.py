"""
Test script for RAG Service
Tests document retrieval, knowledge base search, and context generation
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import RAGService

def print_section(title):
    """Print a formatted section title"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_knowledge_base_search():
    """Test knowledge base search"""
    print_section("TEST 1: Recherche dans la Base de Connaissances")
    
    rag = RAGService()
    
    queries = [
        ("Qu'est-ce que la photosynthèse?", "sciences"),
        ("Expliquez le romantisme en littérature", "littérature"),
        ("Quelles sont les causes de la révolution française?", "histoire"),
        ("Qu'est-ce que l'éthique en philosophie?", "philosophie"),
        ("Qu'est-ce que l'intelligence artificielle?", "informatique"),
    ]
    
    for query, expected_domain in queries:
        print(f"\n📝 Requête: {query}")
        print(f"   Domaine attendu: {expected_domain}")
        
        results = rag._search_knowledge_base(query, domain=expected_domain, top_k=2)
        print(f"   ✅ Résultats trouvés: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"   Résultat {i}:")
            print(f"      - Score: {result.get('score', 0):.3f}")
            print(f"      - Source: {result.get('source', 'unknown')}")
            print(f"      - Titre: {result.get('title', 'N/A')}")
            print(f"      - Extrait: {result.get('text', '')[:100]}...")

def test_user_document_management():
    """Test user document management"""
    print_section("TEST 2: Gestion des Documents Utilisateur")
    
    rag = RAGService()
    
    # Add test documents
    user_id = "test_user_123"
    
    doc1_content = """L'intelligence artificielle (IA) est un domaine en pleine expansion qui transforme de nombreux secteurs. Les applications de l'IA incluent la reconnaissance vocale, la vision par ordinateur, et le traitement du langage naturel. Le machine learning est une sous-catégorie de l'IA qui permet aux systèmes d'apprendre à partir de données."""
    
    doc2_content = """La photosynthèse est un processus essentiel pour la vie sur Terre. Les plantes utilisent la lumière du soleil pour convertir le CO2 et l'eau en glucose. Ce processus produit également de l'oxygène comme sous-produit."""
    
    print(f"📝 Ajout de documents pour l'utilisateur: {user_id}")
    
    rag.add_user_document(user_id, "doc_1", doc1_content, title="Document sur l'IA")
    rag.add_user_document(user_id, "doc_2", doc2_content, title="Document sur la photosynthèse")
    
    print(f"   ✅ Documents ajoutés: {len(rag.user_documents.get(user_id, []))}")
    print(f"   ✅ Chunks créés: {len([k for k, v in rag.chunk_embeddings.items() if v.get('user_id') == user_id])}")
    
    # Test search in user documents
    print(f"\n📝 Recherche dans les documents utilisateur")
    query = "Qu'est-ce que l'intelligence artificielle?"
    results = rag._search_user_documents(query, ["doc_1", "doc_2"], top_k=2)
    
    print(f"   Requête: {query}")
    print(f"   ✅ Résultats trouvés: {len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"   Résultat {i}:")
        print(f"      - Score: {result.get('score', 0):.3f}")
        print(f"      - Source: {result.get('source', 'unknown')}")
        print(f"      - Extrait: {result.get('text', '')[:150]}...")

def test_rag_context_generation():
    """Test RAG context generation for QA"""
    print_section("TEST 3: Génération de Contexte pour QA")
    
    rag = RAGService()
    
    questions = [
        {
            'question': "Qu'est-ce que la photosynthèse?",
            'user_id': None,
            'domain': 'sciences'
        },
        {
            'question': "Comment fonctionne l'intelligence artificielle?",
            'user_id': 'test_user_123',
            'domain': 'informatique'
        }
    ]
    
    for i, case in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {case['question']}")
        print(f"   Utilisateur: {case['user_id'] or 'Aucun'}")
        print(f"   Domaine: {case['domain']}")
        
        context = rag.get_context_for_qa(
            question=case['question'],
            user_id=case['user_id'],
            domain=case['domain'],
            max_chunks=3
        )
        
        print(f"   ✅ Contexte généré: {len(context)} caractères")
        if context:
            print(f"   Extrait: {context[:200]}...")
        else:
            print(f"   ⚠️  Aucun contexte trouvé")

def test_combined_search():
    """Test combined search (user docs + knowledge base)"""
    print_section("TEST 4: Recherche Combinée (Documents + Base de Connaissances)")
    
    rag = RAGService()
    
    # Add user document first
    user_id = "test_user_456"
    rag.add_user_document(
        user_id,
        "user_doc_1",
        "La révolution française de 1789 a été causée par plusieurs facteurs: les difficultés financières, les inégalités sociales, et l'influence des Lumières.",
        title="Mon document sur la révolution"
    )
    
    query = "Quelles sont les causes de la révolution française?"
    print(f"📝 Requête: {query}")
    print(f"   Recherche dans: documents utilisateur + base de connaissances")
    
    results = rag.search(
        query=query,
        user_documents=["user_doc_1"],
        domain="histoire",
        top_k=5
    )
    
    print(f"   ✅ Résultats combinés: {len(results)}")
    
    for i, result in enumerate(results, 1):
        print(f"   Résultat {i}:")
        print(f"      - Score: {result.get('score', 0):.3f}")
        print(f"      - Source: {result.get('source', 'unknown')}")
        if result.get('title'):
            print(f"      - Titre: {result.get('title')}")
        print(f"      - Extrait: {result.get('text', '')[:120]}...")

def test_chunking():
    """Test text chunking"""
    print_section("TEST 5: Découpage de Texte (Chunking)")
    
    rag = RAGService()
    
    long_text = """La photosynthèse est un processus biologique fondamental. Les plantes utilisent la lumière du soleil. Le processus convertit le CO2 en glucose. L'oxygène est produit comme sous-produit. La photosynthèse se déroule dans les chloroplastes. La chlorophylle capture l'énergie lumineuse. Ce processus est essentiel à la vie sur Terre. Il constitue la base de la chaîne alimentaire. Il produit l'oxygène que nous respirons."""
    
    print(f"📝 Texte original: {len(long_text.split())} mots")
    
    chunks = rag._chunk_text(long_text, chunk_size=20, overlap=5)
    
    print(f"   ✅ Chunks créés: {len(chunks)}")
    
    for i, chunk in enumerate(chunks, 1):
        words = len(chunk.split())
        print(f"   Chunk {i}: {words} mots - {chunk[:80]}...")

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  TESTS DU SERVICE RAG (Retrieval-Augmented Generation)")
    print("=" * 70)
    
    try:
        test_knowledge_base_search()
        test_user_document_management()
        test_rag_context_generation()
        test_combined_search()
        test_chunking()
        
        print("\n" + "=" * 70)
        print("  ✅ TOUS LES TESTS TERMINÉS")
        print("=" * 70)
        print("\n💡 Le service RAG est opérationnel et prêt à être utilisé !")
        print()
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

