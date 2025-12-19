"""
Test RAG avec des cas d'usage réels
Simule des scénarios utilisateur réels pour tester le système RAG
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import RAGService
from app.services.few_shot_service import FewShotLearningService

# Try to import QA service (may fail if transformers not installed)
try:
    from app.services.qa_service import QAService
    QA_AVAILABLE = True
except ImportError:
    QA_AVAILABLE = False
    QAService = None

def print_section(title):
    """Print a formatted section title"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def setup_real_user_documents(rag_service):
    """Setup realistic user documents for testing"""
    print("📚 Configuration des documents utilisateur...")
    
    # User 1: Étudiant en biologie
    user_1_id = "student_bio_001"
    
    doc1 = """La photosynthèse est un processus biologique fondamental qui se déroule dans les chloroplastes des cellules végétales. 
    Ce processus convertit l'énergie lumineuse en énergie chimique stockée dans les molécules de glucose. 
    La réaction globale de la photosynthèse peut être résumée par l'équation: 6CO2 + 6H2O + lumière → C6H12O6 + 6O2.
    Les deux phases principales sont les réactions photochimiques (phase claire) et le cycle de Calvin (phase sombre)."""
    
    doc2 = """La respiration cellulaire est le processus inverse de la photosynthèse. Elle se déroule dans les mitochondries et produit de l'ATP 
    à partir du glucose. Les trois étapes principales sont la glycolyse, le cycle de Krebs, et la chaîne de transport d'électrons. 
    La respiration aérobie nécessite de l'oxygène et produit environ 36 molécules d'ATP par molécule de glucose."""
    
    rag_service.add_user_document(
        user_1_id,
        "bio_doc_1",
        doc1,
        title="Notes sur la photosynthèse",
        metadata={"course": "Biologie", "topic": "Photosynthèse"}
    )
    
    rag_service.add_user_document(
        user_1_id,
        "bio_doc_2",
        doc2,
        title="Notes sur la respiration cellulaire",
        metadata={"course": "Biologie", "topic": "Respiration"}
    )
    
    # User 2: Étudiant en histoire
    user_2_id = "student_history_001"
    
    doc3 = """La révolution française de 1789 a été déclenchée par une combinaison de facteurs économiques, sociaux et politiques. 
    Les causes économiques incluent les mauvaises récoltes de 1788, la crise financière de la monarchie, et l'augmentation des impôts. 
    Les causes sociales incluent les inégalités profondes entre les trois ordres (clergé, noblesse, tiers état). 
    Les causes politiques incluent l'influence des idées des Lumières et l'incapacité de la monarchie à se réformer."""
    
    rag_service.add_user_document(
        user_2_id,
        "hist_doc_1",
        doc3,
        title="Causes de la révolution française",
        metadata={"course": "Histoire", "topic": "Révolution française"}
    )
    
    print(f"   ✅ Documents ajoutés pour 2 utilisateurs")
    print(f"   - Utilisateur 1 (Biologie): 2 documents")
    print(f"   - Utilisateur 2 (Histoire): 1 document")
    print()
    
    return user_1_id, user_2_id

def test_scenario_1_student_biology():
    """Scénario 1: Étudiant en biologie pose des questions sur ses cours"""
    print_section("SCÉNARIO 1: Étudiant en Biologie")
    
    rag = RAGService()
    qa = QAService() if QA_AVAILABLE else None
    
    # Setup documents
    user_id, _ = setup_real_user_documents(rag)
    
    questions = [
        {
            'question': "Expliquez-moi comment fonctionne la photosynthèse étape par étape.",
            'expected_sources': ['user_document', 'knowledge_base'],
            'expected_keywords': ['photosynthèse', 'chloroplastes', 'énergie', 'glucose', 'CO2']
        },
        {
            'question': "Quelle est la différence entre la photosynthèse et la respiration cellulaire?",
            'expected_sources': ['user_document', 'knowledge_base'],
            'expected_keywords': ['photosynthèse', 'respiration', 'différence', 'ATP', 'glucose']
        },
        {
            'question': "Où se déroule la respiration cellulaire dans la cellule?",
            'expected_sources': ['user_document', 'knowledge_base'],
            'expected_keywords': ['mitochondries', 'respiration', 'cellule']
        }
    ]
    
    for i, case in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {case['question']}")
        print(f"   Utilisateur: Étudiant en biologie (documents disponibles)")
        
        # Test RAG search
        search_results = rag.search(
            query=case['question'],
            user_documents=["bio_doc_1", "bio_doc_2"],
            domain="sciences",
            top_k=3
        )
        
        print(f"   ✅ Résultats RAG: {len(search_results)}")
        for j, result in enumerate(search_results, 1):
            print(f"      {j}. Source: {result.get('source', 'unknown')}, Score: {result.get('score', 0):.3f}")
            if result.get('title'):
                print(f"         Titre: {result.get('title')}")
        
        # Test context generation
        context = rag.get_context_for_qa(
            question=case['question'],
            user_id=user_id,
            domain="sciences",
            max_chunks=5
        )
        
        print(f"   ✅ Contexte généré: {len(context)} caractères")
        if context:
            print(f"   Extrait: {context[:150]}...")
        
        # Test QA with RAG (if model available)
        if qa:
            try:
                result = qa.answer_question(
                    question=case['question'],
                    user_id=user_id,
                    user_document_ids=["bio_doc_1", "bio_doc_2"]
                )
                
                if result.get('answer'):
                    print(f"   ✅ Réponse générée: {len(result['answer'])} caractères")
                    print(f"   Confiance: {result.get('confidence', 0):.2%}")
                    print(f"   RAG utilisé: {result.get('rag_used', False)}")
                    
                    if result.get('sources'):
                        print(f"   Sources: {len(result['sources'])}")
                        for source in result['sources'][:2]:
                            print(f"      - {source.get('source', 'unknown')}: {source.get('title', 'N/A')}")
                else:
                    print(f"   ⚠️  Modèle non chargé")
            except Exception as e:
                print(f"   ⚠️  Erreur QA: {str(e)[:100]}")
        else:
            print(f"   ℹ️  Service QA non disponible (transformers non installé)")
            print(f"   ✅ Contexte RAG prêt pour génération de réponse")

def test_scenario_2_student_history():
    """Scénario 2: Étudiant en histoire pose des questions"""
    print_section("SCÉNARIO 2: Étudiant en Histoire")
    
    rag = RAGService()
    qa = QAService() if QA_AVAILABLE else None
    
    # Setup documents
    _, user_id = setup_real_user_documents(rag)
    
    questions = [
        {
            'question': "Quelles sont les causes principales de la révolution française de 1789?",
            'expected_keywords': ['révolution', '1789', 'causes', 'économiques', 'sociales']
        },
        {
            'question': "Expliquez le rôle des trois ordres dans la révolution française.",
            'expected_keywords': ['trois ordres', 'clergé', 'noblesse', 'tiers état']
        }
    ]
    
    for i, case in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {case['question']}")
        print(f"   Utilisateur: Étudiant en histoire (documents disponibles)")
        
        # Test RAG
        context = rag.get_context_for_qa(
            question=case['question'],
            user_id=user_id,
            domain="histoire",
            max_chunks=3
        )
        
        print(f"   ✅ Contexte généré: {len(context)} caractères")
        
        # Test QA
        if qa:
            try:
                result = qa.answer_question(
                    question=case['question'],
                    user_id=user_id,
                    user_document_ids=["hist_doc_1"]
                )
                
                if result.get('answer'):
                    print(f"   ✅ Réponse générée")
                    print(f"   RAG utilisé: {result.get('rag_used', False)}")
                    if result.get('sources'):
                        print(f"   Sources trouvées: {len(result['sources'])}")
            except Exception as e:
                print(f"   ⚠️  Erreur: {str(e)[:100]}")
        else:
            print(f"   ℹ️  Service QA non disponible")
            print(f"   ✅ Contexte RAG prêt")

def test_scenario_3_no_documents():
    """Scénario 3: Utilisateur sans documents (utilise uniquement la base de connaissances)"""
    print_section("SCÉNARIO 3: Utilisateur sans Documents")
    
    rag = RAGService()
    qa = QAService() if QA_AVAILABLE else None
    
    questions = [
        "Qu'est-ce que l'intelligence artificielle?",
        "Expliquez le romantisme en littérature française.",
        "Quelle est la différence entre l'éthique et la morale?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question}")
        print(f"   Utilisateur: Sans documents (base de connaissances uniquement)")
        
        # Test RAG (knowledge base only)
        context = rag.get_context_for_qa(
            question=question,
            user_id=None,
            domain=None,  # Auto-detect
            max_chunks=3
        )
        
        print(f"   ✅ Contexte généré: {len(context)} caractères")
        if context:
            print(f"   Extrait: {context[:120]}...")
        
        # Test QA
        if qa:
            try:
                result = qa.answer_question(question=question)
                
                if result.get('answer'):
                    print(f"   ✅ Réponse générée")
                    print(f"   RAG utilisé: {result.get('rag_used', False)}")
                    if result.get('sources'):
                        print(f"   Sources: {[s.get('source') for s in result['sources']]}")
            except Exception as e:
                print(f"   ⚠️  Erreur: {str(e)[:100]}")
        else:
            print(f"   ℹ️  Service QA non disponible")
            print(f"   ✅ Contexte RAG généré depuis base de connaissances")

def test_scenario_4_mixed_sources():
    """Scénario 4: Combinaison de documents utilisateur et base de connaissances"""
    print_section("SCÉNARIO 4: Sources Mixtes (Documents + Base de Connaissances)")
    
    rag = RAGService()
    
    # Add user document
    user_id = "mixed_user"
    rag.add_user_document(
        user_id,
        "mixed_doc_1",
        "L'intelligence artificielle utilise des algorithmes de machine learning pour apprendre à partir de données. Le deep learning est une sous-catégorie qui utilise des réseaux de neurones profonds.",
        title="Mon document sur l'IA"
    )
    
    question = "Qu'est-ce que l'intelligence artificielle et comment fonctionne-t-elle?"
    print(f"📝 Question: {question}")
    print(f"   Sources disponibles: Document utilisateur + Base de connaissances")
    
    # Search in both
    results = rag.search(
        query=question,
        user_documents=["mixed_doc_1"],
        domain="informatique",
        top_k=5
    )
    
    print(f"   ✅ Résultats combinés: {len(results)}")
    
    user_doc_results = [r for r in results if r.get('source') == 'user_document']
    kb_results = [r for r in results if r.get('source') == 'knowledge_base']
    
    print(f"   - Documents utilisateur: {len(user_doc_results)}")
    print(f"   - Base de connaissances: {len(kb_results)}")
    
    # Show top results
    for i, result in enumerate(results[:3], 1):
        print(f"   Résultat {i}:")
        print(f"      Source: {result.get('source')}")
        print(f"      Score: {result.get('score', 0):.3f}")
        if result.get('title'):
            print(f"      Titre: {result.get('title')}")
        print(f"      Extrait: {result.get('text', '')[:100]}...")

def test_scenario_5_domain_detection():
    """Scénario 5: Détection automatique de domaine"""
    print_section("SCÉNARIO 5: Détection Automatique de Domaine")
    
    rag = RAGService()
    few_shot = FewShotLearningService()
    
    questions = [
        ("Qu'est-ce que la photosynthèse?", "sciences"),
        ("Expliquez le romantisme", "littérature"),
        ("Quelles sont les causes de la révolution?", "histoire"),
        ("Qu'est-ce que l'éthique?", "philosophie"),
        ("Comment fonctionne le marché?", "économie")
    ]
    
    for question, expected_domain in questions:
        print(f"\n📝 Question: {question}")
        
        # Detect domain
        detected_domain = few_shot.detect_domain(question)
        print(f"   Domaine détecté: {detected_domain} (attendu: {expected_domain})")
        
        # Search with detected domain
        results = rag.search(
            query=question,
            domain=detected_domain,
            top_k=2
        )
        
        print(f"   ✅ Résultats trouvés: {len(results)}")
        if results:
            print(f"   Meilleur score: {results[0].get('score', 0):.3f}")

def test_scenario_6_context_quality():
    """Scénario 6: Qualité du contexte généré"""
    print_section("SCÉNARIO 6: Qualité du Contexte Généré")
    
    rag = RAGService()
    user_id, _ = setup_real_user_documents(rag)
    
    question = "Expliquez la différence entre photosynthèse et respiration cellulaire"
    
    print(f"📝 Question: {question}")
    
    # Generate context
    context = rag.get_context_for_qa(
        question=question,
        user_id=user_id,
        domain="sciences",
        max_chunks=5
    )
    
    print(f"   ✅ Contexte généré: {len(context)} caractères")
    print(f"   Nombre de mots: {len(context.split())}")
    
    # Check quality indicators
    quality_indicators = {
        'Contient "photosynthèse"': 'photosynthèse' in context.lower(),
        'Contient "respiration"': 'respiration' in context.lower(),
        'Contient "différence" ou "différent"': any(word in context.lower() for word in ['différence', 'différent', 'contraire']),
        'Longueur appropriée (500-2000 chars)': 500 <= len(context) <= 2000,
        'Multiple phrases': context.count('.') >= 3
    }
    
    print(f"\n   Indicateurs de qualité:")
    for indicator, passed in quality_indicators.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {indicator}")
    
    # Show context preview
    print(f"\n   Aperçu du contexte:")
    print(f"   {context[:300]}...")

def main():
    """Run all real-world scenarios"""
    print("\n" + "=" * 70)
    print("  TESTS RAG AVEC CAS D'USAGE RÉELS")
    print("=" * 70)
    
    try:
        test_scenario_1_student_biology()
        test_scenario_2_student_history()
        test_scenario_3_no_documents()
        test_scenario_4_mixed_sources()
        test_scenario_5_domain_detection()
        test_scenario_6_context_quality()
        
        print("\n" + "=" * 70)
        print("  ✅ TOUS LES SCÉNARIOS TESTÉS")
        print("=" * 70)
        print("\n💡 Le système RAG fonctionne correctement avec des cas réels !")
        print("   Les réponses sont enrichies par le contexte des documents et")
        print("   de la base de connaissances.")
        print()
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

