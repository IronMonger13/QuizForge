from django import forms
from django.forms import formset_factory

from .models import Quiz, Question, Choice


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


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["question_text", "marks"]
        widgets = {
            "question_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter your question",
                    "rows": 3,
                }
            ),
            "marks": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "value": 1}
            ),
        }
        labels = {"question_text": "Question", "marks": "Marks"}


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ["choice_text", "is_correct"]
        widgets = {
            "choice_text": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter an answer choice"}
            ),
            "is_correct": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {"choice_text": "Answer Choice", "is_correct": "Correct Answer"}


ChoiceFormSet = formset_factory(
    ChoiceForm, extra=4, min_num=4, max_num=4, validate_min=True, validate_max=True
)
