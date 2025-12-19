import language_tool_python
from typing import List, Dict
import re
import time
from app.utils.logger import get_logger

logger = get_logger()

class GrammarService:
    def __init__(self):
        try:
            # Ensure Java log prevention is configured BEFORE any Java process
            try:
                from app.utils.java_log_prevention import configure_java_environment
                configure_java_environment()
            except Exception as config_error:
                logger.warning(f"Could not configure Java environment: {config_error}")
            
            # Try to find Java in common locations
            import os
            import subprocess
            
            # Check if Java is available
            java_available = False
            try:
                result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=5)
                java_available = True
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                # Try to find Java in Program Files
                java_paths = [
                    r"C:\Program Files\Microsoft\jdk-17.0.17.10-hotspot\bin\java.exe",
                    r"C:\Program Files\Java\jdk-17\bin\java.exe",
                    r"C:\Program Files\Java\jre-17\bin\java.exe",
                ]
                for java_path in java_paths:
                    if os.path.exists(java_path):
                        os.environ['JAVA_HOME'] = os.path.dirname(os.path.dirname(java_path))
                        os.environ['PATH'] = os.path.dirname(java_path) + os.pathsep + os.environ.get('PATH', '')
                        java_available = True
                        break
            
            if java_available:
                # Try to use remote server first (avoids local Java processes entirely)
                try:
                    start_time = time.time()
                    # Try remote server first to avoid local Java processes
                    try:
                        self.tool = language_tool_python.LanguageTool(
                            'fr-FR',
                            remote_server='https://api.languagetool.org'
                        )
                        logger.info("LanguageTool initialized with remote server (no local Java processes)")
                    except Exception as remote_error:
                        # Fallback to local if remote fails
                        logger.warning(f"Remote LanguageTool failed, using local: {remote_error}")
                        # Ensure Java options are set before local initialization
                        import platform
                        java_opts = '-XX:-CreateCoredumpOnCrash -XX:ErrorFile=NUL' if platform.system() == 'Windows' else '-XX:-CreateCoredumpOnCrash -XX:ErrorFile=/dev/null'
                        os.environ['_JAVA_OPTIONS'] = java_opts
                        os.environ['JAVA_TOOL_OPTIONS'] = java_opts
                        self.tool = language_tool_python.LanguageTool('fr-FR')
                    duration_ms = (time.time() - start_time) * 1000
                    logger.info(
                        "LanguageTool initialized successfully",
                        extra_data={"event": "service_init", "service": "GrammarService"}
                    )
                    logger.log_model_performance(
                        model_name="LanguageTool",
                        operation="initialization",
                        duration_ms=duration_ms
                    )
                except Exception as lt_error:
                    logger.warning(
                        "LanguageTool initialization error",
                        exc_info=lt_error,
                        extra_data={"event": "service_init_error", "service": "GrammarService"}
                    )
                    self.tool = None
            else:
                raise Exception("Java not found in PATH or common locations")
        except Exception as e:
            logger.warning(
                "Could not initialize LanguageTool",
                exc_info=e,
                extra_data={"event": "service_init_error", "service": "GrammarService"}
            )
            self.tool = None
    
    def correct_text(self, text: str) -> Dict:
        """
        Correct French text and provide detailed explanations.
        
        Args:
            text: Input French text with potential errors
            
        Returns:
            Dictionary with original_text, corrected_text, and corrections list
        """
        start_time = time.time()
        
        if not self.tool:
            logger.warning(
                "Grammar correction attempted but LanguageTool not available",
                extra_data={"event": "grammar_correction", "text_length": len(text)}
            )
            # Fallback: basic corrections
            return {
                "original_text": text,
                "corrected_text": text,
                "corrections": []
            }
        
        try:
            matches = self.tool.check(text)
            corrected_text = text
            corrections = []
            
            # Sort matches by offset in reverse order to apply corrections from end to start
            sorted_matches = sorted(matches, key=lambda x: x.offset, reverse=True)
            
            for match in sorted_matches:
                if match.replacements:
                    # Get the best replacement
                    replacement = match.replacements[0]
                    
                    # Get error length - try different attribute names for compatibility
                    error_length = getattr(match, 'errorLength', None) or getattr(match, 'error_length', None) or getattr(match, 'length', None) or len(replacement)
                    
                    # Create correction entry
                    correction = {
                        "original": text[match.offset:match.offset + error_length],
                        "corrected": replacement,
                        "explanation": match.message,
                        "rule_id": getattr(match, 'ruleId', None) or getattr(match, 'rule_id', None) or 'UNKNOWN',
                        "offset": match.offset
                    }
                    corrections.append(correction)
                    
                    # Apply correction
                    corrected_text = (
                        corrected_text[:match.offset] +
                        replacement +
                        corrected_text[match.offset + error_length:]
                    )
            
            # Reverse corrections list to show in order
            corrections.reverse()
            
            duration_ms = (time.time() - start_time) * 1000
            
            logger.log_model_performance(
                model_name="LanguageTool",
                operation="grammar_correction",
                duration_ms=duration_ms,
                input_size=len(text),
                output_size=len(corrected_text)
            )
            
            logger.info(
                f"Grammar correction completed: {len(corrections)} corrections found",
                extra_data={
                    "event": "grammar_correction",
                    "text_length": len(text),
                    "corrections_count": len(corrections)
                }
            )
            
            return {
                "original_text": text,
                "corrected_text": corrected_text,
                "corrections": corrections
            }
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.log_error_with_context(
                error=e,
                context={
                    "operation": "grammar_correction",
                    "text_length": len(text),
                    "duration_ms": duration_ms
                }
            )
            # Return original text on error
            return {
                "original_text": text,
                "corrected_text": text,
                "corrections": []
            }
    
    def explain_correction(self, original: str, corrected: str, rule_id: str) -> str:
        """
        Provide detailed explanation for a specific correction.
        """
        explanations = {
            "FR_SPELL": "Erreur d'orthographe détectée.",
            "FR_GRAMMAR": "Erreur grammaticale détectée.",
            "FR_PREPOSITION": "Erreur de préposition.",
            "FR_AGREEMENT": "Erreur d'accord (genre/nombre).",
        }
        
        return explanations.get(rule_id, "Correction suggérée pour améliorer la qualité du texte.")

