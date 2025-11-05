from flask import Flask, request, send_file
from flask_cors import CORS
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.colors import HexColor
import logging

app = Flask(__name__)
CORS(app)

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_markdown_to_pdf(markdown_text):
    """
    Convertit du Markdown simple en PDF avec ReportLab
    
    Args:
        markdown_text (str): Le contenu markdown à convertir
        
    Returns:
        io.BytesIO: Buffer contenant le PDF généré
    """
    try:
        logger.info(f"Début conversion PDF, longueur markdown: {len(markdown_text)}")
        
        # Créer un buffer en mémoire pour le PDF
        pdf_buffer = io.BytesIO()
        
        # Créer le document PDF avec marges
        document = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            topMargin=2*cm,
            bottomMargin=2*cm,
            leftMargin=2*cm,
            rightMargin=2*cm
        )
        
        # Récupérer les styles de base
        base_styles = getSampleStyleSheet()
        
        # Créer des styles personnalisés
        style_title = ParagraphStyle(
            'CustomTitle',
            parent=base_styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=28
        )
        
        style_h2 = ParagraphStyle(
            'CustomH2',
            parent=base_styles['Heading2'],
            fontSize=18,
            textColor=HexColor('#1e40af'),
            spaceBefore=20,
            spaceAfter=12,
            fontName='Helvetica-Bold',
            leftIndent=10,
            leading=22
        )
        
        style_h3 = ParagraphStyle(
            'CustomH3',
            parent=base_styles['Heading3'],
            fontSize=14,
            textColor=HexColor('#2563eb'),
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            leading=18
        )
        
        style_body = ParagraphStyle(
            'CustomBody',
            parent=base_styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=16
        )
        
        style_italic = ParagraphStyle(
            'CustomItalic',
            parent=base_styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Oblique',
            textColor=HexColor('#6b7280'),
            spaceAfter=15,
            leading=16
        )
        
        # Préparer le contenu (story)
        content = []
        
        # Séparer le markdown en lignes
        lines = markdown_text.split('\n')
        
        logger.info(f"Traitement de {len(lines)} lignes")
        
        for line in lines:
            line_stripped = line.strip()
            
            # Ignorer les lignes vides (mais ajouter un espace)
            if not line_stripped:
                content.append(Spacer(1, 0.3*cm))
                continue
            
            # Titre principal (H1)
            if line_stripped.startswith('# '):
                text = line_stripped[2:].strip()
                content.append(Paragraph(text, style_title))
                
            # Titre niveau 2 (H2)
            elif line_stripped.startswith('## '):
                text = line_stripped[3:].strip()
                content.append(Paragraph(text, style_h2))
                
            # Titre niveau 3 (H3)
            elif line_stripped.startswith('### '):
                text = line_stripped[4:].strip()
                content.append(Paragraph(text, style_h3))
                
            # Séparateur horizontal
            elif line_stripped.startswith('---'):
                content.append(Spacer(1, 0.5*cm))
                
            # Liste à puces
            elif line_stripped.startswith('- ') or line_stripped.startswith('* '):
                text = '• ' + line_stripped[2:].strip()
                # Traiter le markdown dans les listes
                text = process_inline_markdown(text)
                content.append(Paragraph(text, style_body))
                
            # Texte en italique (ligne commençant par *)
            elif line_stripped.startswith('*') and line_stripped.endswith('*'):
                text = line_stripped[1:-1].strip()
                content.append(Paragraph(text, style_italic))
                
            # Texte normal
            else:
                text = process_inline_markdown(line_stripped)
                content.append(Paragraph(text, style_body))
        
        # Construire le PDF
        logger.info("Construction du PDF...")
        document.build(content)
        
        # Repositionner au début du buffer
        pdf_buffer.seek(0)
        
        logger.info(f"PDF généré avec succès, taille: {len(pdf_buffer.getvalue())} bytes")
        
        return pdf_buffer
        
    except Exception as e:
        logger.error(f"Erreur lors de la conversion: {str(e)}", exc_info=True)
        raise


def process_inline_markdown(text):
    """
    Traite le markdown inline (bold, italic, liens)
    
    Args:
        text (str): Texte avec markdown inline
        
    Returns:
        str: Texte avec balises HTML pour ReportLab
    """
    # Bold (**texte**)
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    
    # Italic (*texte*)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    
    # Liens [texte](url) - ReportLab supporte les liens
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<link href="\2">\1</link>', text)
    
    # Code inline `code`
    text = re.sub(r'`(.+?)`', r'<font face="Courier" color="#1f2937">\1</font>', text)
    
    return text


@app.route('/convert', methods=['POST'])
def api_convert():
    """
    Endpoint principal de conversion Markdown -> PDF
    
    Attend un JSON avec:
    - markdown: le contenu markdown (string, obligatoire)
    - css: ignoré pour cette version (optionnel)
    """
    try:
        # Récupérer les données JSON
        data = request.get_json()
        
        if not data:
            logger.error("Aucune donnée JSON reçue")
            return {'error': 'No JSON data provided'}, 400
        
        markdown_content = data.get('markdown', '')
        
        if not markdown_content:
            logger.error("Champ 'markdown' vide ou absent")
            return {'error': 'No markdown content provided'}, 400
        
        logger.info(f"Requête reçue, longueur markdown: {len(markdown_content)}")
        
        # Convertir en PDF
        pdf_file = convert_markdown_to_pdf(markdown_content)
        
        # Retourner le PDF
        return send_file(
            pdf_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='newsletter.pdf'
        )
        
    except Exception as e:
        logger.error(f"Erreur dans /convert: {str(e)}", exc_info=True)
        return {
            'error': 'PDF conversion failed',
            'details': str(e)
        }, 500


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de santé pour vérifier que l'API fonctionne"""
    return {
        'status': 'healthy',
        'service': 'PDF Converter API',
        'version': '1.0'
    }


@app.route('/', methods=['GET'])
def root():
    """Endpoint racine avec informations sur l'API"""
    return {
        'service': 'PDF Converter API',
        'status': 'running',
        'endpoints': {
            'POST /convert': 'Convert markdown to PDF',
            'GET /health': 'Health check',
            'GET /': 'API information'
        }
    }


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Démarrage du serveur sur le port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
