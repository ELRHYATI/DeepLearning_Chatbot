"""
Test avec des cas d'usage réels
Simule des requêtes utilisateur réelles pour tester le few-shot learning
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.few_shot_service import FewShotLearningService

# Try to import services (may fail if transformers not installed)
try:
    from app.services.qa_service import QAService
    QA_AVAILABLE = True
except ImportError:
    QA_AVAILABLE = False

try:
    from app.services.reformulation_service import ReformulationService
    REFORM_AVAILABLE = True
except ImportError:
    REFORM_AVAILABLE = False

try:
    from app.services.summarization_service import SummarizationService
    SUMMARY_AVAILABLE = True
except ImportError:
    SUMMARY_AVAILABLE = False

try:
    from app.services.plan_service import PlanService
    PLAN_AVAILABLE = True
except ImportError:
    PLAN_AVAILABLE = False

def print_section(title):
    """Print a formatted section title"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_qa_real_cases():
    """Test QA service with real questions"""
    print_section("TEST 1: Questions-Réponses - Cas Réels")
    
    if not QA_AVAILABLE:
        print("⚠️  Service QA non disponible (transformers non installé)")
        print("   Test des prompts uniquement\n")
        qa_service = None
    else:
        qa_service = QAService()
    
    real_questions = [
        {
            'question': "Qu'est-ce que la photosynthèse et comment fonctionne-t-elle?",
            'domain': 'sciences',
            'expected_keywords': ['plante', 'lumière', 'énergie', 'CO2', 'oxygène']
        },
        {
            'question': "Expliquez le romantisme en littérature française du 19e siècle.",
            'domain': 'littérature',
            'expected_keywords': ['mouvement', 'sentiment', 'émotion', '19e siècle']
        },
        {
            'question': "Quelles sont les causes principales de la révolution française de 1789?",
            'domain': 'histoire',
            'expected_keywords': ['1789', 'causes', 'révolution', 'française']
        },
        {
            'question': "Qu'est-ce que l'éthique en philosophie et comment se distingue-t-elle de la morale?",
            'domain': 'philosophie',
            'expected_keywords': ['éthique', 'morale', 'philosophie', 'distinction']
        },
        {
            'question': "Comment fonctionne le marché économique et quels sont les mécanismes de l'offre et de la demande?",
            'domain': 'économie',
            'expected_keywords': ['marché', 'offre', 'demande', 'prix', 'équilibre']
        }
    ]
    
    for i, case in enumerate(real_questions, 1):
        print(f"\n📝 Question {i}: {case['question']}")
        print(f"   Domaine attendu: {case['domain']}")
        
        # Detect domain
        few_shot = FewShotLearningService()
        detected_domain = few_shot.detect_domain(case['question'])
        print(f"   Domaine détecté: {detected_domain}")
        
        # Get examples that would be used
        examples = few_shot.get_examples('qa', domain=detected_domain, max_examples=2)
        print(f"   Exemples chargés: {len(examples)}")
        
        # Show prompt preview
        prompt = few_shot.build_enhanced_prompt(
            text=case['question'],
            task_type='qa',
            domain=detected_domain,
            include_examples=True
        )
        print(f"   Longueur du prompt: {len(prompt)} caractères")
        print(f"   Contient des exemples: {'Exemples' in prompt}")
        
        # Try to get answer (if model is available)
        if qa_service:
            try:
                result = qa_service.answer_question(case['question'])
                if result.get('answer'):
                    answer = result['answer']
                    print(f"   ✅ Réponse générée ({len(answer)} caractères)")
                    
                    # Check if answer contains expected keywords
                    answer_lower = answer.lower()
                    found_keywords = [kw for kw in case['expected_keywords'] if kw.lower() in answer_lower]
                    print(f"   Mots-clés trouvés: {found_keywords} / {len(case['expected_keywords'])}")
                else:
                    print(f"   ⚠️  Modèle non chargé")
            except Exception as e:
                print(f"   ⚠️  Erreur: {str(e)[:100]}")
        else:
            print(f"   ℹ️  Prompt prêt pour génération (modèle non chargé)")

def test_reformulation_real_cases():
    """Test reformulation service with real texts"""
    print_section("TEST 2: Reformulation - Cas Réels")
    
    if not REFORM_AVAILABLE:
        print("⚠️  Service Reformulation non disponible (transformers non installé)")
        print("   Test des prompts uniquement\n")
        reform_service = None
    else:
        reform_service = ReformulationService()
    
    real_texts = [
        {
            'text': "Les chercheurs ont trouvé quelque chose d'important dans leur étude. Ils ont fait des tests et ça marche bien.",
            'style': 'academic',
            'domain': 'sciences',
            'expected_improvements': ['identifié', 'résultats', 'significatifs', 'expérimentations', 'démontré']
        },
        {
            'text': "L'auteur parle de l'amour dans son livre. Le personnage principal est triste et il y a beaucoup d'émotions.",
            'style': 'academic',
            'domain': 'littérature',
            'expected_improvements': ['explore', 'thématique', 'protagoniste', 'mélancolie', 'émotions']
        },
        {
            'text': "L'intelligence artificielle transforme notre société. C'est une technologie qui change beaucoup de choses.",
            'style': 'paraphrase',
            'domain': 'informatique',
            'expected_improvements': ['révolutionne', 'structures', 'contemporaines', 'technologie', 'transformation']
        }
    ]
    
    for i, case in enumerate(real_texts, 1):
        print(f"\n📝 Texte {i}: {case['text'][:80]}...")
        print(f"   Style: {case['style']}, Domaine: {case['domain']}")
        
        # Detect domain
        few_shot = FewShotLearningService()
        detected_domain = few_shot.detect_domain(case['text'])
        print(f"   Domaine détecté: {detected_domain}")
        
        # Get examples
        examples = few_shot.get_examples('reformulation', domain=detected_domain, style=case['style'], max_examples=2)
        print(f"   Exemples chargés: {len(examples)}")
        
        # Show prompt preview
        prompt = few_shot.build_enhanced_prompt(
            text=case['text'],
            task_type='reformulation',
            style=case['style'],
            domain=detected_domain,
            include_examples=True
        )
        print(f"   Longueur du prompt: {len(prompt)} caractères")
        print(f"   Contient des exemples: {'Exemples' in prompt}")
        
        # Try to reformulate (if model is available)
        if reform_service:
            try:
                result = reform_service.reformulate_text(case['text'], style=case['style'])
                if result.get('reformulated_text'):
                    reformulated = result['reformulated_text']
                    print(f"   ✅ Texte reformulé ({len(reformulated)} caractères)")
                    
                    # Check improvements
                    reformulated_lower = reformulated.lower()
                    found_improvements = [kw for kw in case['expected_improvements'] if kw.lower() in reformulated_lower]
                    print(f"   Améliorations trouvées: {found_improvements} / {len(case['expected_improvements'])}")
                    
                    # Show similarity
                    similarity = result.get('changes', {}).get('similarity_estimate', 0)
                    print(f"   Similarité estimée: {similarity:.2%}")
                else:
                    print(f"   ⚠️  Modèle non chargé")
            except Exception as e:
                print(f"   ⚠️  Erreur: {str(e)[:100]}")
        else:
            print(f"   ℹ️  Prompt prêt pour génération (modèle non chargé)")

def test_summarization_real_cases():
    """Test summarization service with real texts"""
    print_section("TEST 3: Résumé - Cas Réels")
    
    if not SUMMARY_AVAILABLE:
        print("⚠️  Service Summarization non disponible (transformers non installé)")
        print("   Test des prompts uniquement\n")
        summary_service = None
    else:
        summary_service = SummarizationService()
    
    real_texts = [
        {
            'text': """La photosynthèse est un processus biologique fondamental par lequel les plantes, les algues et certaines bactéries convertissent l'énergie lumineuse en énergie chimique utilisable. Ce processus complexe utilise le dioxyde de carbone (CO2) présent dans l'atmosphère et l'eau (H2O) absorbée par les racines pour produire du glucose (C6H12O6), une molécule énergétique, et de l'oxygène (O2) comme sous-produit. La photosynthèse se déroule principalement dans les chloroplastes des cellules végétales, organites contenant la chlorophylle, le pigment vert qui capture l'énergie lumineuse. Ce processus est essentiel à la vie sur Terre car il constitue la base de la chaîne alimentaire et produit l'oxygène que nous respirons.""",
            'domain': 'sciences',
            'expected_key_points': ['photosynthèse', 'plantes', 'énergie', 'CO2', 'oxygène']
        },
        {
            'text': """Le romantisme est un mouvement littéraire et artistique qui émerge en Europe à la fin du 18e siècle et domine le 19e siècle. Il privilégie l'expression des sentiments, l'individualité, l'imagination, et la nature. Les romantiques rejettent le rationalisme des Lumières et valorisent l'émotion, le mystère, et le sublime. En France, les principaux représentants du romantisme incluent Victor Hugo, Alphonse de Lamartine, et Alfred de Musset. Le mouvement influence profondément la poésie, le roman, et le théâtre de l'époque.""",
            'domain': 'littérature',
            'expected_key_points': ['romantisme', 'mouvement', '19e siècle', 'sentiments', 'Victor Hugo']
        }
    ]
    
    for i, case in enumerate(real_texts, 1):
        print(f"\n📝 Texte {i} ({len(case['text'])} caractères)")
        print(f"   Domaine: {case['domain']}")
        
        # Detect domain
        few_shot = FewShotLearningService()
        detected_domain = few_shot.detect_domain(case['text'])
        print(f"   Domaine détecté: {detected_domain}")
        
        # Get examples
        examples = few_shot.get_examples('summarization', domain=detected_domain, max_examples=1)
        print(f"   Exemples chargés: {len(examples)}")
        
        # Try to summarize (if model is available)
        if summary_service:
            try:
                result = summary_service.summarize_text(case['text'], length_style='medium')
                if result.get('summary'):
                    summary = result['summary']
                    print(f"   ✅ Résumé généré ({len(summary)} caractères)")
                    print(f"   Ratio de compression: {result.get('compression_ratio', 0):.2%}")
                    
                    # Check key points
                    summary_lower = summary.lower()
                    found_points = [kw for kw in case['expected_key_points'] if kw.lower() in summary_lower]
                    print(f"   Points clés conservés: {found_points} / {len(case['expected_key_points'])}")
                else:
                    print(f"   ⚠️  Modèle non chargé")
            except Exception as e:
                print(f"   ⚠️  Erreur: {str(e)[:100]}")
        else:
            print(f"   ℹ️  Prompt prêt pour génération (modèle non chargé)")

def test_plan_real_cases():
    """Test plan service with real topics"""
    print_section("TEST 4: Plan - Cas Réels")
    
    if not PLAN_AVAILABLE:
        print("⚠️  Service Plan non disponible (transformers non installé)")
        print("   Test des prompts uniquement\n")
        plan_service = None
    else:
        plan_service = PlanService()
    
    real_topics = [
        {
            'topic': "L'impact de l'intelligence artificielle sur l'éducation moderne",
            'plan_type': 'academic',
            'domain': 'informatique',
            'expected_sections': ['Introduction', 'Développement', 'Conclusion']
        },
        {
            'topic': "Analysez les causes et conséquences de la révolution française de 1789",
            'plan_type': 'analytical',
            'domain': 'histoire',
            'expected_sections': ['Introduction', 'Analyse', 'Conclusion']
        },
        {
            'topic': "Faut-il interdire les réseaux sociaux aux mineurs?",
            'plan_type': 'argumentative',
            'domain': 'sociologie',
            'expected_sections': ['Introduction', 'Arguments pour', 'Arguments contre', 'Conclusion']
        }
    ]
    
    for i, case in enumerate(real_topics, 1):
        print(f"\n📝 Sujet {i}: {case['topic']}")
        print(f"   Type: {case['plan_type']}, Domaine: {case['domain']}")
        
        # Detect domain
        few_shot = FewShotLearningService()
        detected_domain = few_shot.detect_domain(case['topic'])
        print(f"   Domaine détecté: {detected_domain}")
        
        # Get examples
        examples = few_shot.get_examples('plan', domain=detected_domain, style=case['plan_type'], max_examples=1)
        print(f"   Exemples chargés: {len(examples)}")
        
        # Show prompt preview
        prompt = few_shot.build_enhanced_prompt(
            text=case['topic'],
            task_type='plan',
            style=case['plan_type'],
            domain=detected_domain,
            include_examples=True
        )
        print(f"   Longueur du prompt: {len(prompt)} caractères")
        print(f"   Contient des exemples: {'Exemples' in prompt}")
        
        # Try to generate plan (if model is available)
        if plan_service:
            try:
                result = plan_service.generate_plan(case['topic'], plan_type=case['plan_type'])
                if result.get('sections'):
                    sections = result['sections']
                    print(f"   ✅ Plan généré avec {len(sections)} sections principales")
                    
                    # Check expected sections
                    found_sections = [sec for sec in case['expected_sections'] if sec.lower() in str(sections).lower()]
                    print(f"   Sections trouvées: {found_sections} / {len(case['expected_sections'])}")
                elif result.get('full_plan'):
                    print(f"   ✅ Plan généré ({len(result['full_plan'])} caractères)")
                else:
                    print(f"   ⚠️  Modèle non chargé")
            except Exception as e:
                print(f"   ⚠️  Erreur: {str(e)[:100]}")
        else:
            print(f"   ℹ️  Prompt prêt pour génération (modèle non chargé)")

def test_few_shot_impact():
    """Compare prompts with and without few-shot examples"""
    print_section("TEST 5: Impact du Few-Shot Learning")
    
    few_shot = FewShotLearningService()
    
    test_cases = [
        {
            'text': "Qu'est-ce que la photosynthèse?",
            'task_type': 'qa',
            'domain': 'sciences'
        },
        {
            'text': "Les chercheurs ont trouvé quelque chose d'important.",
            'task_type': 'reformulation',
            'style': 'academic',
            'domain': 'sciences'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Cas {i}: {case['text']}")
        
        # Prompt without examples
        prompt_without = few_shot.build_enhanced_prompt(
            text=case['text'],
            task_type=case['task_type'],
            style=case.get('style'),
            domain=case.get('domain'),
            include_examples=False
        )
        
        # Prompt with examples
        prompt_with = few_shot.build_enhanced_prompt(
            text=case['text'],
            task_type=case['task_type'],
            style=case.get('style'),
            domain=case.get('domain'),
            include_examples=True
        )
        
        print(f"   Sans exemples: {len(prompt_without)} caractères")
        print(f"   Avec exemples: {len(prompt_with)} caractères")
        print(f"   Différence: +{len(prompt_with) - len(prompt_without)} caractères (+{((len(prompt_with) - len(prompt_without)) / len(prompt_without) * 100):.1f}%)")
        print(f"   Exemples ajoutés: {'Exemples' in prompt_with and 'Exemples' not in prompt_without}")

def main():
    """Run all real-world tests"""
    print("\n" + "=" * 70)
    print("  TESTS AVEC CAS D'USAGE RÉELS - FEW-SHOT LEARNING")
    print("=" * 70)
    
    try:
        test_qa_real_cases()
        test_reformulation_real_cases()
        test_summarization_real_cases()
        test_plan_real_cases()
        test_few_shot_impact()
        
        print("\n" + "=" * 70)
        print("  ✅ TOUS LES TESTS TERMINÉS")
        print("=" * 70)
        print("\n💡 Note: Si les modèles ne sont pas chargés, seuls les prompts")
        print("   sont testés. Les réponses réelles nécessitent les modèles HuggingFace.")
        print()
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

