import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from django.conf import settings
import gpxpy
import gpxpy.gpx
from datetime import datetime


def generate_route_pdf(route, waypoints):
    """Генерация PDF-документа для маршрута"""
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        textColor=colors.HexColor('#2C3E50')
    ))

    styles.add(ParagraphStyle(
        name='WaypointTitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1ABC9C'),
        spaceAfter=12
    ))

    # Собираем элементы документа
    story = []

    # Заголовок
    title = Paragraph(f"Маршрут: {route.title}", styles['CustomTitle'])
    story.append(title)

    # Основная информация
    story.append(Paragraph(f"<b>Тематика:</b> {route.get_theme_display()}", styles['Normal']))
    story.append(Paragraph(f"<b>Длительность:</b> {route.duration_hours} часов", styles['Normal']))
    story.append(Paragraph(f"<b>Тип транспорта:</b> {route.get_transport_type_display()}", styles['Normal']))

    if route.price:
        story.append(Paragraph(f"<b>Стоимость:</b> {route.price} руб.", styles['Normal']))

    story.append(Spacer(1, 20))

    # Описание маршрута
    story.append(Paragraph("<b>Описание маршрута:</b>", styles['Heading2']))
    story.append(Paragraph(route.description, styles['Normal']))
    story.append(Spacer(1, 20))

    # Точки маршрута
    story.append(Paragraph("<b>Точки маршрута:</b>", styles['Heading2']))

    for waypoint in waypoints:
        # Заголовок точки
        waypoint_title = Paragraph(
            f"{waypoint.order}. {waypoint.name} ({waypoint.get_waypoint_type_display()})",
            styles['WaypointTitle']
        )
        story.append(waypoint_title)

        # Описание точки
        if waypoint.short_description:
            story.append(Paragraph(waypoint.short_description, styles['Normal']))

        # Дополнительная информация
        info_lines = []
        if waypoint.estimated_stay_minutes:
            info_lines.append(f"Время на посещение: {waypoint.estimated_stay_minutes} мин")
        if waypoint.difficulty != 'easy':
            info_lines.append(f"Сложность: {waypoint.get_difficulty_display()}")

        if info_lines:
            story.append(Paragraph("<br/>".join(info_lines), styles['Normal']))

        story.append(Spacer(1, 10))

    # Практическая информация
    story.append(Paragraph("<b>Практическая информация:</b>", styles['Heading2']))

    practical_info = []
    if route.need_food_supply:
        practical_info.append("• Рекомендуется взять запас еды и воды")
    if route.max_participants:
        practical_info.append(f"• Рекомендуемое количество участников: до {route.max_participants} человек")

    if practical_info:
        story.append(Paragraph("<br/>".join(practical_info), styles['Normal']))

    # Время создания
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"<i>Документ создан: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>",
        styles['Italic']
    ))

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
            description=waypoint.short_description,
            type=waypoint.get_waypoint_type_display()
        )
        gpx.waypoints.append(gpx_waypoint)

        # Добавляем точку в трек
        gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(
                latitude=waypoint.latitude,
                longitude=waypoint.longitude,
                name=f"{waypoint.order}. {waypoint.name}"
            )
        )

    return gpx.to_xml()