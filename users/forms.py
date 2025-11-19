from django import forms
from .models import PersonalRoute
from .models import VisitNote

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
                'class': 'form-control'
            }),
            'rating': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Расскажите о вашем посещении...'
            }),
            'waypoint': forms.HiddenInput(),  # Скрытое поле, так как точка будет определяться из контекста
        }
        labels = {
            'visit_date': 'Дата посещения',
            'rating': 'Оценка',
            'notes': 'Заметки',
            'photos': 'Фотографии'
        }
