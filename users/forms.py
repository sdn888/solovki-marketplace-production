from django import forms
from .models import PersonalRoute
from .models import VisitNote, Waypoint, VisitNoteImage
from django.utils import timezone
from routes.models import Waypoint, WaypointImage
from routes.forms import CoordinateFloatField


class PersonalRouteForm(forms.ModelForm):
    class Meta:
        model = PersonalRoute
        fields = ['title', 'description', 'color', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Например: Мой идеальный тур по Соловкам'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Расскажите о вашем маршруте...'
            }),
            'color': forms.HiddenInput(),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убедимся, что поле color использует правильные choices
        self.fields['color'].choices = PersonalRoute.COLOR_CHOICES


class VisitNoteForm(forms.ModelForm):
    class Meta:
        model = VisitNote
        fields = ['waypoint', 'visit_date', 'rating', 'notes', 'photos']
        widgets = {
            'visit_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'Выберите дату посещения'
            }),
            'rating': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': 'Расскажите о вашем посещении: впечатления, советы, особенности...'
            }),
            'waypoint': forms.Select(attrs={
                'class': 'form-control'
            }),
            'photos': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'visit_date': 'Дата посещения *',
            'rating': 'Ваша оценка *',
            'notes': 'Заметки и впечатления',
            'photos': 'Фотографии с посещения'
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Ограничиваем выбор только активными точками маршрутов
        self.fields['waypoint'].queryset = Waypoint.objects.filter(
            route__is_active=True
        ).select_related('route').order_by('route__title', 'order')

        # Добавляем пустой вариант
        self.fields['waypoint'].empty_label = "Выберите точку маршрута"

        # Делаем поля обязательными
        self.fields['visit_date'].required = True
        self.fields['rating'].required = True
        self.fields['waypoint'].required = True

    def clean_visit_date(self):
        visit_date = self.cleaned_data.get('visit_date')
        if visit_date and visit_date > timezone.now().date():
            raise forms.ValidationError("Дата посещения не может быть в будущем")
        return visit_date


# users/forms.py - ИСПРАВЛЕННЫЕ МЕТОДЫ clean_latitude и clean_longitude

class UserWaypointForm(forms.ModelForm):
    """Форма для создания/редактирования точки пользователем"""
    latitude = CoordinateFloatField(
        widget=forms.NumberInput(attrs={
            'step': '0.000001',
            'placeholder': '64.0245',
            'class': 'form-control'
        }),
        label='Широта'
    )

    longitude = CoordinateFloatField(
        widget=forms.NumberInput(attrs={
            'step': '0.000001',
            'placeholder': '35.7105',
            'class': 'form-control'
        }),
        label='Долгота'
    )

    class Meta:
        model = Waypoint
        fields = [
            'name', 'waypoint_type', 'latitude', 'longitude', 'altitude',
            'short_description', 'detailed_description', 'history_info',
            'architecture_info', 'visit_notes', 'path_description',
            'best_time_to_visit', 'difficulty', 'estimated_stay_minutes',
            'has_food', 'has_toilets', 'has_parking',
            'is_wheelchair_accessible', 'is_optional'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'waypoint_type': forms.Select(attrs={'class': 'form-control'}),
            'altitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Краткое описание для карточек и списков'
            }),
            'detailed_description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Полное описание достопримечательности'
            }),
            'history_info': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Исторические факты и даты'
            }),
            'architecture_info': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Архитектурные особенности'
            }),
            'visit_notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Особенности посещения'
            }),
            'path_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Как добраться до точки'
            }),
            'best_time_to_visit': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Лучшее время для посещения'
            }),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'estimated_stay_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_latitude(self):
        latitude = self.cleaned_data.get('latitude')
        if latitude is not None:
            # ИСПРАВЛЕНО: правильный диапазон широты для Соловков
            if latitude < 63.5 or latitude > 65.5:
                raise forms.ValidationError(
                    "Широта должна быть в диапазоне 63.5 - 65.5 для Соловецких островов. "
                    "Типичные значения: 64.0 - 65.0"
                )
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get('longitude')
        if longitude is not None:
            # ИСПРАВЛЕНО: правильный диапазон долготы для Соловков
            if longitude < 34.5 or longitude > 36.5:
                raise forms.ValidationError(
                    "Долгота должна быть в диапазоне 34.5 - 36.5 для Соловецких островов. "
                    "Типичные значения: 35.0 - 36.0"
                )
        return longitude


class UserWaypointImageForm(forms.ModelForm):
    """Форма для загрузки изображений к точке"""
    class Meta:
        model = WaypointImage
        fields = ['image', 'caption', 'order', 'is_primary']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'caption': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Описание фотографии'
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }