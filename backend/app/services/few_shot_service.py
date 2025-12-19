"""
Service for dynamic few-shot learning with adaptive examples
Provides domain-specific examples for better model performance
"""
from typing import Dict, List, Optional, Tuple
import re
from collections import defaultdict
import json
import os
from app.utils.logger import get_logger

logger = get_logger()


class FewShotLearningService:
    """Service for dynamic few-shot learning with adaptive examples"""
    
    def __init__(self):
        self.examples_db = defaultdict(list)
        self.domain_keywords = self._initialize_domain_keywords()
        self._load_examples()
    
    def _initialize_domain_keywords(self) -> Dict[str, List[str]]:
        """Initialize domain-specific keywords for detection"""
        return {
            'sciences': [
                'physique', 'chimie', 'biologie', 'mathématique', 'expérience',
                'expérimentation', 'hypothèse', 'théorie', 'loi', 'formule',
                'molécule', 'atome', 'réaction', 'équation', 'calcul',
                'photosynthèse', 'respiration', 'cellule', 'adn', 'génétique',
                'quantique', 'relativité', 'énergie', 'force', 'mouvement',
                'scientifique', 'science', 'laboratoire', 'expérimental',
                'biologique', 'physique', 'chimique', 'mathématique'
            ],
            'littérature': [
                'roman', 'poésie', 'auteur', 'œuvre', 'littéraire', 'écrivain',
                'personnage', 'narrateur', 'récit', 'fiction', 'prose',
                'vers', 'strophe', 'métaphore', 'allégorie', 'symbolisme',
                'romantisme', 'réalisme', 'naturalisme', 'surréalisme'
            ],
            'histoire': [
                'historique', 'événement', 'guerre', 'révolution', 'civilisation',
                'empire', 'roi', 'reine', 'monarchie', 'république',
                'moyen âge', 'renaissance', 'antiquité', 'contemporain',
                'bataille', 'traité', 'alliance', 'conquête', 'décolonisation',
                'histoire', 'historien', 'période', 'époque', 'chronologie',
                'causes', 'conséquences', 'événement historique'
            ],
            'philosophie': [
                'philosophique', 'éthique', 'morale', 'pensée', 'existence',
                'philosophe', 'doctrine', 'théorie', 'concept', 'notion',
                'raison', 'conscience', 'liberté', 'justice', 'vérité',
                'métaphysique', 'épistémologie', 'logique', 'esthétique',
                'philosophie', 'philosopher', 'réflexion', 'questionnement'
            ],
            'économie': [
                'économique', 'marché', 'prix', 'production', 'capitalisme',
                'consommation', 'offre', 'demande', 'inflation', 'croissance',
                'pib', 'chômage', 'investissement', 'commerce', 'finance',
                'monnaie', 'banque', 'bourse', 'crise', 'récession'
            ],
            'informatique': [
                'programmation', 'algorithme', 'logiciel', 'système', 'données',
                'intelligence artificielle', 'ia', 'machine learning', 'réseau',
                'base de données', 'sécurité', 'cyber', 'développement',
                'code', 'application', 'interface', 'serveur', 'client',
                'informatique', 'informatique', 'ordinateur', 'technologie',
                'apprentissage automatique', 'deep learning', 'neural'
            ],
            'psychologie': [
                'psychologie', 'psychologique', 'comportement', 'mental',
                'cognitif', 'émotion', 'psychologue', 'thérapie', 'conscience',
                'inconscient', 'personnalité', 'développement', 'apprentissage',
                'mémoire', 'perception', 'intelligence', 'stress', 'anxiété'
            ],
            'géographie': [
                'géographie', 'géographique', 'pays', 'continent', 'climat',
                'population', 'territoire', 'relief', 'montagne', 'fleuve',
                'océan', 'ville', 'région', 'frontière', 'culture', 'langue',
                'géographe', 'géographique', 'décrire', 'décrivez', 'climatique'
            ],
            'sociologie': [
                'sociologie', 'société', 'social', 'groupe', 'communauté',
                'culture', 'norme', 'valeur', 'institution', 'organisation',
                'classe', 'stratification', 'mobilité', 'identité', 'intégration'
            ]
        }
    
    def _load_examples(self):
        """Load examples from file or initialize with defaults"""
        examples_file = os.path.join(
            os.path.dirname(__file__),
            'few_shot_examples.json'
        )
        
        if os.path.exists(examples_file):
            try:
                with open(examples_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.examples_db = defaultdict(list, data)
                logger.info(f"Loaded {sum(len(v) for v in self.examples_db.values())} few-shot examples")
            except Exception as e:
                logger.warning(f"Could not load examples file: {e}")
                self._initialize_default_examples()
        else:
            self._initialize_default_examples()
            self._save_examples()
    
    def _save_examples(self):
        """Save examples to file"""
        examples_file = os.path.join(
            os.path.dirname(__file__),
            'few_shot_examples.json'
        )
        
        try:
            with open(examples_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.examples_db), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Could not save examples file: {e}")
    
    def _initialize_default_examples(self):
        """Initialize with default examples for each task type"""
        
        # QA Examples
        self.examples_db['qa_sciences'] = [
            {
                'question': "Qu'est-ce que la photosynthèse?",
                'context': "La photosynthèse est le processus par lequel les plantes convertissent la lumière en énergie.",
                'answer': "La photosynthèse est un processus biologique fondamental par lequel les plantes, les algues et certaines bactéries convertissent l'énergie lumineuse en énergie chimique utilisable. Ce processus utilise le dioxyde de carbone (CO2) et l'eau (H2O) pour produire du glucose (C6H12O6) et de l'oxygène (O2) comme sous-produit."
            },
            {
                'question': "Comment fonctionne la respiration cellulaire?",
                'context': "La respiration cellulaire produit de l'ATP à partir du glucose.",
                'answer': "La respiration cellulaire est le processus par lequel les cellules produisent de l'énergie (ATP) à partir du glucose et d'autres molécules organiques. Elle se déroule en trois étapes principales : la glycolyse dans le cytoplasme, le cycle de Krebs dans la matrice mitochondriale, et la chaîne de transport d'électrons dans la membrane interne des mitochondries."
            }
        ]
        
        self.examples_db['qa_littérature'] = [
            {
                'question': "Qu'est-ce que le romantisme en littérature?",
                'context': "Le romantisme est un mouvement littéraire du 19e siècle.",
                'answer': "Le romantisme est un mouvement littéraire et artistique qui émerge en Europe à la fin du 18e siècle et domine le 19e siècle. Il privilégie l'expression des sentiments, l'individualité, l'imagination, et la nature. Les romantiques rejettent le rationalisme des Lumières et valorisent l'émotion, le mystère, et le sublime."
            }
        ]
        
        # Reformulation Examples
        self.examples_db['reformulation_academic_sciences'] = [
            {
                'original': "Les chercheurs ont trouvé quelque chose d'important.",
                'reformulated': "Les chercheurs ont identifié des résultats significatifs dans le cadre de cette étude."
            },
            {
                'original': "C'est une bonne idée pour améliorer les choses.",
                'reformulated': "Cette approche présente un potentiel considérable pour l'optimisation des processus."
            },
            {
                'original': "On a fait des tests et ça marche bien.",
                'reformulated': "Les expérimentations menées ont démontré l'efficacité de cette méthode."
            }
        ]
        
        self.examples_db['reformulation_academic_littérature'] = [
            {
                'original': "L'auteur parle de l'amour dans son livre.",
                'reformulated': "L'auteur explore la thématique de l'amour à travers son œuvre littéraire."
            },
            {
                'original': "Le personnage principal est triste.",
                'reformulated': "Le protagoniste manifeste une profonde mélancolie tout au long du récit."
            }
        ]
        
        self.examples_db['reformulation_paraphrase'] = [
            {
                'original': "L'intelligence artificielle transforme notre société.",
                'reformulated': "L'IA révolutionne actuellement les structures sociales contemporaines."
            },
            {
                'original': "Les étudiants doivent étudier régulièrement pour réussir.",
                'reformulated': "Pour obtenir de bons résultats, les apprenants doivent consacrer du temps à leurs études de manière constante."
            }
        ]
        
        # Summarization Examples
        self.examples_db['summarization_sciences'] = [
            {
                'original': "La photosynthèse est un processus complexe qui se déroule en plusieurs étapes. D'abord, les plantes absorbent la lumière solaire grâce à la chlorophylle. Ensuite, cette énergie est utilisée pour convertir le CO2 et l'eau en glucose. Le processus produit également de l'oxygène comme sous-produit.",
                'summary': "La photosynthèse convertit la lumière solaire en énergie chimique, transformant le CO2 et l'eau en glucose tout en libérant de l'oxygène."
            }
        ]
        
        # Plan Examples
        self.examples_db['plan_academic_sciences'] = [
            {
                'topic': "L'impact de l'intelligence artificielle sur l'éducation",
                'plan': """I. Introduction
   A. Accroche (contexte actuel de l'IA)
   B. Problématique (Comment l'IA transforme-t-elle l'éducation?)
   C. Annonce du plan

II. Développement
   A. Les applications de l'IA dans l'éducation
      1. Apprentissage personnalisé
      2. Automatisation des tâches administratives
   B. Les défis et limites
      1. Questions éthiques
      2. Inégalités d'accès
   C. Les perspectives d'avenir
      1. Évolution des méthodes pédagogiques
      2. Préparation des étudiants

III. Conclusion
   A. Synthèse des points clés
   B. Ouverture (réflexion sur l'avenir)"""
            }
        ]
    
    def detect_domain(self, text: str) -> str:
        """
        Detect the academic domain of the text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Detected domain name
        """
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if not domain_scores:
            return 'general'
        
        # Return domain with highest score
        if not domain_scores:
            return 'general'
        
        detected_domain = max(domain_scores, key=domain_scores.get)
        
        # Lower threshold to 1 match for better detection
        # But prioritize domains with multiple matches
        if domain_scores[detected_domain] >= 2:
            return detected_domain
        elif domain_scores[detected_domain] >= 1:
            # If only one match, check if it's a strong indicator
            strong_indicators = {
                'sciences': ['photosynthèse', 'respiration cellulaire', 'adn', 'atome', 'molécule'],
                'histoire': ['révolution', 'guerre', 'empire', 'monarchie'],
                'philosophie': ['éthique', 'morale', 'philosophe', 'métaphysique'],
                'informatique': ['machine learning', 'intelligence artificielle', 'ia', 'algorithme'],
                'géographie': ['climat', 'pays', 'continent', 'géographie']
            }
            
            # Check if the matched keyword is a strong indicator
            text_lower = text.lower()
            for keyword in strong_indicators.get(detected_domain, []):
                if keyword in text_lower:
                    return detected_domain
            
            # If not a strong indicator, return general for single matches
            return 'general'
        else:
            return 'general'
    
    def get_examples(
        self,
        task_type: str,
        domain: Optional[str] = None,
        style: Optional[str] = None,
        max_examples: int = 3
    ) -> List[Dict]:
        """
        Get relevant examples for a task
        
        Args:
            task_type: Type of task ('qa', 'reformulation', 'summarization', 'plan')
            domain: Domain name (optional, will be detected if not provided)
            style: Style for reformulation (optional)
            max_examples: Maximum number of examples to return
            
        Returns:
            List of example dictionaries
        """
        # Build key for examples database
        if task_type == 'qa':
            key = f'qa_{domain}' if domain else 'qa_general'
        elif task_type == 'reformulation':
            if style and domain:
                key = f'reformulation_{style}_{domain}'
            elif style:
                key = f'reformulation_{style}'
            else:
                key = 'reformulation_general'
        elif task_type == 'summarization':
            key = f'summarization_{domain}' if domain else 'summarization_general'
        elif task_type == 'plan':
            key = f'plan_{style}_{domain}' if (style and domain) else f'plan_{style}' if style else 'plan_general'
        else:
            key = f'{task_type}_general'
        
        # Get examples
        examples = self.examples_db.get(key, [])
        
        # If no domain-specific examples, try general
        if not examples and domain and domain != 'general':
            general_key = key.replace(f'_{domain}', '_general')
            examples = self.examples_db.get(general_key, [])
        
        # If still no examples, try any examples for this task type
        if not examples:
            for k, v in self.examples_db.items():
                if k.startswith(f'{task_type}_'):
                    examples.extend(v)
                    break
        
        return examples[:max_examples]
    
    def format_examples_for_prompt(
        self,
        examples: List[Dict],
        task_type: str
    ) -> str:
        """
        Format examples as a prompt string
        
        Args:
            examples: List of example dictionaries
            task_type: Type of task
            
        Returns:
            Formatted examples string
        """
        if not examples:
            return ""
        
        formatted = []
        
        if task_type == 'qa':
            formatted.append("Exemples de questions-réponses:")
            for i, ex in enumerate(examples, 1):
                formatted.append(f"\nExemple {i}:")
                formatted.append(f"Question: {ex.get('question', '')}")
                if ex.get('context'):
                    formatted.append(f"Contexte: {ex.get('context', '')}")
                formatted.append(f"Réponse: {ex.get('answer', '')}")
        
        elif task_type == 'reformulation':
            formatted.append("Exemples de reformulation:")
            for i, ex in enumerate(examples, 1):
                formatted.append(f"\nExemple {i}:")
                formatted.append(f"Original: {ex.get('original', '')}")
                formatted.append(f"Reformulé: {ex.get('reformulated', '')}")
        
        elif task_type == 'summarization':
            formatted.append("Exemples de résumé:")
            for i, ex in enumerate(examples, 1):
                formatted.append(f"\nExemple {i}:")
                formatted.append(f"Texte original: {ex.get('original', '')}")
                formatted.append(f"Résumé: {ex.get('summary', '')}")
        
        elif task_type == 'plan':
            formatted.append("Exemples de plan:")
            for i, ex in enumerate(examples, 1):
                formatted.append(f"\nExemple {i}:")
                formatted.append(f"Sujet: {ex.get('topic', '')}")
                formatted.append(f"Plan:\n{ex.get('plan', '')}")
        
        return "\n".join(formatted)
    
    def add_example(
        self,
        task_type: str,
        example: Dict,
        domain: Optional[str] = None,
        style: Optional[str] = None
    ):
        """
        Add a new example to the database
        
        Args:
            task_type: Type of task
            example: Example dictionary
            domain: Domain name (optional)
            style: Style for reformulation (optional)
        """
        # Build key
        if task_type == 'qa':
            key = f'qa_{domain}' if domain else 'qa_general'
        elif task_type == 'reformulation':
            if style and domain:
                key = f'reformulation_{style}_{domain}'
            elif style:
                key = f'reformulation_{style}'
            else:
                key = 'reformulation_general'
        elif task_type == 'summarization':
            key = f'summarization_{domain}' if domain else 'summarization_general'
        elif task_type == 'plan':
            key = f'plan_{style}_{domain}' if (style and domain) else f'plan_{style}' if style else 'plan_general'
        else:
            key = f'{task_type}_general'
        
        # Add example (limit to 10 per key to avoid bloat)
        if len(self.examples_db[key]) < 10:
            self.examples_db[key].append(example)
            self._save_examples()
            logger.info(f"Added example to {key}")
        else:
            # Replace oldest example
            self.examples_db[key].pop(0)
            self.examples_db[key].append(example)
            self._save_examples()
            logger.info(f"Replaced example in {key}")
    
    def build_enhanced_prompt(
        self,
        text: str,
        task_type: str,
        style: Optional[str] = None,
        domain: Optional[str] = None,
        include_examples: bool = True
    ) -> str:
        """
        Build an enhanced prompt with few-shot examples
        
        Args:
            text: Input text
            task_type: Type of task
            style: Style for reformulation/plan
            domain: Domain name (will be detected if not provided)
            include_examples: Whether to include examples
            
        Returns:
            Enhanced prompt string
        """
        # Detect domain if not provided
        if not domain:
            domain = self.detect_domain(text)
        
        # Get examples
        examples_text = ""
        if include_examples:
            examples = self.get_examples(task_type, domain, style, max_examples=3)
            if examples:
                examples_text = self.format_examples_for_prompt(examples, task_type)
        
        # Build prompt based on task type
        if task_type == 'qa':
            prompt = f"""Tu es un expert en {domain if domain != 'general' else 'questions-réponses académiques'}.

{examples_text}

Maintenant, réponds à cette question de manière précise et détaillée:

Question: {text}

Réponse:"""
        
        elif task_type == 'reformulation':
            style_instructions = {
                'academic': "style académique rigoureux et formel",
                'formal': "style formel et professionnel",
                'paraphrase': "paraphrase en conservant le sens exact",
                'simplification': "style simple et accessible",
                'simple': "style simple et clair"
            }
            style_desc = style_instructions.get(style, "style amélioré")
            
            prompt = f"""Tu es un expert en rédaction académique française.

{examples_text}

Tâche: Réécris ce texte dans un {style_desc}.

Règles:
- Utiliser un vocabulaire approprié au style demandé
- Structurer les phrases de manière claire
- Maintenir le sens exact du texte original
- Éviter les répétitions

Texte à réécrire:
{text}

Réécriture ({style_desc}):"""
        
        elif task_type == 'summarization':
            prompt = f"""Tu es un expert en résumé de textes académiques.

{examples_text}

Tâche: Résume ce texte de manière concise tout en conservant les informations essentielles.

Texte à résumer:
{text}

Résumé:"""
        
        elif task_type == 'plan':
            prompt = f"""Tu es un expert en structuration d'essais académiques.

{examples_text}

Tâche: Génère un plan détaillé pour un essai académique en français.

Sujet: {text}
Type de plan: {style if style else 'académique'}

Génère un plan structuré avec:
- Introduction (accroche, problématique, annonce du plan)
- Développement (2-3 parties principales avec sous-parties)
- Conclusion (synthèse, ouverture)

Plan:"""
        
        else:
            prompt = text
        
        return prompt

