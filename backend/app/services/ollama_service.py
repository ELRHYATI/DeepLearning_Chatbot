"""
Service for integrating Ollama with Mistral and other models
"""
import httpx
import os
from typing import Dict, Optional, List, AsyncGenerator
from app.utils.logger import get_logger

logger = get_logger()

# Note: ollama package is optional - we use httpx directly for better control


class OllamaService:
    """Service for interacting with Ollama API"""
    
    def __init__(self):
        # Ollama configuration
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.default_model = os.getenv("OLLAMA_MODEL", "mistral")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "120.0"))
        self.available_models = []
        self._check_connection()
    
    def _check_connection(self, retry: bool = True):
        """Check if Ollama is available"""
        try:
            # Try with a longer timeout and better error handling
            response = httpx.get(
                f"{self.ollama_url}/api/tags",
                timeout=10.0,  # Increased timeout
                follow_redirects=True
            )
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                self.available_models = [model["name"] for model in models]
                if self.available_models:
                    logger.info(f"Ollama connected at {self.ollama_url}. Available models: {self.available_models}")
                else:
                    logger.warning(f"Ollama connected but no models found. Use 'ollama pull mistral' to install a model.")
                return True
            else:
                logger.warning(f"Ollama returned status {response.status_code} at {self.ollama_url}")
                self.available_models = []
                return False
        except httpx.ConnectError as e:
            if retry:
                # Try alternative URL formats
                alternative_urls = [
                    "http://127.0.0.1:11434",
                    "http://localhost:11434"
                ]
                for alt_url in alternative_urls:
                    if alt_url != self.ollama_url:
                        try:
                            logger.info(f"Trying alternative Ollama URL: {alt_url}")
                            response = httpx.get(f"{alt_url}/api/tags", timeout=10.0)
                            if response.status_code == 200:
                                self.ollama_url = alt_url
                                data = response.json()
                                models = data.get("models", [])
                                self.available_models = [model["name"] for model in models]
                                logger.info(f"Ollama found at {alt_url}. Available models: {self.available_models}")
                                return True
                        except:
                            continue
            
            logger.warning(f"Ollama connection error at {self.ollama_url}: {e}")
            logger.info("To use Ollama: 1) Install Ollama from https://ollama.ai 2) Run 'ollama serve' 3) Run 'ollama pull mistral'")
            self.available_models = []
            return False
        except httpx.TimeoutException:
            logger.warning(f"Ollama timeout at {self.ollama_url}. Is Ollama running?")
            self.available_models = []
            return False
        except Exception as e:
            logger.warning(f"Ollama check failed at {self.ollama_url}: {e}")
            logger.info("To use Ollama: 1) Install Ollama from https://ollama.ai 2) Run 'ollama serve' 3) Run 'ollama pull mistral'")
            self.available_models = []
            return False
    
    def is_available(self, recheck: bool = False) -> bool:
        """Check if Ollama is available and has models"""
        if recheck or len(self.available_models) == 0:
            self._check_connection(retry=True)
        return len(self.available_models) > 0
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return self.available_models
    
    def _find_model_variant(self, model_name: str) -> Optional[str]:
        """Find a model variant that matches the base name (e.g., 'mistral' -> 'mistral:7b-instruct-q4_0')"""
        # Exact match
        if model_name in self.available_models:
            return model_name
        
        # Find any model that starts with the base name
        for available_model in self.available_models:
            if available_model.startswith(model_name + ":") or available_model == model_name:
                logger.info(f"Found model variant: {available_model} for requested {model_name}")
                return available_model
        
        return None
    
    def _ensure_model_pulled(self, model_name: str) -> Optional[str]:
        """Ensure model is pulled/available. Returns the actual model name to use, or None if not available."""
        # Check if exact match or variant exists
        actual_model = self._find_model_variant(model_name)
        if actual_model:
            return actual_model
        
        # Try to pull the model
        try:
            logger.info(f"Pulling model {model_name}...")
            response = httpx.post(
                f"{self.ollama_url}/api/pull",
                json={"name": model_name},
                timeout=300.0  # 5 minutes for model pull
            )
            if response.status_code == 200:
                # Update available models
                self._check_connection()
                actual_model = self._find_model_variant(model_name)
                return actual_model
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
        
        return None
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict:
        """
        Generate a response using Ollama
        
        Args:
            prompt: User prompt/question
            model: Model name (defaults to configured model)
            context: Optional context for RAG
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
        
        Returns:
            Dictionary with response, model used, and metadata
        """
        # Recheck availability before use
        if not self.is_available(recheck=True):
            return {
                "response": "Ollama n'est pas disponible. Veuillez démarrer Ollama (ollama serve) et installer le modèle Mistral (ollama pull mistral).",
                "model": None,
                "error": "Ollama not available",
                "help": "Install Ollama from https://ollama.ai, then run 'ollama serve' and 'ollama pull mistral'"
            }
        
        requested_model = model or self.default_model
        
        # Ensure model is available and get actual model name (may be a variant)
        actual_model = self._ensure_model_pulled(requested_model)
        if not actual_model:
            return {
                "response": f"Le modèle {requested_model} n'est pas disponible. Veuillez l'installer avec: ollama pull {requested_model}",
                "model": requested_model,
                "error": "Model not available"
            }
        
        # Build the full prompt
        full_prompt = self._build_prompt(prompt, context, system_prompt)
        
        try:
            if stream:
                # For streaming, return generator
                return await self._generate_stream(full_prompt, actual_model, temperature, max_tokens)
            else:
                # Non-streaming request
                response = httpx.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": actual_model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        }
                    },
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "response": data.get("response", "").strip(),
                        "model": actual_model,
                        "done": data.get("done", True),
                        "context": data.get("context", []),
                        "total_duration": data.get("total_duration", 0),
                        "load_duration": data.get("load_duration", 0),
                        "prompt_eval_count": data.get("prompt_eval_count", 0),
                        "eval_count": data.get("eval_count", 0)
                    }
                else:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return {
                        "response": f"Erreur lors de la génération: {response.status_code}",
                        "model": actual_model,
                        "error": f"API error: {response.status_code}"
                    }
        except httpx.TimeoutException:
            logger.error(f"Ollama request timeout after {self.timeout}s")
            return {
                "response": "La requête a pris trop de temps. Veuillez réessayer.",
                "model": model_name,
                "error": "Timeout"
            }
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}", exc_info=e)
            return {
                "response": f"Erreur lors de la communication avec Ollama: {str(e)}",
                "model": model_name,
                "error": str(e)
            }
    
    async def _generate_stream(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[Dict, None]:
        """Generate streaming response"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        }
                    }
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    import json
                                    data = json.loads(line)
                                    yield {
                                        "response": data.get("response", ""),
                                        "done": data.get("done", False),
                                        "model": model
                                    }
                                    if data.get("done", False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                    else:
                        yield {
                            "response": f"Erreur: {response.status_code}",
                            "done": True,
                            "error": f"API error: {response.status_code}"
                        }
        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=e)
            yield {
                "response": f"Erreur: {str(e)}",
                "done": True,
                "error": str(e)
            }
    
    def generate_response_sync(
        self,
        prompt: str,
        model: Optional[str] = None,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict:
        """
        Synchronous version of generate_response
        Uses httpx directly in sync mode to avoid asyncio issues
        """
        # Recheck availability before use
        if not self.is_available(recheck=True):
            return {
                "response": "Ollama n'est pas disponible. Veuillez démarrer Ollama (ollama serve) et installer le modèle Mistral (ollama pull mistral).",
                "model": None,
                "error": "Ollama not available",
                "help": "Install Ollama from https://ollama.ai, then run 'ollama serve' and 'ollama pull mistral'"
            }
        
        requested_model = model or self.default_model
        
        # Ensure model is available and get actual model name (may be a variant)
        actual_model = self._ensure_model_pulled(requested_model)
        if not actual_model:
            return {
                "response": f"Le modèle {requested_model} n'est pas disponible. Veuillez l'installer avec: ollama pull {requested_model}",
                "model": requested_model,
                "error": "Model not available"
            }
        
        # Build the full prompt
        full_prompt = self._build_prompt(prompt, context, system_prompt)
        
        try:
            # Use httpx in sync mode
            response = httpx.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": actual_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "response": data.get("response", "").strip(),
                    "model": actual_model,
                    "done": data.get("done", True),
                    "context": data.get("context", []),
                    "total_duration": data.get("total_duration", 0),
                    "load_duration": data.get("load_duration", 0),
                    "prompt_eval_count": data.get("prompt_eval_count", 0),
                    "eval_count": data.get("eval_count", 0)
                }
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return {
                    "response": f"Erreur lors de la génération: {response.status_code}",
                    "model": actual_model,
                    "error": f"API error: {response.status_code}"
                }
        except httpx.TimeoutException:
            logger.error(f"Ollama request timeout after {self.timeout}s")
            return {
                "response": "La requête a pris trop de temps. Veuillez réessayer.",
                "model": actual_model,
                "error": "Timeout"
            }
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}", exc_info=e)
            return {
                "response": f"Erreur lors de la communication avec Ollama: {str(e)}",
                "model": actual_model,
                "error": str(e)
            }
    
    def _build_prompt(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Build the full prompt with context and system instructions"""
        parts = []
        
        # System prompt (default for French academic chatbot)
        if system_prompt:
            parts.append(f"System: {system_prompt}")
        else:
            parts.append(
                "System: Tu es un assistant académique français spécialisé dans l'aide aux étudiants. "
                "Tu réponds de manière précise, structurée et académique. Utilise un langage clair et professionnel. "
                "Si tu ne connais pas quelque chose, dis-le honnêtement."
            )
        
        # Context (for RAG)
        if context:
            parts.append(f"\nContexte:\n{context}")
        
        # User prompt
        parts.append(f"\nQuestion: {prompt}\n\nRéponse:")
        
        return "\n".join(parts)
    
    def answer_question_sync(
        self,
        question: str,
        context: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict:
        """
        Synchronous wrapper for answer_question
        """
        # Recheck availability first
        if not self.is_available(recheck=True):
            return {
                "question": question,
                "answer": "Ollama n'est pas disponible. Veuillez démarrer Ollama (ollama serve) et installer le modèle Mistral (ollama pull mistral).",
                "confidence": 0.0,
                "sources": [],
                "error": "Ollama not available"
            }
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If loop is running, we need to run in a separate thread with a new event loop
            import concurrent.futures
            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        self.answer_question(question, context, model)
                    )
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                return future.result(timeout=120)
        else:
            return loop.run_until_complete(
                self.answer_question(question, context, model)
            )
    
    def reformulate_text(
        self,
        text: str,
        style: str = "academic",
        model: Optional[str] = None
    ) -> Dict:
        """
        Reformulate text using Ollama (similar interface to ReformulationService)
        
        Args:
            text: Text to reformulate
            style: Style preference (academic, formal, simple, paraphrase)
            model: Model to use (defaults to configured model)
        
        Returns:
            Dictionary with original_text, reformulated_text, and changes
        """
        # Recheck availability first
        if not self.is_available(recheck=True):
            return {
                "original_text": text,
                "reformulated_text": text,
                "changes": {"error": "Ollama not available"}
            }
        
        # Build style-specific system prompt
        style_prompts = {
            "academic": (
                "Tu es un expert en rédaction académique française. "
                "Quand on te donne un texte à reformuler, tu dois UNIQUEMENT retourner le texte reformulé, "
                "sans ajouter d'explications, d'instructions ou de préfixes. "
                "Réécris le texte dans un style académique rigoureux et formel, "
                "utilise un vocabulaire précis et technique, structure les idées de manière logique, "
                "et adopte un ton objectif et scientifique. Conserve le sens original mais améliore la formulation."
            ),
            "formal": (
                "Tu es un expert en rédaction formelle française. "
                "Réécris le texte suivant dans un style formel et professionnel. "
                "Utilise un langage poli et respectueux, structure les phrases de manière claire et élégante."
            ),
            "paraphrase": (
                "Tu es un expert en paraphrase française. "
                "Paraphrase le texte suivant de manière à éviter le plagiat tout en conservant exactement le même sens. "
                "Utilise des synonymes, restructure les phrases, change l'ordre des idées si nécessaire, "
                "mais garde le sens original intact. Le texte reformulé doit être significativement différent "
                "dans la formulation mais identique dans le contenu sémantique."
            ),
            "simple": (
                "Tu es un expert en simplification de texte français. "
                "Simplifie le texte suivant pour le rendre plus accessible. "
                "Utilise un vocabulaire simple et courant, des phrases courtes et claires, "
                "évite le jargon technique, et explique les concepts complexes de manière simple."
            )
        }
        
        system_prompt = style_prompts.get(style, style_prompts["academic"])
        
        # Use a direct prompt without question/answer format
        # Build prompt directly without using _build_prompt to avoid "Question:" labels
        full_prompt = f"{system_prompt}\n\nTexte à reformuler:\n{text}\n\nTexte reformulé:"
        
        # Call Ollama API directly to avoid the question/answer prompt structure
        requested_model = model or self.default_model
        actual_model = self._ensure_model_pulled(requested_model)
        if not actual_model:
            return {
                "original_text": text,
                "reformulated_text": text,
                "changes": {"error": f"Model {requested_model} not available"}
            }
        
        try:
            response = httpx.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": actual_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7 if style == "paraphrase" else 0.5,
                        "num_predict": 2000,
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            data = response.json()
            result = {
                "response": data.get("response", "").strip(),
                "model": actual_model
            }
        except Exception as e:
            logger.error(f"Error calling Ollama for reformulation: {e}")
            return {
                "original_text": text,
                "reformulated_text": text,
                "changes": {"error": str(e)}
            }
        
        if "error" in result:
            return {
                "original_text": text,
                "reformulated_text": text,
                "changes": {"error": result.get("error", "Unknown error")}
            }
        
        reformulated = result.get("response", text).strip()
        
        # Aggressive cleanup - remove instruction patterns and prompt remnants
        import re
        
        # Remove the specific pattern seen in the image: "Texte reformulé (academic): ..."
        reformulated = re.sub(r'^[Tt]exte\s+reformulé\s*\([^)]+\)\s*[:：]\s*', '', reformulated, flags=re.MULTILINE)
        
        # Remove common instruction phrases at the start
        instruction_patterns = [
            r'^.*?[Rr]éécris.*?:?\s*',
            r'^.*?[Rr]éformule.*?:?\s*',
            r'^.*?[Rr]édécrire.*?:?\s*',
            r'^.*?[Ss]tyle.*?académique.*?:?\s*',
            r'^.*?[Uu]tilise.*?vocabulaire.*?:?\s*',
            r'^.*?[Ss]tructure.*?idées.*?:?\s*',
            r'^.*?[Tt]on.*?objectif.*?:?\s*',
            r'^.*?[Ll]es\s+idées\s+sont\s+structurellement.*?:?\s*',
        ]
        
        for pattern in instruction_patterns:
            reformulated = re.sub(pattern, '', reformulated, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove lines that contain instruction keywords
        lines = reformulated.split('\n')
        cleaned_lines = []
        skip_next = False
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Skip lines that are clearly instructions
            if any(keyword in line_lower for keyword in [
                'réécris', 'réformule', 'texte à reformuler', 'style académique',
                'vocabulaire précis', 'structure les idées', 'ton objectif', 
                'réponds uniquement', 'sans explications', 'texte reformulé (',
                'rédécrire ce texte', 'les idées sont structurellement',
                'en utilisant un vocabulaire', 'en structurant', 'selon un ton'
            ]):
                skip_next = True
                continue
            
            # If previous line was skipped and this line starts with instruction-like text, skip it too
            if skip_next and any(word in line_lower[:50] for word in ['en utilisant', 'selon', 'structure']):
                continue
            
            skip_next = False
            
            # Skip empty lines at the start
            if not cleaned_lines and not line.strip():
                continue
                
            cleaned_lines.append(line)
        
        reformulated = '\n'.join(cleaned_lines).strip()
        
        # Remove any remaining prefix patterns
        reformulated = re.sub(r'^(Texte|Réponse|Résultat|Réformulé)[:：]\s*', '', reformulated, flags=re.IGNORECASE)
        
        # Remove trailing instruction fragments
        reformulated = re.sub(r'\s*[\.。]\s*(L\'intelligence|Les systèmes|Ces systèmes).*$', '', reformulated, flags=re.IGNORECASE)
        
        # If the cleaned text is too short or empty, use original
        if len(reformulated.strip()) < len(text.strip()) * 0.3:
            reformulated = text
        
        # If still too similar, apply additional transformations
        if reformulated == text or len(reformulated) < len(text) * 0.5:
            # Fallback to rule-based transformations
            from app.services.reformulation_service import ReformulationService
            reform_service = ReformulationService()
            if style == "paraphrase":
                reformulated = reform_service._apply_paraphrase_transformations(text)
            elif style == "simple":
                reformulated = reform_service._apply_simplification_transformations(text)
            else:
                reformulated = reform_service._apply_academic_transformations(text, style)
        
        return {
            "original_text": text,
            "reformulated_text": reformulated,
            "changes": {
                "style": style,
                "word_count_change": len(reformulated.split()) - len(text.split()),
                "model": result.get("model", model or self.default_model)
            }
        }
    
    def reformulate_text_sync(
        self,
        text: str,
        style: str = "academic",
        model: Optional[str] = None
    ) -> Dict:
        """
        Synchronous wrapper for reformulate_text (now just calls it directly since it's sync)
        """
        return self.reformulate_text(text, style, model)
    
    async def answer_question(
        self,
        question: str,
        context: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict:
        """
        Answer a question using Ollama (similar interface to QAService)
        
        Args:
            question: The question in French
            context: Optional context paragraph
            model: Model to use (defaults to configured model)
        
        Returns:
            Dictionary with answer, confidence, and sources
        """
        system_prompt = (
            "Tu es un expert en question-réponse académique. "
            "Réponds de manière précise et structurée en français. "
            "Utilise le contexte fourni si disponible, sinon utilise tes connaissances générales. "
            "Sois concis mais complet."
        )
        
        result = await self.generate_response(
            prompt=question,
            model=model,
            context=context,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for more factual answers
            max_tokens=1500
        )
        
        if "error" in result:
            return {
                "question": question,
                "answer": result.get("response", "Erreur lors de la génération de la réponse."),
                "confidence": 0.0,
                "sources": []
            }
        
        # Calculate confidence based on response quality
        response_text = result.get("response", "")
        confidence = 0.7  # Base confidence for Ollama
        
        # Boost confidence if context was used
        if context and len(context) > 100:
            confidence = 0.85
        
        # Boost confidence for longer, more detailed answers
        if len(response_text) > 200:
            confidence = min(0.95, confidence + 0.1)
        elif len(response_text) > 100:
            confidence = min(0.90, confidence + 0.05)
        
        # Lower confidence for very short answers
        if len(response_text) < 50:
            confidence = 0.5
        
        return {
            "question": question,
            "answer": response_text,
            "confidence": confidence,
            "sources": [context[:200] + "..."] if context and len(context) > 200 else [],
            "model": result.get("model", model or self.default_model)
        }
    
    async def enhance_qa_response(
        self,
        original_answer: str,
        question: str,
        context: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict:
        """
        Enhance a QA response from another model (e.g., Camembert) using Ollama.
        Reviews, validates, and improves the answer for accuracy and clarity.
        
        Args:
            original_answer: The answer from the primary model
            question: The original question
            context: Optional context used
            model: Model to use (defaults to configured model)
        
        Returns:
            Dictionary with enhanced_answer, improvements, and validation
        """
        if not self.is_available(recheck=True):
            return {
                "enhanced_answer": original_answer,
                "improvements": [],
                "validated": False,
                "error": "Ollama not available"
            }
        
        system_prompt = (
            "Tu es un expert académique français chargé d'améliorer et de valider des réponses à des questions. "
            "Tu dois:\n"
            "1. Vérifier l'exactitude factuelle de la réponse\n"
            "2. Améliorer la clarté et la précision\n"
            "3. Corriger toute erreur ou imprécision\n"
            "4. Rendre la réponse plus académique et structurée\n"
            "5. S'assurer que la réponse répond bien à la question\n\n"
            "Retourne UNIQUEMENT la réponse améliorée, sans explications supplémentaires."
        )
        
        prompt = f"""Question: {question}\n\n"""
        if context:
            prompt += f"Contexte: {context}\n\n"
        prompt += f"Réponse originale à améliorer: {original_answer}\n\n"
        prompt += "Réponse améliorée et validée:"
        
        result = await self.generate_response(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.3,  # Low temperature for factual accuracy
            max_tokens=2000
        )
        
        if "error" in result:
            return {
                "enhanced_answer": original_answer,
                "improvements": [],
                "validated": False,
                "error": result.get("error")
            }
        
        enhanced = result.get("response", original_answer).strip()
        
        # Clean up any instruction remnants
        import re
        enhanced = re.sub(r'^(Réponse améliorée|Réponse validée|Réponse)[:：]\s*', '', enhanced, flags=re.IGNORECASE)
        enhanced = enhanced.strip()
        
        # If enhanced answer is too short or seems wrong, keep original
        if len(enhanced) < len(original_answer) * 0.5:
            enhanced = original_answer
        
        # Detect improvements
        improvements = []
        if len(enhanced) > len(original_answer) * 1.1:
            improvements.append("Réponse plus détaillée")
        if enhanced != original_answer:
            improvements.append("Contenu amélioré")
        
        return {
            "enhanced_answer": enhanced,
            "original_answer": original_answer,
            "improvements": improvements,
            "validated": True,
            "model": result.get("model", model or self.default_model)
        }
    
    def enhance_qa_response_sync(
        self,
        original_answer: str,
        question: str,
        context: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict:
        """Synchronous wrapper for enhance_qa_response"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If loop is running, we need to run in a separate thread with a new event loop
            import concurrent.futures
            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        self.enhance_qa_response(original_answer, question, context, model)
                    )
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                return future.result(timeout=120)
        else:
            return loop.run_until_complete(
                self.enhance_qa_response(original_answer, question, context, model)
            )
    
    async def enhance_reformulation(
        self,
        original_reformulation: str,
        original_text: str,
        style: str = "academic",
        model: Optional[str] = None
    ) -> Dict:
        """
        Enhance a reformulation from another model (e.g., T5) using Ollama.
        Improves quality, style consistency, and academic rigor.
        
        Args:
            original_reformulation: The reformulated text from primary model
            original_text: The original text
            style: Style preference (academic, formal, simple, paraphrase)
            model: Model to use (defaults to configured model)
        
        Returns:
            Dictionary with enhanced_reformulation and improvements
        """
        if not self.is_available(recheck=True):
            return {
                "enhanced_reformulation": original_reformulation,
                "improvements": [],
                "error": "Ollama not available"
            }
        
        style_instructions = {
            "academic": "style académique rigoureux, vocabulaire précis et technique, ton objectif et scientifique",
            "formal": "style formel et professionnel, langage poli et respectueux",
            "paraphrase": "paraphrase significativement différente mais conservant exactement le même sens",
            "simple": "style simple et accessible, vocabulaire courant, phrases courtes"
        }
        
        style_desc = style_instructions.get(style, style_instructions["academic"])
        
        system_prompt = (
            f"Tu es un expert en rédaction française spécialisé dans la reformulation. "
            f"Tu dois améliorer une reformulation pour qu'elle soit en {style_desc}. "
            f"Retourne UNIQUEMENT le texte reformulé amélioré, sans explications ni préfixes."
        )
        
        prompt = f"""Texte original: {original_text}\n\n"""
        prompt += f"Reformulation actuelle à améliorer: {original_reformulation}\n\n"
        prompt += f"Texte reformulé amélioré ({style}):"
        
        result = await self.generate_response(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.5 if style == "paraphrase" else 0.4,
            max_tokens=2000
        )
        
        if "error" in result:
            return {
                "enhanced_reformulation": original_reformulation,
                "improvements": [],
                "error": result.get("error")
            }
        
        enhanced = result.get("response", original_reformulation).strip()
        
        # Clean up instruction remnants
        import re
        patterns_to_remove = [
            r'^[Tt]exte\s+reformulé.*?[:：]\s*',
            r'^[Rr]éformulation.*?[:：]\s*',
            r'^[Aa]mélioré.*?[:：]\s*',
        ]
        for pattern in patterns_to_remove:
            enhanced = re.sub(pattern, '', enhanced, flags=re.IGNORECASE | re.MULTILINE)
        enhanced = enhanced.strip()
        
        # If enhanced is too different or too short, keep original
        if len(enhanced) < len(original_reformulation) * 0.5:
            enhanced = original_reformulation
        
        improvements = []
        if enhanced != original_reformulation:
            improvements.append("Qualité améliorée")
        if style == "academic" and any(word in enhanced.lower() for word in ["considérer", "démontrer", "analyser", "examiner"]):
            improvements.append("Vocabulaire académique renforcé")
        
        return {
            "enhanced_reformulation": enhanced,
            "original_reformulation": original_reformulation,
            "improvements": improvements,
            "model": result.get("model", model or self.default_model)
        }
    
    def enhance_reformulation_sync(
        self,
        original_reformulation: str,
        original_text: str,
        style: str = "academic",
        model: Optional[str] = None
    ) -> Dict:
        """Synchronous wrapper for enhance_reformulation"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If loop is running, we need to run in a separate thread with a new event loop
            import concurrent.futures
            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        self.enhance_reformulation(original_reformulation, original_text, style, model)
                    )
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                return future.result(timeout=120)
        else:
            return loop.run_until_complete(
                self.enhance_reformulation(original_reformulation, original_text, style, model)
            )
    
    async def enhance_grammar_correction(
        self,
        corrected_text: str,
        original_text: str,
        corrections: List[Dict],
        model: Optional[str] = None
    ) -> Dict:
        """
        Enhance grammar correction from LanguageTool using Ollama.
        Validates corrections and improves overall text quality.
        
        Args:
            corrected_text: Text corrected by LanguageTool
            original_text: Original text with errors
            corrections: List of corrections made
            model: Model to use (defaults to configured model)
        
        Returns:
            Dictionary with enhanced_corrected_text and additional_corrections
        """
        if not self.is_available(recheck=True):
            return {
                "enhanced_corrected_text": corrected_text,
                "additional_corrections": [],
                "error": "Ollama not available"
            }
        
        system_prompt = (
            "Tu es un expert en grammaire et style français. "
            "Tu dois vérifier et améliorer un texte déjà corrigé. "
            "Identifie les erreurs restantes, améliore le style, et assure-toi que le texte est parfait. "
            "Retourne UNIQUEMENT le texte amélioré, sans explications."
        )
        
        prompt = f"""Texte original: {original_text}\n\n"""
        prompt += f"Texte corrigé (à améliorer): {corrected_text}\n\n"
        prompt += "Corrections apportées:\n"
        for corr in corrections[:5]:  # List first 5 corrections
            prompt += f"- {corr.get('original', '')} → {corr.get('corrected', '')}\n"
        prompt += "\nTexte final amélioré:"
        
        result = await self.generate_response(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.2,  # Very low temperature for grammar accuracy
            max_tokens=2000
        )
        
        if "error" in result:
            return {
                "enhanced_corrected_text": corrected_text,
                "additional_corrections": [],
                "error": result.get("error")
            }
        
        enhanced = result.get("response", corrected_text).strip()
        
        # Clean up
        import re
        enhanced = re.sub(r'^(Texte.*?|Correction.*?|Amélioré.*?)[:：]\s*', '', enhanced, flags=re.IGNORECASE)
        enhanced = enhanced.strip()
        
        # If enhanced is too different, keep original correction
        if len(enhanced) < len(corrected_text) * 0.7:
            enhanced = corrected_text
        
        additional_corrections = []
        if enhanced != corrected_text:
            # Detect what changed
            additional_corrections.append("Améliorations de style et fluidité")
        
        return {
            "enhanced_corrected_text": enhanced,
            "original_corrected_text": corrected_text,
            "additional_corrections": additional_corrections,
            "model": result.get("model", model or self.default_model)
        }
    
    def enhance_grammar_correction_sync(
        self,
        corrected_text: str,
        original_text: str,
        corrections: List[Dict],
        model: Optional[str] = None
    ) -> Dict:
        """Synchronous wrapper for enhance_grammar_correction"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # If loop is running, we need to run in a separate thread with a new event loop
            import concurrent.futures
            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        self.enhance_grammar_correction(corrected_text, original_text, corrections, model)
                    )
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                return future.result(timeout=120)
        else:
            return loop.run_until_complete(
                self.enhance_grammar_correction(corrected_text, original_text, corrections, model)
            )
    
    def summarize_text(
        self,
        text: str,
        length_style: str = "medium",
        model: Optional[str] = None
    ) -> Dict:
        """
        Summarize text using Ollama
        
        Args:
            text: Text to summarize
            length_style: Style of summary (short, medium, long, detailed)
            model: Model to use (defaults to configured model)
        
        Returns:
            Dictionary with summary, original_length, summary_length, compression_ratio
        """
        if not self.is_available(recheck=True):
            return {
                "summary": text,
                "original_length": len(text),
                "summary_length": len(text),
                "compression_ratio": 1.0,
                "error": "Ollama not available"
            }
        
        # Build length-specific prompts
        length_prompts = {
            "short": "Fais un résumé très court et concis du texte suivant. Retourne UNIQUEMENT le résumé, sans explications:",
            "medium": "Fais un résumé moyen du texte suivant, en conservant les points principaux. Retourne UNIQUEMENT le résumé, sans explications:",
            "long": "Fais un résumé détaillé du texte suivant, en conservant tous les points importants. Retourne UNIQUEMENT le résumé, sans explications:",
            "detailed": "Fais un résumé très détaillé du texte suivant, en conservant tous les détails importants et la structure. Retourne UNIQUEMENT le résumé, sans explications:"
        }
        
        system_prompt = (
            "Tu es un expert en résumé de textes académiques français. "
            "Tu dois créer des résumés clairs, précis et structurés. "
            "Retourne UNIQUEMENT le résumé, sans ajouter de préfixes, d'explications ou de commentaires."
        )
        
        prompt = f"{length_prompts.get(length_style, length_prompts['medium'])}\n\n{text}\n\nRésumé:"
        
        requested_model = model or self.default_model
        actual_model = self._ensure_model_pulled(requested_model)
        if not actual_model:
            return {
                "summary": text,
                "original_length": len(text),
                "summary_length": len(text),
                "compression_ratio": 1.0,
                "error": f"Model {requested_model} not available"
            }
        
        try:
            response = httpx.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": actual_model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for more factual summaries
                        "num_predict": 500 if length_style == "short" else (800 if length_style == "medium" else (1200 if length_style == "long" else 2000)),
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            data = response.json()
            summary = data.get("response", "").strip()
            
            # Clean up summary
            summary = re.sub(r'^Résumé[:\s]*', '', summary, flags=re.IGNORECASE)
            summary = re.sub(r'^Summary[:\s]*', '', summary, flags=re.IGNORECASE)
            summary = summary.strip()
            
            original_length = len(text)
            summary_length = len(summary)
            compression_ratio = summary_length / original_length if original_length > 0 else 1.0
            
            return {
                "summary": summary,
                "original_length": original_length,
                "summary_length": summary_length,
                "compression_ratio": compression_ratio,
                "length_style": length_style,
                "model": actual_model
            }
        except Exception as e:
            logger.error(f"Error calling Ollama for summarization: {e}")
            return {
                "summary": text,
                "original_length": len(text),
                "summary_length": len(text),
                "compression_ratio": 1.0,
                "error": str(e)
            }
    
    def summarize_text_sync(
        self,
        text: str,
        length_style: str = "medium",
        model: Optional[str] = None
    ) -> Dict:
        """
        Synchronous wrapper for summarize_text
        """
        return self.summarize_text(text, length_style, model)
    
    def enhance_summarization_sync(
        self,
        original_summary: str,
        original_text: str,
        length_style: str = "medium",
        model: Optional[str] = None
    ) -> Dict:
        """
        Enhance a summary from another model using Ollama
        
        Args:
            original_summary: Summary from primary model
            original_text: Original text that was summarized
            length_style: Style of summary
            model: Model to use (defaults to configured model)
        
        Returns:
            Dictionary with enhanced_summary
        """
        if not self.is_available(recheck=True):
            return {
                "enhanced_summary": original_summary,
                "error": "Ollama not available"
            }
        
        system_prompt = (
            "Tu es un expert en résumé de textes académiques français. "
            "Tu dois améliorer et valider des résumés existants. "
            "Vérifie que le résumé est complet, précis et bien structuré. "
            "Retourne UNIQUEMENT le résumé amélioré, sans explications."
        )
        
        prompt = f"""Texte original:
{original_text}

Résumé actuel à améliorer:
{original_summary}

Résumé amélioré et validé:"""
        
        requested_model = model or self.default_model
        actual_model = self._ensure_model_pulled(requested_model)
        if not actual_model:
            return {
                "enhanced_summary": original_summary,
                "error": f"Model {requested_model} not available"
            }
        
        try:
            response = httpx.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": actual_model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1000,
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            data = response.json()
            enhanced = data.get("response", "").strip()
            
            # Clean up
            enhanced = re.sub(r'^Résumé[:\s]*', '', enhanced, flags=re.IGNORECASE)
            enhanced = enhanced.strip()
            
            # If enhanced is too different or too short, keep original
            if len(enhanced) < len(original_summary) * 0.5:
                enhanced = original_summary
            
            return {
                "enhanced_summary": enhanced,
                "original_summary": original_summary,
                "model": actual_model
            }
        except Exception as e:
            logger.error(f"Error enhancing summarization: {e}")
            return {
                "enhanced_summary": original_summary,
                "error": str(e)
            }

