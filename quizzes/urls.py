from django.urls import path
from . import views

app_name = "quizzes"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("create/", views.create_quiz, name="create_quiz"),
]
