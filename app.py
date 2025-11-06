from flask import Flask, request, send_file
from flask_cors import CORS
import io
import os
import logging
from weasyprint import HTML
import markdown

app = Flask(__name__)
CORS(app)

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_markdown_to_html(markdown_text):
    """
    Convertit le markdown en HTML
    
    Args:
        markdown_text (str): Le contenu markdown
        
    Returns:
        str: HTML généré
    """
    # Convertir le markdown en HTML avec les extensions
    html_body = markdown.markdown(
        markdown_text,
        extensions=[
            'extra',        # Support des tables, définitions, etc.
            'nl2br',        # Conversion des newlines en <br>
            'sane_lists',   # Listes plus cohérentes
            'codehilite'    # Coloration syntaxique du code
        ]
    )
    
    return html_body


def create_pdf_from_html(html_content, css_content=''):
    """
    Crée un PDF à partir de HTML et CSS avec WeasyPrint
    
    Args:
        html_content (str): Le contenu HTML
        css_content (str): Le CSS personnalisé (optionnel)
        
    Returns:
        io.BytesIO: Buffer contenant le PDF
    """
    try:
        logger.info("Création du PDF avec WeasyPrint...")
        
        # Créer le HTML complet
        full_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsletter</title>
    <style>
        {css_content}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
        
        logger.info(f"HTML complet créé, longueur: {len(full_html)}")
        
        # Créer le document HTML avec WeasyPrint
        html_doc = HTML(string=full_html)
        
        logger.info("Document HTML créé, génération du PDF...")
        
        # CORRECTION: Utiliser write_pdf avec target=None pour retourner bytes
        # Au lieu de passer un buffer, on récupère directement les bytes
        pdf_bytes = html_doc.write_pdf()
        
        logger.info(f"✅ PDF généré, taille: {len(pdf_bytes)} bytes")
        
        # Créer un buffer et y écrire les bytes
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        
        logger.info("✅ Buffer PDF créé avec succès")
        
        return pdf_buffer
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du PDF: {str(e)}", exc_info=True)
        raise


@app.route('/convert', methods=['POST'])
def api_convert():
    """
    Endpoint de conversion Markdown -> PDF
    
    Attend un JSON avec:
    {
        "markdown": "# Contenu...",
        "css": "body { ... }",
        "pdf_options": { ... }  (optionnel, ignoré pour l'instant)
    }
    """
    try:
        # Récupérer les données JSON
        data = request.get_json()
        
        logger.info('=== REQUÊTE REÇUE ===')
        logger.info(f'Content-Type: {request.content_type}')
        
        if not data:
            logger.error("❌ Aucune donnée JSON reçue")
            return {'error': 'No JSON data provided'}, 400
        
        logger.info(f'Données reçues - Clés: {list(data.keys())}')
        
        # Extraire les paramètres
        markdown_content = data.get('markdown', '')
        css_content = data.get('css', '')
        pdf_options = data.get('pdf_options', {})
        
        logger.info(f'Markdown length: {len(markdown_content)}')
        logger.info(f'CSS length: {len(css_content)}')
        logger.info(f'PDF options: {pdf_options}')
        
        # Validation
        if not markdown_content or markdown_content.strip() == '':
            logger.error("❌ Le markdown est vide")
            return {
                'error': 'Markdown content is empty',
                'received_keys': list(data.keys())
            }, 400
        
        logger.info(f'Premiers 200 caractères du markdown: {markdown_content[:200]}')
        
        # Convertir le markdown en HTML
        logger.info("Conversion Markdown -> HTML...")
        html_content = convert_markdown_to_html(markdown_content)
        logger.info(f"HTML généré, longueur: {len(html_content)}")
        
        # Créer le PDF
        logger.info("Génération du PDF...")
        pdf_file = create_pdf_from_html(html_content, css_content)
        
        logger.info("✅ Envoi du PDF au client...")
        
        # Retourner le PDF
        return send_file(
            pdf_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='newsletter.pdf'
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur dans /convert: {str(e)}", exc_info=True)
        return {
            'error': 'PDF conversion failed',
            'details': str(e),
            'type': type(e).__name__
        }, 500


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de santé"""
    return {
        'status': 'healthy',
        'service': 'PDF Converter API (WeasyPrint)',
        'version': '2.1'
    }


@app.route('/', methods=['GET'])
def root():
    """Informations sur l'API"""
    return {
        'service': 'PDF Converter API',
        'engine': 'WeasyPrint',
        'status': 'running',
        'endpoints': {
            'POST /convert': 'Convert markdown to PDF',
            'GET /health': 'Health check',
            'GET /': 'API information'
        }
    }


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Démarrage du serveur sur le port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
