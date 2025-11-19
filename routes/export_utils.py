import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings
import gpxpy
import gpxpy.gpx
from datetime import datetime


# Регистрируем шрифт с поддержкой кириллицы
def register_fonts():
    """Регистрация шрифтов с поддержкой кириллицы"""
    try:
        # Попробуем использовать стандартные системные шрифты
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
        return 'DejaVuSans'
    except:
        try:
            # Альтернативный шрифт
            pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
            pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
            return 'Arial'
        except:
            # Если шрифты не найдены, используем стандартные (могут не поддерживать кириллицу)
            return 'Helvetica'


def generate_route_pdf(route, waypoints):
    """Генерация PDF-документа для маршрута с поддержкой кириллицы"""
    buffer = BytesIO()

    # Регистрируем шрифты
    font_name = register_fonts()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()

    # Создаем стили с поддержкой кириллицы
    title_style = ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontName=f'{font_name}-Bold' if font_name != 'Helvetica' else 'Helvetica-Bold',
        fontSize=16,
        spaceAfter=30,
        textColor=colors.HexColor('#2C3E50'),
        alignment=1  # Center
    )

    heading_style = ParagraphStyle(
        name='CustomHeading',
        parent=styles['Heading2'],
        fontName=f'{font_name}-Bold' if font_name != 'Helvetica' else 'Helvetica-Bold',
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#1ABC9C')
    )

    normal_style = ParagraphStyle(
        name='CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        spaceAfter=6,
        textColor=colors.black
    )

    waypoint_style = ParagraphStyle(
        name='WaypointTitle',
        parent=styles['Heading3'],
        fontName=f'{font_name}-Bold' if font_name != 'Helvetica' else 'Helvetica-Bold',
        fontSize=11,
        textColor=colors.HexColor('#3498DB'),
        spaceAfter=6,
        leftIndent=0
    )

    # Собираем элементы документа
    story = []

    # Заголовок
    title = Paragraph(f"МАРШРУТ: {route.title}", title_style)
    story.append(title)

    # Разделитель
    story.append(Spacer(1, 10))

    # Основная информация в таблице
    route_info = [
        ['<b>Тематика</b>', route.get_theme_display()],
        ['<b>Длительность</b>', f"{route.duration_hours} часов"],
        ['<b>Тип транспорта</b>', route.get_transport_type_display()],
    ]

    if route.price:
        route_info.append(['<b>Стоимость</b>', f"{route.price} руб."])

    route_info.append(['<b>Участники</b>', f"до {route.max_participants} человек"])

    if route.need_food_supply:
        route_info.append(['<b>Питание</b>', 'Рекомендуется взять запас еды'])

    info_table = Table(route_info, colWidths=[4 * cm, 10 * cm])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), font_name, 9),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    story.append(info_table)
    story.append(Spacer(1, 20))

    # Описание маршрута
    story.append(Paragraph("ОПИСАНИЕ МАРШРУТА", heading_style))
    story.append(Paragraph(route.description, normal_style))
    story.append(Spacer(1, 20))

    # Точки маршрута
    story.append(Paragraph("ТОЧКИ МАРШРУТА", heading_style))

    for waypoint in waypoints:
        # Заголовок точки
        waypoint_header = f"{waypoint.order}. {waypoint.name} ({waypoint.get_waypoint_type_display()})"
        story.append(Paragraph(waypoint_header, waypoint_style))

        # Описание точки
        if waypoint.short_description:
            story.append(Paragraph(waypoint.short_description, normal_style))

        # Дополнительная информация
        info_text = []
        if waypoint.estimated_stay_minutes:
            info_text.append(f"<b>Время на посещение:</b> {waypoint.estimated_stay_minutes} мин")
        if waypoint.difficulty != 'easy':
            info_text.append(f"<b>Сложность:</b> {waypoint.get_difficulty_display()}")

        if waypoint.has_food:
            info_text.append("<b>Питание:</b> есть")
        if waypoint.has_parking:
            info_text.append("<b>Парковка:</b> есть")
        if waypoint.is_wheelchair_accessible:
            info_text.append("<b>Доступность:</b> для инвалидных колясок")

        if info_text:
            story.append(Paragraph(" • ".join(info_text), normal_style))

        # Подробное описание (если есть)
        if waypoint.detailed_description:
            story.append(Paragraph(waypoint.detailed_description, normal_style))

        story.append(Spacer(1, 15))

    # Советы (если есть)
    if hasattr(route, 'tips') and route.tips.exists():
        story.append(Paragraph("СОВЕТЫ ПО МАРШРУТУ", heading_style))
        for tip in route.tips.all().order_by('order'):
            story.append(Paragraph(f"<b>{tip.title}</b>", normal_style))
            story.append(Paragraph(tip.description, normal_style))
            story.append(Spacer(1, 10))

    # Время создания
    story.append(Spacer(1, 20))
    created_time = datetime.now().strftime('%d.%m.%Y %H:%M')
    story.append(Paragraph(f"<i>Документ создан: {created_time}</i>", normal_style))
    story.append(Paragraph("<i>Источник: Solovki Marketplace</i>", normal_style))

    # Создаем PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_route_gpx(route, waypoints):
    """Генерация GPX-файла для маршрута"""
    gpx = gpxpy.gpx.GPX()

    # Метаданные маршрута
    gpx.name = route.title
    gpx.description = route.description
    gpx.author_name = "Solovki Marketplace"
    gpx.time = datetime.now()

    # Создаем трек
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = route.title
    gpx.tracks.append(gpx_track)

    # Создаем сегмент трека
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Добавляем точки маршрута как путевые точки
    for waypoint in waypoints:
        gpx_waypoint = gpxpy.gpx.GPXWaypoint(
            latitude=waypoint.latitude,
            longitude=waypoint.longitude,
            name=f"{waypoint.order}. {waypoint.name}",
            description=waypoint.short_description or waypoint.name,
            type=waypoint.get_waypoint_type_display()
        )
        gpx.waypoints.append(gpx_waypoint)

        # Добавляем точку в трек
        gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(
                latitude=waypoint.latitude,
                longitude=waypoint.longitude
            )
        )

    return gpx.to_xml()