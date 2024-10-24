import pandas as pd
import json
from typing import Dict, List
import csv
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def format_race_data(form_data: pd.DataFrame, predictions: List[Dict], race_info: Dict) -> Dict:
    """Format race data for export"""
    export_data = {
        'race_info': race_info,
        'form_guide': form_data.to_dict('records') if not form_data.empty else [],
        'predictions': predictions,
        'track_analysis': {
            'condition': race_info.get('trackCondition', 'Unknown'),
            'distance': race_info.get('distance', 'Unknown'),
            'prize_money': race_info.get('prizeMoney', 'Unknown')
        }
    }
    return export_data

def export_to_csv(form_data: pd.DataFrame) -> str:
    """Export form guide data to CSV"""
    if form_data.empty:
        return ""
    
    # Create string buffer
    output = io.StringIO()
    form_data.to_csv(output, index=False)
    return output.getvalue()

def export_to_json(export_data: Dict) -> str:
    """Export complete race analysis to JSON"""
    return json.dumps(export_data, indent=2)

def export_to_text(export_data: Dict) -> str:
    """Export race analysis as formatted text"""
    text = []
    
    # Race Information
    text.append("RACE ANALYSIS REPORT")
    text.append("=" * 20)
    race_info = export_data.get('race_info', {})
    text.append(f"\nRace Details:")
    text.append(f"Distance: {race_info.get('distance', 'Unknown')}")
    text.append(f"Track Condition: {race_info.get('trackCondition', 'Unknown')}")
    text.append(f"Prize Money: ${race_info.get('prizeMoney', 'Unknown')}")
    
    # Predictions
    text.append("\nPredictions:")
    text.append("-" * 20)
    for i, pred in enumerate(export_data.get('predictions', []), 1):
        text.append(f"\n{i}. {pred.get('horse', 'Unknown')}")
        text.append(f"   Rating: {pred.get('score', 0):.2f}")
        text.append(f"   Confidence: {pred.get('confidence', 'Unknown')}")
    
    # Form Guide
    text.append("\nForm Guide:")
    text.append("-" * 20)
    for horse in export_data.get('form_guide', []):
        text.append(f"\n{horse.get('Horse', 'Unknown')}")
        text.append(f"Barrier: {horse.get('Barrier', 'Unknown')}")
        text.append(f"Weight: {horse.get('Weight', 'Unknown')}")
        text.append(f"Jockey: {horse.get('Jockey', 'Unknown')}")
        text.append(f"Form: {horse.get('Form', 'Unknown')}")
        text.append(f"Rating: {horse.get('Rating', 'Unknown')}")
    
    return "\n".join(text)

def export_to_pdf(export_data: Dict) -> bytes:
    """Generate PDF report with race analysis"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        elements.append(Paragraph("Race Analysis Report", styles['Heading1']))
        
        # Race Information
        race_info = export_data.get('race_info', {})
        race_data = [
            ["Race Details", ""],
            ["Distance", race_info.get('distance', 'Unknown')],
            ["Track Condition", race_info.get('trackCondition', 'Unknown')],
            ["Prize Money", f"${race_info.get('prizeMoney', 'Unknown')}"]
        ]
        
        t = Table(race_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        
        # Predictions
        elements.append(Paragraph("Predictions", styles['Heading2']))
        pred_data = [["Horse", "Rating", "Confidence"]]
        for pred in export_data.get('predictions', []):
            pred_data.append([
                pred.get('horse', 'Unknown'),
                f"{pred.get('score', 0):.2f}",
                pred.get('confidence', 'Unknown')
            ])
        
        t = Table(pred_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        
        # Form Guide
        elements.append(Paragraph("Form Guide", styles['Heading2']))
        form_data = [["Horse", "Barrier", "Weight", "Jockey", "Form", "Rating"]]
        for horse in export_data.get('form_guide', []):
            form_data.append([
                horse.get('Horse', 'Unknown'),
                horse.get('Barrier', 'Unknown'),
                horse.get('Weight', 'Unknown'),
                horse.get('Jockey', 'Unknown'),
                horse.get('Form', 'Unknown'),
                horse.get('Rating', 'Unknown')
            ])
        
        t = Table(form_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        
        # Build PDF
        doc.build(elements)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return b''
