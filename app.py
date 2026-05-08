import os
import json
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from datetime import datetime

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)
os.makedirs(os.path.join(STATIC_FOLDER, 'css'), exist_ok=True)
os.makedirs(os.path.join(STATIC_FOLDER, 'js'), exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("WARNING: OPENAI_API_KEY not found in environment variables")
    client = None
else:
    client = OpenAI(api_key=api_key)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_data_with_ai(df):
    """Process data with pandas and generate insights with OpenAI"""
    if client is None:
        raise ValueError("OpenAI API key not configured")

    # Data profiling
    summary_stats = df.describe(include='all').to_string()
    columns_info = df.columns.tolist()
    sample_data = df.head(10).to_string()
    dtypes_info = df.dtypes.to_string()
    missing_values = df.isnull().sum().to_string()

    # Calculate additional metrics
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    prompt = f"""
    Act as a Senior Data Analyst and Business Consultant with 15+ years of experience.
    Analyze the following dataset and generate a comprehensive executive report.

    DATASET PROFILE:
    - Columns ({len(columns_info)}): {columns_info}
    - Numeric columns: {numeric_cols}
    - Categorical columns: {categorical_cols}
    - Total rows: {len(df)}

    DATA TYPES:
    {dtypes_info}

    MISSING VALUES:
    {missing_values}

    STATISTICAL SUMMARY:
    {summary_stats}

    SAMPLE DATA (first 10 rows):
    {sample_data}

    INSTRUCTIONS:
    Return a JSON object with these exact keys:
    - "executive_summary": Professional 3-paragraph analysis (business context, key findings, strategic implications)
    - "key_metrics": Array of 5-7 objects with "name", "value", and "description" fields
    - "insights": Array of 4-6 deep analytical insights and trends
    - "recommendations": Array of 4-5 concrete actionable recommendations
    - "anomalies": Array of 3-4 data anomalies, risks, or alerts

    Use sophisticated corporate language. Be specific with numbers and percentages where possible.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an elite data analytics SaaS platform. Generate precise, actionable business intelligence."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=4000
        )

        result = json.loads(response.choices[0].message.content)

        # Validate required keys
        required_keys = ['executive_summary', 'key_metrics', 'insights', 'recommendations', 'anomalies']
        for key in required_keys:
            if key not in result:
                result[key] = []

        return result

    except Exception as e:
        print(f"OpenAI Error: {e}")
        # Fallback response
        return {
            "executive_summary": f"Analysis of dataset with {len(df)} rows and {len(columns_info)} columns. The data contains {len(numeric_cols)} numeric and {len(categorical_cols)} categorical variables.",
            "key_metrics": [{"name": "Total Records", "value": str(len(df)), "description": "Total rows in dataset"}],
            "insights": ["Dataset successfully processed"],
            "recommendations": ["Review data quality before making decisions"],
            "anomalies": ["No anomalies detected in initial scan"]
        }

def generate_pdf(data, original_filename):
    """Generate professional PDF report using ReportLab"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = secure_filename(original_filename).rsplit('.', 1)[0]
    pdf_filename = f"AI_Report_{safe_name}_{timestamp}.pdf"
    pdf_path = os.path.join(REPORTS_FOLDER, pdf_filename)

    doc = SimpleDocTemplate(
        pdf_path, 
        pagesize=letter,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=18
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=30,
        alignment=1,  # Center
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=1,
        spaceAfter=20
    )

    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#16213e'),
        spaceBefore=20,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        borderColor=colors.HexColor('#e94560'),
        borderWidth=2,
        borderPadding=5,
        leftIndent=-5
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=8,
        leading=14
    )

    metric_name_style = ParagraphStyle(
        'MetricName',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#16213e'),
        fontName='Helvetica-Bold'
    )

    metric_value_style = ParagraphStyle(
        'MetricValue',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#e94560'),
        fontName='Helvetica-Bold'
    )

    elements = []

    # Header
    elements.append(Paragraph("AI INTELLIGENCE REPORT", title_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", subtitle_style))
    elements.append(Paragraph(f"Source: {original_filename}", subtitle_style))
    elements.append(Spacer(1, 30))

    # Executive Summary
    elements.append(Paragraph("EXECUTIVE SUMMARY", header_style))
    summary_text = data.get('executive_summary', 'No summary available.')
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 15))

    # Key Metrics
    elements.append(Paragraph("KEY METRICS", header_style))
    metrics = data.get('key_metrics', [])

    if metrics:
        metrics_data = [['METRIC', 'VALUE', 'DESCRIPTION']]
        for metric in metrics[:7]:
            if isinstance(metric, dict):
                name = metric.get('name', 'N/A')
                value = str(metric.get('value', 'N/A'))
                desc = metric.get('description', '')
            else:
                name = str(metric)
                value = 'N/A'
                desc = ''
            metrics_data.append([name, value, desc])

        metrics_table = Table(metrics_data, colWidths=[140, 100, 220])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#e94560')),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(metrics_table)

    elements.append(Spacer(1, 20))

    # AI Insights
    elements.append(Paragraph("AI INSIGHTS", header_style))
    insights = data.get('insights', [])
    for i, insight in enumerate(insights[:6], 1):
        elements.append(Paragraph(f"<b>{i}.</b> {insight}", body_style))
    elements.append(Spacer(1, 15))

    # Strategic Recommendations
    elements.append(Paragraph("STRATEGIC RECOMMENDATIONS", header_style))
    recommendations = data.get('recommendations', [])
    for i, rec in enumerate(recommendations[:5], 1):
        elements.append(Paragraph(f"<b>{i}.</b> {rec}", body_style))
    elements.append(Spacer(1, 15))

    # Anomalies & Alerts
    elements.append(Paragraph("ANOMALIES & ALERTS", header_style))
    anomalies = data.get('anomalies', [])
    if anomalies:
        for i, anomaly in enumerate(anomalies[:4], 1):
            elements.append(Paragraph(f"<b>⚠ {i}.</b> {anomaly}", body_style))
    else:
        elements.append(Paragraph("No anomalies detected in the current dataset.", body_style))

    # Footer
    elements.append(Spacer(1, 40))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=1
    )
    elements.append(Paragraph("— AI Report Generator | Enterprise Intelligence Platform —", footer_style))

    doc.build(elements)
    return pdf_filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Invalid file type. Only CSV and XLSX allowed"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        file.save(filepath)

        # Read file based on extension
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, engine='openpyxl')

        # Validate data
        if df.empty:
            return jsonify({"success": False, "error": "File is empty"}), 400

        if len(df.columns) == 0:
            return jsonify({"success": False, "error": "No columns found in file"}), 400

        # AI Analysis
        analysis_results = analyze_data_with_ai(df)

        # Generate PDF
        pdf_filename = generate_pdf(analysis_results, filename)

        # Clean up uploaded file
        try:
            os.remove(filepath)
        except:
            pass

        return jsonify({
            "success": True,
            "analysis": analysis_results,
            "pdf_url": f"/download/{pdf_filename}",
            "rows": len(df),
            "columns": len(df.columns)
        })

    except pd.errors.EmptyDataError:
        return jsonify({"success": False, "error": "File is empty or corrupt"}), 400
    except pd.errors.ParserError:
        return jsonify({"success": False, "error": "Could not parse file. Check format."}), 400
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(REPORTS_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"success": False, "error": "File not found"}), 404

@app.errorhandler(413)
def too_large(e):
    return jsonify({"success": False, "error": "File too large (max 16MB)"}), 413

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')