from django import forms
from .models import PersonalRoute
from .models import VisitNote, Waypoint, VisitNoteImage
from django.utils import timezone

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
    photos = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control'
        }),
        label="Фотографии с посещения"
    )

    class Meta:
        model = VisitNote
        fields = ['waypoint', 'visit_date', 'rating', 'notes', 'photos']  # Вернули photos
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
        }
        labels = {
            'visit_date': 'Дата посещения *',
            'rating': 'Ваша оценка *',
            'notes': 'Заметки и впечатления',
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

    def save(self, commit=True):
        # Сохраняем основную заметку
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user

        if commit:
            instance.save()

            # ВРЕМЕННО: сохраняем только первое фото для обратной совместимости
            photos = self.files.getlist('photos')
            if photos:
                # Сохраняем первое фото в основное поле photos
                instance.photos = photos[0]
                instance.save()

                # Дополнительные фото пока не сохраняем
                # for i, photo in enumerate(photos[1:], start=1):
                #     VisitNoteImage.objects.create(
                #         visit_note=instance,
                #         image=photo,
                #         order=i
                #     )

        return instance
