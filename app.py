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

app = Flask(__name__)
CORS(app)

def markdown_to_pdf(markdown_text):
    """Convertit du Markdown simple en PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    
    # Styles personnalisés
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1e3a8a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=HexColor('#1e40af'),
        spaceBefore=20,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderColor=HexColor('#60a5fa'),
        borderPadding=5,
        leftIndent=10
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=HexColor('#2563eb'),
        spaceBefore=15,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )
    
    story = []
    lines = markdown_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.3*cm))
            continue
            
        # Titre principal
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, title_style))
            
        # Titre niveau 2
        elif line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, h2_style))
            
        # Titre niveau 3
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, h3_style))
            
        # Liste
        elif line.startswith('- ') or line.startswith('* '):
            text = '• ' + line[2:].strip()
            story.append(Paragraph(text, body_style))
            
        # Texte normal
        else:
            # Gestion basique du bold et italic
            text = line.replace('**', '<b>').replace('**', '</b>')
            text = text.replace('*', '<i>').replace('*', '</i>')
            story.append(Paragraph(text, body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.json
        markdown = data.get('markdown', '')
        
        if not markdown:
            return {'error': 'No markdown provided'}, 400
        
        # Générer le PDF
        pdf_buffer = markdown_to_pdf(markdown)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='newsletter.pdf'
        )
        
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}

@app.route('/', methods=['GET'])
def root():
    return {'service': 'PDF Converter', 'status': 'running'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
