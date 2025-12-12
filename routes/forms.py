from django import forms
from .models import Route, Waypoint


class CoordinateFloatField(forms.FloatField):
    def to_python(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace(',', '.')
        return super().to_python(value)


class WaypointForm(forms.ModelForm):
    latitude = CoordinateFloatField(
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '64.0245'})
    )
    longitude = CoordinateFloatField(
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '35.7105'})
    )

    class Meta:
        model = Waypoint
        # ИЗМЕНЯЕМ: убираем exclude, явно указываем поля, включая order
        fields = [
            'order', 'name', 'waypoint_type', 'latitude', 'longitude', 'altitude',
            'short_description', 'detailed_description', 'history_info', 'architecture_info',
            'visit_notes', 'path_description', 'best_time_to_visit', 'difficulty',
            'estimated_stay_minutes', 'has_food', 'has_toilets', 'has_parking',
            'is_wheelchair_accessible', 'is_optional'
        ]
        widgets = {
            'order': forms.NumberInput(attrs={'class': 'form-control', 'step': 1}),
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
        }
        help_texts = {
            'short_description': 'Отображается в карточках и списках (до 1000 символов)',
            'detailed_description': 'Полное описание для страницы точки маршрута',
            'latitude': 'Широта в формате 64.0245',
            'longitude': 'Долгота в формате 35.7105',
            'order': 'Порядковый номер точки в маршруте',
        }


class RouteForm(forms.ModelForm):
    start_lat = CoordinateFloatField(
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '64.0345'})
    )
    start_lon = CoordinateFloatField(
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '35.7105'})
    )
    end_lat = CoordinateFloatField(
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '64.0345'})
    )
    end_lon = CoordinateFloatField(
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.000001', 'placeholder': '35.7105'})
    )

    class Meta:
        model = Route
        # ЗАМЕНЯЕМ fields = '__all__' на явный список, исключая служебные поля
        fields = [
            'title', 'description', 'theme', 'transport_type',
            'duration_hours', 'price', 'need_food_supply',
            'max_participants', 'is_active',
            'start_lat', 'start_lon', 'end_lat', 'end_lon',
            # НОВЫЕ ПОЛЯ для системы ролей:
            'status', 'access_level', 'is_premium'
        ]
        widgets = {
            # СУЩЕСТВУЮЩИЕ виджеты остаются
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'theme': forms.Select(attrs={'class': 'form-control'}),
            'transport_type': forms.Select(attrs={'class': 'form-control'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            # НОВЫЕ виджеты для дополнительных полей
            'status': forms.Select(attrs={'class': 'form-control'}),
            'access_level': forms.Select(attrs={'class': 'form-control'}),
            'is_premium': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'need_food_supply': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'start_lat': 'Широта начала маршрута (отель "Морюшко")',
            'start_lon': 'Долгота начала маршрута',
            # НОВЫЕ подсказки
            'status': 'Статус видимости маршрута',
            'access_level': 'Уровень доступа к маршруту',
            'is_premium': 'Премиум маршруты доступны только подписчикам',
        }
        labels = {
            'is_premium': 'Премиум маршрут',
            'access_level': 'Уровень доступа',
            'status': 'Статус публикации',
        }

    def __init__(self, *args, **kwargs):
        # Извлекаем пользователя из kwargs если передан
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Настраиваем начальные значения для новых полей
        if not self.instance.pk:  # Если это создание нового маршрута
            self.fields['status'].initial = 'draft'
            self.fields['access_level'].initial = 'public'
            self.fields['is_premium'].initial = False

        # Ограничиваем выбор статуса для обычных пользователей
        if self.user and self.user.role not in ['admin', 'expert_guide']:
            # Обычные гиды могут выбирать только черновик или отправлять на модерацию
            self.fields['status'].choices = [
                ('draft', 'Черновик'),
                ('pending', 'Отправить на модерацию'),
            ]

    def clean(self):
        cleaned_data = super().clean()
        is_premium = cleaned_data.get('is_premium')
        access_level = cleaned_data.get('access_level')

        # Проверяем, что премиум маршруты имеют соответствующий уровень доступа
        if is_premium and access_level != 'premium':
            self.add_error('access_level', 'Премиум маршруты должны иметь уровень доступа "Только для премиум"')

        return cleaned_data