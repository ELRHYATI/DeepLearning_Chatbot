"""
Test script for Few-Shot Learning Service
Tests domain detection, example loading, and prompt generation
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.few_shot_service import FewShotLearningService

def test_domain_detection():
    """Test domain detection"""
    print("=" * 60)
    print("TEST 1: Détection de Domaine")
    print("=" * 60)
    
    service = FewShotLearningService()
    
    test_cases = [
        ("Qu'est-ce que la photosynthèse?", "sciences"),
        ("Expliquez le romantisme en littérature", "littérature"),
        ("Quelles sont les causes de la révolution française?", "histoire"),
        ("Qu'est-ce que l'éthique en philosophie?", "philosophie"),
        ("Comment fonctionne le marché économique?", "économie"),
        ("Qu'est-ce que le machine learning?", "informatique"),
        ("Expliquez le comportement cognitif", "psychologie"),
        ("Décrivez le climat de la France", "géographie"),
        ("Qu'est-ce que la stratification sociale?", "sociologie"),
        ("Bonjour, comment allez-vous?", "general"),
    ]
    
    for text, expected_domain in test_cases:
        detected = service.detect_domain(text)
        status = "✅" if detected == expected_domain else "❌"
        print(f"{status} Texte: '{text[:50]}...'")
        print(f"   Attendu: {expected_domain}, Détecté: {detected}")
        print()

def test_example_loading():
    """Test example loading"""
    print("=" * 60)
    print("TEST 2: Chargement des Exemples")
    print("=" * 60)
    
    service = FewShotLearningService()
    
    # Test QA examples
    qa_examples = service.get_examples('qa', domain='sciences', max_examples=2)
    print(f"✅ Exemples QA Sciences: {len(qa_examples)} trouvés")
    if qa_examples:
        print(f"   Premier exemple: {qa_examples[0].get('question', 'N/A')[:50]}...")
    print()
    
    # Test reformulation examples
    reform_examples = service.get_examples('reformulation', domain='sciences', style='academic', max_examples=2)
    print(f"✅ Exemples Reformulation Académique Sciences: {len(reform_examples)} trouvés")
    if reform_examples:
        print(f"   Premier exemple: {reform_examples[0].get('original', 'N/A')[:50]}...")
    print()
    
    # Test plan examples
    plan_examples = service.get_examples('plan', style='academic', max_examples=1)
    print(f"✅ Exemples Plan Académique: {len(plan_examples)} trouvés")
    if plan_examples:
        print(f"   Premier exemple: {plan_examples[0].get('topic', 'N/A')[:50]}...")
    print()

def test_prompt_generation():
    """Test prompt generation"""
    print("=" * 60)
    print("TEST 3: Génération de Prompts")
    print("=" * 60)
    
    service = FewShotLearningService()
    
    # Test QA prompt
    qa_prompt = service.build_enhanced_prompt(
        text="Qu'est-ce que la photosynthèse?",
        task_type='qa',
        domain='sciences',
        include_examples=True
    )
    print("✅ Prompt QA Sciences généré:")
    print(f"   Longueur: {len(qa_prompt)} caractères")
    print(f"   Contient 'Exemples': {'Exemples' in qa_prompt}")
    print(f"   Contient 'expert': {'expert' in qa_prompt.lower()}")
    print()
    
    # Test reformulation prompt
    reform_prompt = service.build_enhanced_prompt(
        text="Les chercheurs ont trouvé quelque chose d'important.",
        task_type='reformulation',
        style='academic',
        domain='sciences',
        include_examples=True
    )
    print("✅ Prompt Reformulation Académique Sciences généré:")
    print(f"   Longueur: {len(reform_prompt)} caractères")
    print(f"   Contient 'Exemples': {'Exemples' in reform_prompt}")
    print(f"   Contient 'académique': {'académique' in reform_prompt.lower()}")
    print()
    
    # Test plan prompt
    plan_prompt = service.build_enhanced_prompt(
        text="L'impact de l'intelligence artificielle sur l'éducation",
        task_type='plan',
        style='academic',
        domain='informatique',
        include_examples=True
    )
    print("✅ Prompt Plan Académique Informatique généré:")
    print(f"   Longueur: {len(plan_prompt)} caractères")
    print(f"   Contient 'Exemples': {'Exemples' in plan_prompt}")
    print(f"   Contient 'plan': {'plan' in plan_prompt.lower()}")
    print()

def test_example_addition():
    """Test adding new examples"""
    print("=" * 60)
    print("TEST 4: Ajout d'Exemples")
    print("=" * 60)
    
    service = FewShotLearningService()
    
    # Add a new QA example
    new_example = {
        'question': "Comment fonctionne la respiration cellulaire?",
        'context': "La respiration cellulaire produit de l'ATP.",
        'answer': "La respiration cellulaire est le processus par lequel les cellules produisent de l'énergie ATP à partir du glucose."
    }
    
    initial_count = len(service.get_examples('qa', domain='sciences'))
    service.add_example('qa', new_example, domain='sciences')
    final_count = len(service.get_examples('qa', domain='sciences'))
    
    print(f"✅ Exemple ajouté: {initial_count} -> {final_count} exemples")
    print()

def test_example_formatting():
    """Test example formatting"""
    print("=" * 60)
    print("TEST 5: Formatage des Exemples")
    print("=" * 60)
    
    service = FewShotLearningService()
    
    examples = service.get_examples('qa', domain='sciences', max_examples=1)
    if examples:
        formatted = service.format_examples_for_prompt(examples, 'qa')
        print("✅ Formatage QA:")
        print(formatted[:200] + "..." if len(formatted) > 200 else formatted)
        print()
    
    examples = service.get_examples('reformulation', style='academic', domain='sciences', max_examples=1)
    if examples:
        formatted = service.format_examples_for_prompt(examples, 'reformulation')
        print("✅ Formatage Reformulation:")
        print(formatted[:200] + "..." if len(formatted) > 200 else formatted)
        print()

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("TESTS DU SYSTÈME FEW-SHOT LEARNING")
    print("=" * 60 + "\n")
    
    try:
        test_domain_detection()
        test_example_loading()
        test_prompt_generation()
        test_example_addition()
        test_example_formatting()
        
        print("=" * 60)
        print("✅ TOUS LES TESTS TERMINÉS")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

