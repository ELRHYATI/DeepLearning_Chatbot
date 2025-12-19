from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch
from typing import Dict, Optional
import os
from app.services.semantic_validation_service import SemanticValidationService
from app.services.few_shot_service import FewShotLearningService
from app.services.adaptive_learning_service import AdaptiveLearningService

class ReformulationService:
    def __init__(self):
        # Primary model - upgraded to better model
        self.model_name = "moussaKam/barthez-orangesum-abstract"  # BART French - better for reformulation
        # Alternative models for better quality (loaded on demand)
        self.alternative_models = [
            "plguillou/t5-base-fr-sum-cnndm",  # T5 French as fallback
        ]
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.reformulation_pipeline = None
        self.alternative_pipelines = {}  # Cache for alternative models
        self.use_ensemble = True  # Enable ensemble methods
        self.semantic_validator = SemanticValidationService()
        self.use_semantic_validation = True  # Enable semantic validation
        self.few_shot_service = FewShotLearningService()  # Few-shot learning service
        self.use_few_shot = True  # Enable few-shot learning
        self.adaptive_learning = AdaptiveLearningService()  # Adaptive learning service
        self.use_adaptive_learning = True  # Enable adaptive learning
        self._load_model()
    
    def _load_model(self):
        """Lazy load the model on first use"""
        if self.reformulation_pipeline is not None:
            return
        
        try:
            print(f"Loading reformulation model: {self.model_name}")
            # Ensure model_name is a string
            model_name_str = str(self.model_name) if self.model_name else "moussaKam/barthez-orangesum-abstract"
            
            # Check if it's a T5 model (starts with t5 or contains t5 in name)
            is_t5_model = "t5" in model_name_str.lower()
            
            if is_t5_model:
                # For T5 models, we must use slow tokenizer (SentencePiece)
                try:
                    from transformers import T5Tokenizer
                    print("Using T5Tokenizer (slow tokenizer with SentencePiece)")
                    self.tokenizer = T5Tokenizer.from_pretrained(
                        model_name_str,
                        local_files_only=False
                    )
                except ImportError as import_error:
                    print(f"T5Tokenizer import error: {import_error}")
                    print("Make sure sentencepiece is installed: pip install sentencepiece")
                    raise import_error
                except Exception as e:
                    print(f"T5Tokenizer loading error: {e}")
                    # Fallback to AutoTokenizer
                    print("Trying AutoTokenizer as fallback...")
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        model_name_str,
                        use_fast=False,
                        trust_remote_code=True,
                        local_files_only=False
                    )
            else:
                # For BART and other models, use AutoTokenizer
                print("Using AutoTokenizer (BART or other model)")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_name_str,
                    use_fast=False,
                    trust_remote_code=True,
                    local_files_only=False
                )
            
            model_name_str = str(self.model_name) if self.model_name else "moussaKam/barthez-orangesum-abstract"
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name_str,
                trust_remote_code=True,
                local_files_only=False
            )
            self.reformulation_pipeline = pipeline(
                "text2text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            print("Reformulation model loaded successfully")
        except Exception as e:
            print(f"Error loading reformulation model: {e}")
            print("Reformulation features will be limited. Models will download on first use.")
            import traceback
            traceback.print_exc()
            self.reformulation_pipeline = None
    
    def reformulate_text(self, text: str, style: str = "academic") -> Dict:
        """
        Reformulate French text while maintaining meaning.
        
        Args:
            text: Original text in French
            style: Style preference (academic, formal, simple, paraphrase, simplification)
            
        Returns:
            Dictionary with original_text, reformulated_text, and changes
        """
        # Try to load model if not loaded
        if not self.reformulation_pipeline:
            self._load_model()
        
        if not self.reformulation_pipeline:
            return {
                "original_text": text,
                "reformulated_text": text,
                "changes": {"status": "Model not available - loading in background"}
            }
        
        try:
            # Use few-shot learning service for dynamic examples
            if self.use_few_shot:
                # Detect domain
                domain = self.few_shot_service.detect_domain(text)
                # Build enhanced prompt with adaptive examples
                prompt = self.few_shot_service.build_enhanced_prompt(
                    text=text,
                    task_type='reformulation',
                    style=style,
                    domain=domain,
                    include_examples=True
                )
            else:
                # Fallback to static prompts
                if style == "academic":
                    prompt = f"""Réécris ce texte dans un style académique rigoureux et formel.

Exemples:
Original: "Les chercheurs ont trouvé quelque chose d'important."
Académique: "Les chercheurs ont identifié des résultats significatifs dans le cadre de cette étude."

Original: "C'est une bonne idée pour améliorer les choses."
Académique: "Cette approche présente un potentiel considérable pour l'optimisation des processus."

Texte à reformuler: {text}"""
                elif style == "formal":
                    prompt = f"""Réécris ce texte dans un style formel et professionnel.

Exemples:
Original: "On doit faire ça rapidement."
Formel: "Il est nécessaire d'effectuer cette tâche dans les plus brefs délais."

Original: "Je pense que c'est bien."
Formel: "Je considère que cette approche est appropriée."

Texte à reformuler: {text}"""
                elif style == "paraphrase":
                    prompt = f"""Paraphrase ce texte en conservant le sens exact mais en changeant la formulation.

Exemples:
Original: "L'intelligence artificielle transforme notre société."
Paraphrase: "L'IA révolutionne actuellement les structures sociales contemporaines."

Original: "Les étudiants doivent étudier régulièrement pour réussir."
Paraphrase: "Pour obtenir de bons résultats, les apprenants doivent consacrer du temps à leurs études de manière constante."

Texte à paraphraser: {text}"""
                elif style == "simplification":
                    prompt = f"""Simplifie ce texte pour le rendre accessible.

Exemples:
Original: "L'analyse quantitative des données révèle des corrélations significatives."
Simplifié: "En regardant les chiffres, on voit que certaines choses sont liées."

Original: "La méthodologie employée dans cette recherche est rigoureuse."
Simplifié: "La façon dont cette étude a été faite est très sérieuse."

Texte à simplifier: {text}"""
                else:  # simple (default fallback)
                    prompt = f"""Réécris ce texte de manière plus simple.

Exemples:
Original: "La complexité de cette problématique nécessite une approche méthodique."
Simple: "Ce problème est compliqué, il faut le résoudre étape par étape."

Texte à reformuler: {text}"""
            
            # Pre-process text for better quality
            cleaned_input = self._preprocess_text(text)
            
            # Generate reformulation with enhanced parameters for better quality
            text_length = len(cleaned_input.split())
            
            # Adjust parameters based on style - OPTIMIZED FOR BETTER QUALITY
            if style == "paraphrase":
                # For paraphrase: higher diversity, more variation, avoid repetition
                generation_params = {
                    "max_length": min(512, max(128, text_length * 3 + 50)),
                    "min_length": max(20, text_length // 2),
                    "num_beams": 6,  # Increased from 5 for better quality
                    "early_stopping": True,
                    "do_sample": True,
                    "temperature": 0.75,  # Slightly reduced for better coherence
                    "top_p": 0.92,  # Slightly reduced for better focus
                    "top_k": 50,  # Optimized
                    "repetition_penalty": 1.6,  # Increased for better anti-repetition
                    "length_penalty": 1.1,  # Slight increase
                    "no_repeat_ngram_size": 4,  # Avoid repeating 4-grams
                    "diversity_penalty": 0.3  # Encourage diversity
                }
            elif style == "simplification":
                # For simplification: simpler output, shorter sentences
                base_params = {
                    "max_length": min(512, max(128, text_length * 2 + 30)),  # Shorter output
                    "min_length": max(15, text_length // 3),  # Can be shorter
                    "num_beams": 5,  # Increased from 4
                    "early_stopping": True,
                    "do_sample": True,
                    "temperature": 0.65,  # Reduced for simpler, clearer output
                    "top_p": 0.88,  # More focused
                    "top_k": 35,  # Reduced for simpler vocabulary
                    "repetition_penalty": 1.3,  # Increased
                    "length_penalty": 0.75,  # Encourage shorter, simpler sentences
                    "no_repeat_ngram_size": 3  # Increased from 2
                }
                
                if self.use_adaptive_learning and user_id:
                    generation_params = self.adaptive_learning.adapt_reformulation_parameters(
                        user_id=user_id,
                        style=style,
                        default_params=base_params
                    )
                else:
                    generation_params = base_params
            elif style == "academic":
                base_params = {
                    "max_length": min(512, max(128, text_length * 3 + 50)),
                    "min_length": max(20, text_length // 2),
                    "num_beams": 8,  # Increased from 6 for better academic quality
                    "early_stopping": True,
                    "do_sample": False,  # Deterministic for academic precision
                    "temperature": 0.3,  # Lower for more precise academic language
                    "top_p": 0.90,  # More focused
                    "top_k": 40,  # More selective vocabulary
                    "repetition_penalty": 1.4,  # Increased
                    "length_penalty": 1.3,  # Increased for better structure
                    "no_repeat_ngram_size": 4  # Increased from 3
                }
                
                if self.use_adaptive_learning and user_id:
                    generation_params = self.adaptive_learning.adapt_reformulation_parameters(
                        user_id=user_id,
                        style=style,
                        default_params=base_params
                    )
                else:
                    generation_params = base_params
            else:  # formal or simple
                base_params = {
                    "max_length": min(512, max(128, text_length * 3 + 50)),
                    "min_length": max(20, text_length // 2),
                    "num_beams": 6,  # Increased from 5
                    "early_stopping": True,
                    "do_sample": True,
                    "temperature": 0.65,
                    "top_p": 0.92,
                    "top_k": 50,
                    "repetition_penalty": 1.3,
                    "length_penalty": 1.0,
                    "no_repeat_ngram_size": 3
                }
                
                if self.use_adaptive_learning and user_id:
                    generation_params = self.adaptive_learning.adapt_reformulation_parameters(
                        user_id=user_id,
                        style=style,
                        default_params=base_params
                    )
                else:
                    generation_params = base_params
            
            # Pre-process input for better results
            text = self._preprocess_text(text) if hasattr(self, '_preprocess_text') else text
            
            # Use ensemble method if enabled
            if self.use_ensemble:
                reformulated = self._ensemble_reformulate(prompt, text, style, generation_params)
            else:
                # Try generation with optimized parameters
                result = self.reformulation_pipeline(prompt, **generation_params)
                reformulated = result[0]["generated_text"] if result else text
            
            # Clean up the reformulated text - remove the prompt if it appears
            if "Réécris" in reformulated or "réécris" in reformulated:
                # Try to extract just the reformulated part
                lines = reformulated.split('\n')
                reformulated = '\n'.join([line for line in lines if not any(word in line.lower() for word in ['réécris', 'texte', 'reformuler'])])
                reformulated = reformulated.strip()
            
            # If reformulation didn't change much, try a different approach
            similarity = self._estimate_similarity(text, reformulated)
            
            # More aggressive threshold - if similarity is too high, force transformation
            if reformulated == text or (similarity > 0.85 and style != "paraphrase") or (similarity > 0.75 and style == "paraphrase"):
                # Apply style-specific transformations
                if style == "paraphrase":
                    reformulated = self._apply_paraphrase_transformations(text)
                elif style == "simplification":
                    reformulated = self._apply_simplification_transformations(text)
                else:
                    reformulated = self._apply_academic_transformations(text, style)
                
                # If still too similar after transformations, apply more aggressive changes
                new_similarity = self._estimate_similarity(text, reformulated)
                if new_similarity > 0.80:
                    # Apply additional transformations
                    reformulated = self._apply_aggressive_reformulation(text, style)
            
            # For paraphrase mode, ensure sufficient variation
            if style == "paraphrase" and similarity > 0.85:
                # Try additional paraphrase techniques
                reformulated = self._enhance_paraphrase(text, reformulated)
            
            # Semantic validation
            validation = None
            if self.use_semantic_validation:
                validation = self.semantic_validator.validate_reformulation(
                    text, reformulated, style
                )
                if not validation.get("valid", True) and not validation.get("warning", False):
                    # If validation fails (not just warning), try more aggressive reformulation
                    reformulated = self._apply_aggressive_reformulation(text, style)
                    # Re-validate
                    validation = self.semantic_validator.validate_reformulation(
                        text, reformulated, style
                    )
            
            # Calculate basic statistics
            original_words = len(text.split())
            reformulated_words = len(reformulated.split())
            
            changes = {
                "word_count_change": reformulated_words - original_words,
                "style": style,
                "similarity_estimate": self._estimate_similarity(text, reformulated)
            }
            
            result_dict = {
                "original_text": text,
                "reformulated_text": reformulated,
                "changes": changes,
                "validation": validation
            }
            
            # Record successful interaction for learning
            if self.use_adaptive_learning and user_id:
                interaction_metadata = {
                    'style': style,
                    'original_length': len(text),
                    'reformulated_length': len(reformulated),
                    'similarity': changes.get('similarity_estimate', 0),
                    'generation_params': generation_params if 'generation_params' in locals() else {}
                }
                if metadata:
                    interaction_metadata.update(metadata)
                
                # Only record if reformulation was successful (not too similar, not too different)
                similarity = changes.get('similarity_estimate', 0)
                if 0.3 <= similarity <= 0.9:
                    self.adaptive_learning.record_successful_interaction(
                        user_id=user_id,
                        task_type='reformulation',
                        metadata=interaction_metadata
                    )
            
            return result_dict
        except Exception as e:
            print(f"Error in reformulation: {e}")
            return {
                "original_text": text,
                "reformulated_text": text,
                "changes": {"error": str(e)}
            }
    
    def _estimate_similarity(self, text1: str, text2: str) -> float:
        """
        Simple similarity estimation based on common words.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _apply_academic_transformations(self, text: str, style: str) -> str:
        """
        Apply basic academic transformations when model doesn't work well.
        """
        if style != "academic":
            return text
        
        # Basic academic vocabulary replacements
        replacements = {
            "très": "considérablement",
            "beaucoup": "substantiellement",
            "important": "significatif",
            "montrer": "démontrer",
            "dire": "affirmer",
            "penser": "considérer",
            "faire": "effectuer",
            "voir": "observer",
            "trouver": "identifier",
            "utiliser": "employer",
            "donner": "fournir",
            "mettre": "placer",
            "prendre": "adopter"
        }
        
        result = text
        for casual, formal in replacements.items():
            # Replace whole words only
            import re
            result = re.sub(r'\b' + casual + r'\b', formal, result, flags=re.IGNORECASE)
        
        # Capitalize first letter
        if result and not result[0].isupper():
            result = result[0].upper() + result[1:]
        
        return result
    
    def _apply_paraphrase_transformations(self, text: str) -> str:
        """
        Apply paraphrase-specific transformations to avoid plagiarism.
        """
        import re
        
        # Synonym replacements for common words
        paraphrase_replacements = {
            # Verbs
            "montrer": "démontrer",
            "indiquer": "révéler",
            "expliquer": "élucider",
            "analyser": "examiner",
            "étudier": "investiguer",
            "trouver": "identifier",
            "utiliser": "employer",
            "faire": "effectuer",
            "donner": "fournir",
            "prendre": "adopter",
            "mettre": "placer",
            "voir": "observer",
            "dire": "affirmer",
            "penser": "considérer",
            
            # Nouns
            "résultat": "conclusion",
            "étude": "recherche",
            "problème": "difficulté",
            "solution": "réponse",
            "méthode": "approche",
            "données": "informations",
            
            # Adjectives
            "important": "significatif",
            "grand": "considérable",
            "petit": "réduit",
            "bon": "efficace",
            "mauvais": "défavorable",
            
            # Adverbs
            "très": "considérablement",
            "beaucoup": "substantiellement",
            "souvent": "fréquemment",
            "toujours": "systématiquement",
            "jamais": "en aucun cas"
        }
        
        result = text
        for original, replacement in paraphrase_replacements.items():
            # Replace whole words only, case-insensitive
            pattern = r'\b' + re.escape(original) + r'\b'
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Restructure sentences: change active to passive and vice versa where possible
        # Simple pattern: "X fait Y" -> "Y est fait par X"
        passive_pattern = r'(\w+)\s+(fait|effectue|réalise)\s+(\w+)'
        def to_passive(match):
            subject = match.group(1)
            verb = match.group(2)
            object_ = match.group(3)
            verb_map = {"fait": "est fait", "effectue": "est effectué", "réalise": "est réalisé"}
            return f"{object_} {verb_map.get(verb, 'est fait')} par {subject}"
        
        # Only apply to a few sentences to avoid over-transformation
        sentences = result.split('.')
        transformed_sentences = []
        for i, sentence in enumerate(sentences):
            if i % 2 == 0 and len(sentence) > 20:  # Transform every other sentence
                sentence = re.sub(passive_pattern, to_passive, sentence, count=1)
            transformed_sentences.append(sentence)
        result = '.'.join(transformed_sentences)
        
        # Capitalize first letter
        if result and not result[0].isupper():
            result = result[0].upper() + result[1:]
        
        return result
    
    def _apply_simplification_transformations(self, text: str) -> str:
        """
        Apply simplification transformations to make text more accessible.
        """
        import re
        
        # Replace complex words with simpler alternatives
        simplification_replacements = {
            # Complex -> Simple
            "considérablement": "beaucoup",
            "substantiellement": "beaucoup",
            "significatif": "important",
            "démontrer": "montrer",
            "élucider": "expliquer",
            "investiguer": "étudier",
            "identifier": "trouver",
            "employer": "utiliser",
            "effectuer": "faire",
            "fournir": "donner",
            "adopter": "prendre",
            "observer": "voir",
            "affirmer": "dire",
            "considérer": "penser",
            "conclusion": "résultat",
            "recherche": "étude",
            "difficulté": "problème",
            "réponse": "solution",
            "approche": "méthode",
            "informations": "données",
            "efficace": "bon",
            "défavorable": "mauvais",
            "fréquemment": "souvent",
            "systématiquement": "toujours"
        }
        
        result = text
        for complex_word, simple_word in simplification_replacements.items():
            pattern = r'\b' + re.escape(complex_word) + r'\b'
            result = re.sub(pattern, simple_word, result, flags=re.IGNORECASE)
        
        # Break long sentences into shorter ones
        # Split on conjunctions and relative pronouns
        split_patterns = [r'\s+et\s+', r'\s+mais\s+', r'\s+qui\s+', r'\s+que\s+', r'\s+où\s+']
        for pattern in split_patterns:
            # Only split if sentence is very long (>100 chars)
            sentences = result.split('.')
            new_sentences = []
            for sentence in sentences:
                if len(sentence) > 100:
                    parts = re.split(pattern, sentence, maxsplit=1)
                    if len(parts) > 1:
                        new_sentences.append(parts[0].strip() + '.')
                        new_sentences.append(parts[1].strip() + '.')
                    else:
                        new_sentences.append(sentence)
                else:
                    new_sentences.append(sentence)
            result = '. '.join(new_sentences)
        
        # Capitalize first letter
        if result and not result[0].isupper():
            result = result[0].upper() + result[1:]
        
        return result
    
    def _enhance_paraphrase(self, original: str, current: str) -> str:
        """
        Enhance paraphrase to ensure sufficient variation from original.
        """
        # If similarity is still too high, apply additional transformations
        if self._estimate_similarity(original, current) > 0.85:
            # Try reordering clauses
            import re
            
            # Split into clauses
            clauses = re.split(r'[,;]\s+', original)
            if len(clauses) > 1:
                # Reorder clauses
                reordered = clauses[1:] + [clauses[0]]
                enhanced = ', '.join(reordered)
                
                # Apply synonym replacements
                enhanced = self._apply_paraphrase_transformations(enhanced)
                
                if self._estimate_similarity(original, enhanced) < 0.85:
                    return enhanced
        
        return current
    
    def _apply_aggressive_reformulation(self, text: str, style: str) -> str:
        """
        Apply more aggressive reformulation when basic methods don't work
        """
        import re
        
        # More comprehensive synonym replacements
        aggressive_replacements = {
            "intelligence artificielle": "système d'intelligence artificielle",
            "domaine de l'informatique": "secteur informatique",
            "permet de créer": "facilite la création",
            "systèmes capables": "systèmes aptes",
            "effectuer des tâches": "accomplir des missions",
            "tâches complexes": "missions complexes",
            "utilisent des algorithmes": "recourent à des algorithmes",
            "algorithmes sophistiqués": "algorithmes avancés",
            "apprendre à partir": "s'instruire à partir",
            "apprendre à partir de données": "acquérir des connaissances à partir de données",
            "Ces systèmes": "Ces dispositifs",
            "Les systèmes": "Les dispositifs"
        }
        
        result = text
        for original, replacement in aggressive_replacements.items():
            pattern = r'\b' + re.escape(original) + r'\b'
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Restructure sentences
        sentences = result.split('.')
        restructured = []
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Change sentence structure
            if i % 2 == 0 and len(sentence) > 20:
                # Try to reorder: "X est Y" -> "Y caractérise X" or similar
                if "est un" in sentence.lower():
                    parts = re.split(r'\s+est\s+un\s+', sentence, flags=re.IGNORECASE, maxsplit=1)
                    if len(parts) == 2:
                        sentence = f"{parts[1]} caractérise {parts[0]}"
                elif "permet de" in sentence.lower():
                    sentence = sentence.replace("permet de", "rend possible de")
            
            restructured.append(sentence)
        
        result = '. '.join(restructured)
        if result and not result.endswith('.'):
            result += '.'
        
        # Ensure first letter is capitalized
        if result and not result[0].isupper():
            result = result[0].upper() + result[1:]
        
        return result
    
    def _ensemble_reformulate(self, prompt: str, original_text: str, style: str, params: dict) -> str:
        """
        Ensemble method: combine results from multiple models for better quality
        """
        results = []
        scores = []
        
        # Try primary model
        if self.reformulation_pipeline:
            try:
                result = self.reformulation_pipeline(prompt, **params)
                if result and result[0].get("generated_text"):
                    reformulated = result[0]["generated_text"]
                    score = self._score_reformulation_quality(original_text, reformulated, style)
                    results.append(reformulated)
                    scores.append(score)
            except Exception as e:
                print(f"Error with primary reformulation model: {e}")
        
        # Try alternative models
        for alt_model_name in self.alternative_models:
            try:
                alt_pipeline = self._load_alternative_reformulation_model(alt_model_name)
                if alt_pipeline:
                    result = alt_pipeline(prompt, **params)
                    if result and result[0].get("generated_text"):
                        reformulated = result[0]["generated_text"]
                        score = self._score_reformulation_quality(original_text, reformulated, style)
                        results.append(reformulated)
                        scores.append(score)
            except Exception as e:
                print(f"Error with alternative reformulation model {alt_model_name}: {e}")
        
        # Select best result
        if not results:
            return original_text
        
        if len(results) == 1:
            return results[0]
        
        # Use best scoring result
        best_idx = scores.index(max(scores))
        return results[best_idx]
    
    def _load_alternative_reformulation_model(self, model_name: str):
        """Load alternative reformulation model on demand"""
        if model_name in self.alternative_pipelines:
            return self.alternative_pipelines[model_name]
        
        try:
            from transformers import pipeline, T5Tokenizer
            # Ensure model_name is a string
            model_name_str = str(model_name) if model_name else "plguillou/t5-base-fr-sum-cnndm"
            # Try T5 tokenizer first
            try:
                tokenizer = T5Tokenizer.from_pretrained(model_name_str, local_files_only=False)
            except:
                tokenizer = AutoTokenizer.from_pretrained(model_name_str, use_fast=False, local_files_only=False)
            
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name_str, local_files_only=False)
            alt_pipeline = pipeline(
                "text2text-generation",
                model=model,
                tokenizer=tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            self.alternative_pipelines[model_name] = alt_pipeline
            return alt_pipeline
        except Exception as e:
            print(f"Could not load alternative reformulation model {model_name}: {e}")
            return None
    
    def _score_reformulation_quality(self, original: str, reformulated: str, style: str) -> float:
        """Score the quality of a reformulation"""
        if not reformulated or len(reformulated.strip()) < 10:
            return 0.0
        
        score = 0.5  # Base score
        
        # Length check (should be similar but not identical)
        orig_len = len(original.split())
        reform_len = len(reformulated.split())
        length_ratio = reform_len / orig_len if orig_len > 0 else 1.0
        
        if 0.5 <= length_ratio <= 2.0:  # Reasonable length
            score += 0.2
        elif 0.3 <= length_ratio <= 3.0:  # Acceptable
            score += 0.1
        
        # Diversity check (should be different from original)
        if reformulated.lower() != original.lower():
            score += 0.2
        
        # Style-specific checks
        if style == "academic":
            # Check for academic vocabulary
            academic_words = ['analyse', 'étude', 'recherche', 'méthode', 'théorie', 'concept', 'hypothèse']
            if any(word in reformulated.lower() for word in academic_words):
                score += 0.1
        elif style == "simplification":
            # Check for simple vocabulary (fewer complex words)
            complex_words = ['néanmoins', 'toutefois', 'cependant', 'par conséquent']
            if not any(word in reformulated.lower() for word in complex_words):
                score += 0.1
        
        return min(1.0, score)

