from django import forms
from django.db import models
from .models import Waypoint


class CoordinateFloatField(forms.FloatField):
    def to_python(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace(',', '.')
        return super().to_python(value)


class GuideWaypointForm(forms.ModelForm):
    """Форма для создания/редактирования точек маршрута гидами"""
    latitude = CoordinateFloatField(
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '64.0245', 'class': 'form-control'})
    )
    longitude = CoordinateFloatField(
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '35.7105', 'class': 'form-control'})
    )

    class Meta:
        model = Waypoint
        fields = [
            'order', 'name', 'waypoint_type', 'latitude', 'longitude', 'altitude',
            'short_description', 'detailed_description', 'history_info', 'architecture_info',
            'visit_notes', 'path_description', 'best_time_to_visit', 'difficulty',
            'estimated_stay_minutes', 'has_food', 'has_toilets', 'has_parking',
            'is_wheelchair_accessible', 'is_optional'
        ]
        widgets = {
            'order': forms.HiddenInput(),  # Делаем поле скрытым
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'waypoint_type': forms.Select(attrs={'class': 'form-control'}),
            'altitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Краткое описание, которое будет показываться в списках и карточках',
                'class': 'form-control'
            }),
            'detailed_description': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Полное и подробное описание достопримечательности',
                'class': 'form-control'
            }),
            'history_info': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Исторические факты, даты, значимые события',
                'class': 'form-control'
            }),
            'architecture_info': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Архитектурные особенности, стиль, материалы',
                'class': 'form-control'
            }),
            'visit_notes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Особенности посещения, рекомендации, что учесть',
                'class': 'form-control'
            }),
            'path_description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Как добраться, описание пути, ориентиры',
                'class': 'form-control'
            }),
            'best_time_to_visit': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Лучшее время года, время суток, погодные условия',
                'class': 'form-control'
            }),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'estimated_stay_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'has_food': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_toilets': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_parking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_wheelchair_accessible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_optional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'short_description': 'Отображается в карточках и списках (до 1000 символов)',
            'detailed_description': 'Полное описание для страницы точки маршрута',
            'latitude': 'Широта в формате 64.0245',
            'longitude': 'Долгота в формате 35.7105',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # route теперь передается через атрибут формы после создания

    def clean_order(self):
        """Валидация поля order"""
        order = self.cleaned_data.get('order')

        # Если поле пустое и у нас есть маршрут, вычисляем автоматически
        if not order and hasattr(self, 'route') and self.route:
            max_order = self.route.waypoints.aggregate(models.Max('order'))['order__max']
            order = (max_order or 0) + 1

        return order

    # ДОБАВЛЯЕМ ВАЛИДАЦИЮ КООРДИНАТ ДЛЯ СОЛОВКОВ
    def clean_latitude(self):
        """Валидация широты для Соловецких островов"""
        latitude = self.cleaned_data.get('latitude')
        if latitude is not None:
            # Правильный диапазон для Соловков
            if latitude < 63.5 or latitude > 65.5:
                raise forms.ValidationError(
                    "Широта должна быть в диапазоне 63.5 - 65.5 для Соловецких островов. "
                    "Типичные значения: 64.0 - 65.0"
                )
        return latitude

    def clean_longitude(self):
        """Валидация долготы для Соловецких островов"""
        longitude = self.cleaned_data.get('longitude')
        if longitude is not None:
            # Правильный диапазон для Соловков
            if longitude < 34.5 or longitude > 36.5:
                raise forms.ValidationError(
                    "Долгота должна быть в диапазоне 34.5 - 36.5 для Соловецких островов. "
                    "Типичные значения: 35.0 - 36.0"
                )
        return longitude