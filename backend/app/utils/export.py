"""
Utilitaires pour l'export de conversations en PDF et Markdown
"""
import re
from datetime import datetime
from typing import List, Dict
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app.utils.logger import get_logger

logger = get_logger()


def clean_markdown(text: str) -> str:
    """Nettoie le texte markdown pour l'affichage"""
    # Supprimer les balises markdown simples
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)  # Italic
    text = re.sub(r'`(.*?)`', r'\1', text)  # Code
    text = re.sub(r'#+\s*(.*)', r'\1', text)  # Headers
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links
    return text


def format_message_for_export(message: Dict, role: str) -> str:
    """Formate un message pour l'export"""
    content = message.get('content', '')
    
    # Nettoyer le contenu markdown basique
    content = clean_markdown(content)
    
    # Ajouter le préfixe selon le rôle
    if role == 'user':
        return f"**Vous:** {content}"
    else:
        return f"**Assistant:** {content}"


def export_to_markdown(session_title: str, messages: List[Dict], created_at: str = None) -> str:
    """
    Exporte une conversation en Markdown
    
    Args:
        session_title: Titre de la session
        messages: Liste des messages
        created_at: Date de création (optionnel)
    
    Returns:
        Contenu Markdown
    """
    md_content = []
    
    # En-tête
    md_content.append(f"# {session_title}\n")
    
    if created_at:
        try:
            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime("%d/%m/%Y à %H:%M")
            md_content.append(f"*Créé le {formatted_date}*\n")
        except:
            md_content.append(f"*Créé le {created_at}*\n")
    
    md_content.append("\n---\n\n")
    
    # Messages
    for message in messages:
        role = message.get('role', 'user')
        content = message.get('content', '')
        created = message.get('created_at', '')
        
        # Formater la date si disponible
        date_str = ""
        if created:
            try:
                date_obj = datetime.fromisoformat(created.replace('Z', '+00:00'))
                date_str = date_obj.strftime("%H:%M")
            except:
                pass
        
        # Ajouter le message
        if role == 'user':
            md_content.append(f"## 👤 Vous")
        else:
            md_content.append(f"## 🤖 Assistant")
        
        if date_str:
            md_content.append(f"*{date_str}*\n")
        
        md_content.append(f"\n{content}\n\n")
        md_content.append("---\n\n")
    
    return "\n".join(md_content)


def export_to_pdf(session_title: str, messages: List[Dict], created_at: str = None) -> BytesIO:
    """
    Exporte une conversation en PDF
    
    Args:
        session_title: Titre de la session
        messages: Liste des messages
        created_at: Date de création (optionnel)
    
    Returns:
        BytesIO contenant le PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=(0.2, 0.2, 0.5),
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    # Style pour les messages utilisateur
    user_style = ParagraphStyle(
        'UserMessage',
        parent=styles['Normal'],
        fontSize=11,
        textColor=(0.1, 0.3, 0.6),
        leftIndent=0,
        rightIndent=0,
        spaceAfter=6
    )
    
    # Style pour les messages assistant
    assistant_style = ParagraphStyle(
        'AssistantMessage',
        parent=styles['Normal'],
        fontSize=11,
        textColor=(0.2, 0.2, 0.2),
        leftIndent=20,
        rightIndent=0,
        spaceAfter=6
    )
    
    # Style pour les dates
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=(0.5, 0.5, 0.5),
        spaceAfter=12
    )
    
    # Titre
    story.append(Paragraph(session_title, title_style))
    story.append(Spacer(1, 0.1 * inch))
    
    # Date de création
    if created_at:
        try:
            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime("%d/%m/%Y à %H:%M")
            story.append(Paragraph(f"<i>Créé le {formatted_date}</i>", date_style))
        except:
            story.append(Paragraph(f"<i>Créé le {created_at}</i>", date_style))
    
    story.append(Spacer(1, 0.2 * inch))
    
    # Messages
    for message in messages:
        role = message.get('role', 'user')
        content = message.get('content', '')
        created = message.get('created_at', '')
        
        # Nettoyer le contenu HTML/Markdown pour PDF
        content = clean_markdown(content)
        # Échapper les caractères HTML pour ReportLab
        content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # Convertir les sauts de ligne
        content = content.replace('\n', '<br/>')
        
        # Formater la date
        date_str = ""
        if created:
            try:
                date_obj = datetime.fromisoformat(created.replace('Z', '+00:00'))
                date_str = date_obj.strftime("%H:%M")
            except:
                pass
        
        # Ajouter le préfixe selon le rôle
        if role == 'user':
            prefix = "<b>👤 Vous</b>"
            style = user_style
        else:
            prefix = "<b>🤖 Assistant</b>"
            style = assistant_style
        
        # Construire le paragraphe
        para_text = f"{prefix}"
        if date_str:
            para_text += f" <i>({date_str})</i>"
        para_text += f"<br/>{content}"
        
        story.append(Paragraph(para_text, style))
        story.append(Spacer(1, 0.15 * inch))
    
    # Construire le PDF
    try:
        doc.build(story)
    except Exception as e:
        logger.error("Error building PDF", exc_info=e)
        raise
    
    buffer.seek(0)
    return buffer


def format_share_link(share_token: str, base_url: str = None) -> str:
    """
    Formate un lien de partage
    
    Args:
        share_token: Token de partage
        base_url: URL de base (optionnel)
    
    Returns:
        Lien de partage complet
    """
    if base_url:
        return f"{base_url}/share/{share_token}"
    return f"/share/{share_token}"

