from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        # fields = ['movie_title', 'feedback_text']
        fields = ['user_feedback']
        widgets = {
            'movie_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter movie title'}),
            'feedback_text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter your feedback'}),
        }
# app/forms.py
