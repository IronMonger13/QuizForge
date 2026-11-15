from django import forms

from .models import Quiz


class QuizForm(forms.ModelForm):

    class Meta:
        model = Quiz

        fields = ["title", "description", "category", "time_limit"]

        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter your quiz title"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Describe what your quiz is about",
                    "rows": 4,
                }
            ),
            "category": forms.Select(attrs={"class": "form-select"}),
            "time_limit": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter time limit in minutes",
                    "min": 1,
                }
            ),
        }

        labels = {
            "title": "Quiz Title",
            "description": "Description",
            "category": "Category",
            "time_limit": "Time Limit (Minutes)",
        }

        help_texts = {"time_limit": "Leave empty if your quiz has no time limit."}
