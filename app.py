from flask import Flask, request, send_file
from flask_cors import CORS
import markdown
from weasyprint import HTML
import io
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.json
        md_content = data.get('markdown', '')
        css_content = data.get('css', '')
        
        logging.info(f"Received markdown length: {len(md_content)}")
        logging.info(f"Received CSS length: {len(css_content)}")
        
        # Convertir Markdown en HTML
        html_body = markdown.markdown(
            md_content, 
            extensions=['extra', 'nl2br', 'sane_lists', 'codehilite']
        )
        
        # HTML complet avec CSS
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                {css_content}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """
        
        logging.info("Converting to PDF...")
        
        # Générer le PDF avec WeasyPrint
        pdf_bytes = HTML(string=full_html).write_pdf()
        
        logging.info(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
        
        # Retourner le PDF
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='newsletter.pdf'
        )
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {'error': str(e)}, 500

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy', 'service': 'PDF Converter API'}

@app.route('/', methods=['GET'])
def root():
    return {
        'message': 'PDF Converter API',
        'endpoints': {
            '/health': 'GET - Health check',
            '/convert': 'POST - Convert markdown to PDF'
        }
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
