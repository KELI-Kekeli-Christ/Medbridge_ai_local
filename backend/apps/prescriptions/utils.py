import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.platypus.flowables import KeepTogether

# ─── Enregistrement des polices Unicode (support Ewe : ŋ ɖ ɔ ƒ ʊ ...) ────────
_FONTS_REGISTERED = False

def _register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    import os
    candidates = [
        # DejaVu (pré-installé sur Ubuntu/Debian)
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        # Noto Sans (fallback)
        ('/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
         '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf'),
        # FreeSans (fallback)
        ('/usr/share/fonts/truetype/freefont/FreeSans.ttf',
         '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'),
    ]
    for regular, bold in candidates:
        if os.path.exists(regular):
            pdfmetrics.registerFont(TTFont('MedBridgeFont', regular))
            if os.path.exists(bold):
                pdfmetrics.registerFont(TTFont('MedBridgeFont-Bold', bold))
            else:
                pdfmetrics.registerFont(TTFont('MedBridgeFont-Bold', regular))
            _FONTS_REGISTERED = True
            return
    # Aucune police TTF trouvée — fallback Helvetica (caractères Ewe incorrects)
    _FONTS_REGISTERED = True


def _styles():
    _register_fonts()
    font = 'MedBridgeFont' if _FONTS_REGISTERED else 'Helvetica'
    font_bold = 'MedBridgeFont-Bold' if _FONTS_REGISTERED else 'Helvetica-Bold'

    return {
        'title': ParagraphStyle(
            'MBTitle',
            fontName=font_bold,
            fontSize=16,
            textColor=colors.HexColor('#1a3c5e'),
            spaceAfter=6,
            leading=20,
        ),
        'section': ParagraphStyle(
            'MBSection',
            fontName=font_bold,
            fontSize=12,
            textColor=colors.HexColor('#2d7dd2'),
            spaceBefore=12,
            spaceAfter=4,
            leading=16,
        ),
        'body': ParagraphStyle(
            'MBBody',
            fontName=font,
            fontSize=10,
            textColor=colors.HexColor('#222222'),
            leading=16,
            spaceAfter=2,
        ),
        'meta': ParagraphStyle(
            'MBMeta',
            fontName=font,
            fontSize=8,
            textColor=colors.HexColor('#888888'),
            leading=12,
        ),
        'label': ParagraphStyle(
            'MBLabel',
            fontName=font_bold,
            fontSize=9,
            textColor=colors.HexColor('#555555'),
            leading=13,
            spaceAfter=1,
        ),
    }


def _white_background(canvas, doc):
    """Dessine un fond blanc explicite sur chaque page."""
    canvas.saveState()
    canvas.setFillColor(colors.white)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.restoreState()


def generate_prescription_pdf(prescription) -> io.BytesIO:
    """Génère un PDF bilingue (version médecin + version patient) avec support Unicode."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    s = _styles()
    story = []

    # ── En-tête ──────────────────────────────────────────────────────────────
    story.append(Paragraph("MedBridge — Ordonnance Médicale", s['title']))
    story.append(Paragraph(
        f"ID : {prescription.prescription_id}  |  "
        f"Date : {prescription.created_at.strftime('%d/%m/%Y %H:%M')}",
        s['meta'],
    ))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2d7dd2')))
    story.append(Spacer(1, 0.4 * cm))

    # ── Informations patient ──────────────────────────────────────────────────
    patient = getattr(prescription, 'patient_info', None)
    if patient:
        patient_lines = []
        if patient.get('last_name') or patient.get('first_name'):
            name = f"{patient.get('last_name', '')} {patient.get('first_name', '')}".strip()
            patient_lines.append(f"Patient : {name}")
        if patient.get('age'):
            patient_lines.append(f"Âge : {patient['age']}")
        if patient_lines:
            story.append(Paragraph("  |  ".join(patient_lines), s['body']))
            story.append(Spacer(1, 0.3 * cm))

    # ── Version médicale ──────────────────────────────────────────────────────
    story.append(Paragraph("Version Médicale (Médecin)", s['section']))
    doctor_text = getattr(prescription, 'doctor_text', '') or ''
    for line in doctor_text.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), s['body']))
    story.append(Spacer(1, 0.6 * cm))

    # ── Séparateur ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
    story.append(Spacer(1, 0.4 * cm))

    # ── Version patient (langue locale avec caractères Ewe/Arabe) ────────────
    story.append(Paragraph("Version Patient (Langue locale)", s['section']))
    patient_text = getattr(prescription, 'patient_text', '') or ''
    if patient_text.strip():
        for line in patient_text.split('\n'):
            if line.strip():
                story.append(Paragraph(line.strip(), s['body']))
    else:
        story.append(Paragraph("Version patient non générée.", s['meta']))

    # ── Pied de page ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc')))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Document généré automatiquement par MedBridge AI — "
        "Université d’Avignon. "
        "Ce document expire 24h après sa création.",
        s['meta'],
    ))

    doc.build(story, onFirstPage=_white_background, onLaterPages=_white_background)
    return buffer
