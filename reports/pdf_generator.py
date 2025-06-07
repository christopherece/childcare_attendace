from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from datetime import datetime
import requests
from io import BytesIO

def generate_attendance_pdf(attendances, selected_date, room_name, center_name="Childcare Center"):
    try:
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="attendance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        page_width, page_height = A4
        
        # Margins
        left_margin = 30
        right_margin = page_width - 30
        top_margin = page_height - 40
        bottom_margin = 40

        # === LOGO ===
        image_url = "https://topitsolutions.co.nz/static/images/logos/it_logo2.png"
        try:
            img_response = requests.get(image_url)
            if img_response.status_code == 200:
                logo_data = BytesIO(img_response.content)
                logo_data.seek(0)
                p.drawImage(logo_data, left_margin, top_margin - 45, width=80, height=35, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print("Failed to load logo:", e)

        # === HEADER TEXT ===
        p.setFont("Helvetica-Bold", 20)
        p.setFillColorRGB(0, 0, 0)
        p.drawCentredString(page_width / 2, top_margin - 10, center_name)

        p.setFont("Helvetica-Bold", 16)
        p.drawCentredString(page_width / 2, top_margin - 35, "Attendance Report")

        p.setFont("Helvetica", 12)
        p.setFillColorRGB(0.2, 0.2, 0.2)
        p.drawCentredString(
            page_width / 2,
            top_margin - 55,
            f"Report Date: {selected_date if selected_date else 'Today'} | Room: {room_name}"
        )

        # === HORIZONTAL LINE ===
        p.setStrokeColorRGB(0, 0, 0)
        p.setLineWidth(1)
        p.line(left_margin, top_margin - 70, right_margin, top_margin - 70)

        # === TABLE DATA ===
        data = [['Child Name', 'Parent', 'Sign In', 'Sign Out', 'Notes']]
        for a in attendances:
            child = a.get('child', {})
            data.append([
                child.get('name', 'N/A'),
                child.get('parent', {}).get('name', 'No Parent'),
                a.get('sign_in_time', '-'),
                a.get('sign_out_time', '-'),
                a.get('notes', '-')
            ])

        # Calculate evenly distributed column widths
        usable_width = page_width - left_margin - (page_width - right_margin)
        col_width = usable_width / 5

        table = Table(data, colWidths=[col_width] * 5)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6)
        ]))

        # Position the table closer to the header
        table_x = left_margin
        table_y = top_margin - 280

        table.wrapOn(p, 0, 0)
        table.drawOn(p, table_x, table_y)

        # === FOOTER ===
        footer_y = bottom_margin + 10
        p.setFont("Helvetica", 10)
        p.setFillColorRGB(0.33, 0.33, 0.33)
        p.drawString(left_margin, footer_y, f"Page {p.getPageNumber()}")
        p.drawRightString(right_margin, footer_y, "2025 ChildCare App | childcare.topitsolutions.co.nz")

        p.save()
        return response

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return HttpResponse("Error generating PDF", status=500)