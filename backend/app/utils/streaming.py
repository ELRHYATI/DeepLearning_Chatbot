"""
Utilitaires pour le streaming de réponses avec Server-Sent Events (SSE)
"""
import json
import asyncio
from typing import AsyncGenerator, Generator, Optional
from fastapi.responses import StreamingResponse
from app.utils.logger import get_logger

logger = get_logger()


def format_sse_event(data: dict, event: Optional[str] = None) -> str:
    """
    Formate les données en format SSE (Server-Sent Events)
    
    Args:
        data: Données à envoyer
        event: Type d'événement (optionnel)
    
    Returns:
        Chaîne formatée SSE
    """
    lines = []
    if event:
        lines.append(f"event: {event}")
    
    # Convertir les données en JSON
    json_data = json.dumps(data, ensure_ascii=False)
    lines.append(f"data: {json_data}")
    lines.append("")  # Ligne vide pour terminer l'événement
    
    return "\n".join(lines)


async def stream_text_chunks(
    text: str,
    chunk_size: int = 3,
    delay: float = 0.02
) -> AsyncGenerator[str, None]:
    """
    Stream un texte par chunks pour un effet de frappe progressive
    
    Args:
        text: Texte à streamer
        chunk_size: Nombre de caractères par chunk
        delay: Délai entre les chunks en secondes
    
    Yields:
        Chunks de texte formatés en SSE
    """
    accumulated = ""
    
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        accumulated += chunk
        
        data = {
            "type": "chunk",
            "content": chunk,
            "accumulated": accumulated,
            "done": False
        }
        
        yield format_sse_event(data, event="message")
        await asyncio.sleep(delay)
    
    # Envoyer l'événement final
    final_data = {
        "type": "done",
        "content": "",
        "accumulated": accumulated,
        "done": True
    }
    yield format_sse_event(final_data, event="message")


async def stream_response(
    generator: AsyncGenerator[dict, None],
    initial_message: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Stream une réponse depuis un générateur async
    
    Args:
        generator: Générateur async qui produit des chunks de réponse
        initial_message: Message initial à envoyer (optionnel)
    
    Yields:
        Événements SSE formatés
    """
    # Envoyer le message initial si fourni
    if initial_message:
        data = {
            "type": "start",
            "message": initial_message
        }
        yield format_sse_event(data, event="start")
    
    try:
        async for chunk in generator:
            if isinstance(chunk, dict):
                yield format_sse_event(chunk, event="message")
            else:
                # Si c'est une chaîne, l'envoyer comme chunk
                data = {
                    "type": "chunk",
                    "content": str(chunk),
                    "done": False
                }
                yield format_sse_event(data, event="message")
    
    except Exception as e:
        logger.error("Error in stream_response", exc_info=e)
        error_data = {
            "type": "error",
            "error": str(e),
            "message": "Une erreur s'est produite lors du streaming."
        }
        yield format_sse_event(error_data, event="error")
    
    finally:
        # Envoyer l'événement de fin
        end_data = {
            "type": "end",
            "done": True
        }
        yield format_sse_event(end_data, event="end")


def create_streaming_response(
    generator: AsyncGenerator[str, None],
    media_type: str = "text/event-stream"
) -> StreamingResponse:
    """
    Crée une réponse de streaming SSE
    
    Args:
        generator: Générateur async qui produit des événements SSE
        media_type: Type MIME de la réponse
    
    Returns:
        StreamingResponse configurée
    """
    return StreamingResponse(
        generator,
        media_type=media_type,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Désactive le buffering nginx
        }
    )


async def stream_text_progressive(
    text: str,
    words_per_chunk: int = 2,
    delay: float = 0.05,
    character_by_character: bool = True
) -> AsyncGenerator[dict, None]:
    """
    Stream un texte caractère par caractère ou mot par mot pour un effet plus naturel
    
    Args:
        text: Texte à streamer
        words_per_chunk: Nombre de mots par chunk (si character_by_character=False)
        delay: Délai entre les chunks en secondes
        character_by_character: Si True, stream caractère par caractère, sinon mot par mot
    
    Yields:
        Dictionnaires avec les chunks de texte
    """
    accumulated = ""
    
    if character_by_character:
        # Stream caractère par caractère
        # Ensure text is a string
        text_str = str(text) if text is not None else ""
        
        for i, char in enumerate(text_str):
            accumulated += char
            
            yield {
                "type": "chunk",
                "content": str(char),  # Ensure content is always a string
                "accumulated": str(accumulated),  # Ensure accumulated is always a string
                "done": False,
                "progress": min(100, int((i + 1) / len(text_str) * 100)) if len(text_str) > 0 else 0
            }
            
            # Délai plus court pour caractères, mais variable selon le type
            if char == ' ':
                await asyncio.sleep(delay * 0.3)  # Espaces plus rapides
            elif char in '\n':
                await asyncio.sleep(delay * 0.5)  # Retours à la ligne
            else:
                await asyncio.sleep(delay * 0.8)  # Caractères normaux
    else:
        # Stream mot par mot (ancien comportement)
        words = text.split()
        
        for i in range(0, len(words), words_per_chunk):
            chunk_words = words[i:i + words_per_chunk]
            chunk = " ".join(chunk_words)
            
            # Ajouter un espace si ce n'est pas le début
            if accumulated:
                accumulated += " "
            accumulated += chunk
            
            yield {
                "type": "chunk",
                "content": str(chunk),  # Ensure content is always a string
                "accumulated": str(accumulated),  # Ensure accumulated is always a string
                "done": False,
                "progress": min(100, int((i + len(chunk_words)) / len(words) * 100)) if len(words) > 0 else 0
            }
            
            await asyncio.sleep(delay)
    
    # Envoyer le chunk final - ensure all values are strings
    yield {
        "type": "done",
        "content": "",
        "accumulated": str(accumulated) if accumulated else "",
        "done": True,
        "progress": 100
    }

