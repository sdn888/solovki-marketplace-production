from django import forms
from .models import PersonalRoute


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