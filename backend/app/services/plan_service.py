"""
Service for generating essay plans and structures
Helps students organize their academic writing
"""
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch
from typing import Dict, Optional, List
import os
import re
from app.services.few_shot_service import FewShotLearningService

class PlanService:
    """Service for generating academic essay plans"""
    
    def __init__(self):
        # Use BART for better text generation
        self.model_name = "moussaKam/barthez-orangesum-abstract"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.plan_pipeline = None
        self.few_shot_service = FewShotLearningService()  # Few-shot learning service
        self.use_few_shot = True  # Enable few-shot learning
        self._load_model()
    
    def _load_model(self):
        """Lazy load the model on first use"""
        if self.plan_pipeline is not None:
            return
        
        try:
            print(f"Loading plan generation model: {self.model_name}")
            from transformers import pipeline
            self.plan_pipeline = pipeline(
                "text2text-generation",
                model=self.model_name,
                device=0 if self.device == "cuda" else -1
            )
            print("Plan generation model loaded successfully")
        except Exception as e:
            print(f"Error loading plan model: {e}")
            self.plan_pipeline = None
    
    def generate_plan(
        self,
        topic: str,
        plan_type: str = "academic",  # "academic", "argumentative", "analytical", "comparative"
        structure: str = "classic"  # "classic", "thematic", "chronological", "problem-solution"
    ) -> Dict:
        """
        Generate an academic essay plan
        
        Args:
            topic: The essay topic or question
            plan_type: Type of essay plan
            structure: Structure style
        
        Returns:
            Dictionary with plan structure
        """
        if not topic or len(topic.strip()) < 10:
            return {
                "error": "Topic too short. Please provide a more detailed topic or question."
            }
        
        if self.plan_pipeline is None:
            self._load_model()
        
        if self.plan_pipeline is None:
            return {
                "error": "Plan generation model not available"
            }
        
        try:
            # Use few-shot learning service for dynamic examples
            if self.use_few_shot:
                # Detect domain
                domain = self.few_shot_service.detect_domain(topic)
                # Build enhanced prompt with adaptive examples
                prompt = self.few_shot_service.build_enhanced_prompt(
                    text=topic,
                    task_type='plan',
                    style=plan_type,
                    domain=domain,
                    include_examples=True
                )
            else:
                # Fallback to static prompt
                prompt = self._create_plan_prompt(topic, plan_type, structure)
            
            # Generate plan structure
            result = self.plan_pipeline(
                prompt,
                max_length=800,
                min_length=200,
                do_sample=True,
                num_beams=5,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.3
            )
            
            generated_text = result[0]["generated_text"] if result else ""
            
            # Parse and structure the plan
            plan = self._parse_plan(generated_text, topic, plan_type, structure)
            
            return plan
        except Exception as e:
            print(f"Error generating plan: {e}")
            return {
                "error": f"Error generating plan: {str(e)}",
                "topic": topic
            }
    
    def _create_plan_prompt(self, topic: str, plan_type: str, structure: str) -> str:
        """Create a prompt with few-shot examples for plan generation"""
        
        if plan_type == "academic":
            examples = """
Exemple de plan académique:

Sujet: "L'impact de l'intelligence artificielle sur l'éducation"

Plan:
I. Introduction
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
   B. Ouverture (réflexion sur l'avenir)
"""
        elif plan_type == "argumentative":
            examples = """
Exemple de plan argumentatif:

Sujet: "Faut-il interdire les réseaux sociaux aux mineurs?"

Plan:
I. Introduction
   A. Contexte (omniprésence des réseaux sociaux)
   B. Problématique
   C. Thèse (position)

II. Arguments pour
   A. Protection des mineurs
   B. Prévention des risques

III. Arguments contre
   A. Éducation et responsabilisation
   B. Liberté d'expression

IV. Conclusion
   A. Synthèse
   B. Position finale
"""
        elif plan_type == "analytical":
            examples = """
Exemple de plan analytique:

Sujet: "Analysez les causes de la révolution française"

Plan:
I. Introduction
   A. Contexte historique
   B. Problématique

II. Analyse des causes
   A. Causes économiques
   B. Causes sociales
   C. Causes politiques

III. Conclusion
   A. Synthèse
   B. Conséquences
"""
        else:  # comparative
            examples = """
Exemple de plan comparatif:

Sujet: "Comparez la démocratie athénienne et la démocratie moderne"

Plan:
I. Introduction
   A. Contexte
   B. Problématique

II. Points communs
   A. Participation citoyenne
   B. Principes fondamentaux

III. Différences
   A. Structure institutionnelle
   B. Échelle et portée

IV. Conclusion
   A. Synthèse comparative
   B. Enseignements
"""
        
        structure_instructions = {
            "classic": "Structure classique: Introduction, Développement (2-3 parties), Conclusion",
            "thematic": "Structure thématique: Organiser par thèmes ou concepts",
            "chronological": "Structure chronologique: Organiser par périodes temporelles",
            "problem-solution": "Structure problème-solution: Problème, Causes, Solutions"
        }
        
        prompt = f"""Génère un plan détaillé pour un essai académique en français.

{examples}

Sujet: {topic}
Type de plan: {plan_type}
Structure: {structure_instructions.get(structure, structure_instructions['classic'])}

Génère un plan structuré avec:
- Introduction (accroche, problématique, annonce du plan)
- Développement (2-3 parties principales avec sous-parties)
- Conclusion (synthèse, ouverture)

Plan:"""
        
        return prompt
    
    def _parse_plan(self, generated_text: str, topic: str, plan_type: str, structure: str) -> Dict:
        """Parse and structure the generated plan"""
        
        # Clean the generated text
        plan_text = generated_text.strip()
        
        # Remove prompt artifacts
        plan_text = re.sub(r'^(Plan|Plan:|Plan détaillé)[:：]\s*', '', plan_text, flags=re.IGNORECASE)
        
        # Extract sections
        sections = {
            "introduction": [],
            "development": [],
            "conclusion": []
        }
        
        current_section = None
        lines = plan_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if re.match(r'^I+\.?\s+(Introduction|INTRODUCTION)', line, re.IGNORECASE):
                current_section = "introduction"
            elif re.match(r'^I+\.?\s+(Développement|DÉVELOPPEMENT|Développement|Corps)', line, re.IGNORECASE):
                current_section = "development"
            elif re.match(r'^I+\.?\s+(Conclusion|CONCLUSION)', line, re.IGNORECASE):
                current_section = "conclusion"
            elif current_section and (line.startswith(('A.', 'B.', 'C.', '1.', '2.', '3.', '-', '•')) or 
                                      re.match(r'^[A-Z]\.', line)):
                sections[current_section].append(line)
        
        # If parsing failed, use the raw text
        if not any(sections.values()):
            # Split by major sections
            parts = re.split(r'(?=I+\.?\s+(?:Introduction|Développement|Conclusion))', plan_text, flags=re.IGNORECASE)
            if len(parts) >= 2:
                sections["introduction"] = [parts[1] if len(parts) > 1 else ""]
            if len(parts) >= 3:
                sections["development"] = [parts[2] if len(parts) > 2 else ""]
            if len(parts) >= 4:
                sections["conclusion"] = [parts[3] if len(parts) > 3 else ""]
        
        # If still empty, use the full text
        if not any(sections.values()):
            sections["introduction"] = [plan_text[:len(plan_text)//3]]
            sections["development"] = [plan_text[len(plan_text)//3:2*len(plan_text)//3]]
            sections["conclusion"] = [plan_text[2*len(plan_text)//3:]]
        
        return {
            "topic": topic,
            "plan_type": plan_type,
            "structure": structure,
            "sections": sections,
            "full_plan": plan_text,
            "word_count": len(plan_text.split())
        }
    
    def enhance_plan_with_details(self, plan: Dict, detail_level: str = "medium") -> Dict:
        """
        Enhance a plan with more details
        
        Args:
            plan: The basic plan structure
            detail_level: "basic", "medium", "detailed"
        """
        if detail_level == "basic":
            return plan
        
        # Add more structure and details
        enhanced_sections = {}
        for section_name, section_content in plan["sections"].items():
            enhanced_sections[section_name] = []
            for item in section_content:
                # Add sub-items if detail level is high
                if detail_level == "detailed":
                    enhanced_sections[section_name].append(f"{item}\n   - Point à développer\n   - Exemple à citer")
                else:
                    enhanced_sections[section_name].append(item)
        
        plan["sections"] = enhanced_sections
        plan["detail_level"] = detail_level
        
        return plan

