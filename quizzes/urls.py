from django.urls import path
from . import views

app_name = "quizzes"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("create/", views.create_quiz, name="create_quiz"),
    path("quiz/<int:quiz_id>/edit/", views.edit_quiz, name="edit_quiz"),
    path("quiz/<int:quiz_id>/delete/", views.delete_quiz, name="delete_quiz"),
    path(
        "quiz/<int:quiz_id>/attempts/",
        views.quiz_attempt_history,
        name="quiz_attempt_history",
    ),
    path("quiz/<int:quiz_id>/add-question/", views.add_question, name="add_question"),
    path("quiz/<int:quiz_id>/", views.quiz_detail, name="quiz_detail"),
    path("quiz/<int:quiz_id>/publish/", views.publish_quiz, name="publish_quiz"),
    path("explore/", views.explore_quizzes, name="explore_quizzes"),
    path("quiz/<int:quiz_id>/attempt/", views.take_quiz, name="take_quiz"),
    path(
        "attempt/<int:attempt_id>/result/", views.attempt_result, name="attempt_result"
    ),
    path("attempt-history/", views.attempt_history, name="attempt_history"),
    path(
        "question/<int:question_id>/edit/",
        views.edit_question,
        name="edit_question",
    ),
    path(
        "question/<int:question_id>/delete/",
        views.delete_question,
        name="delete_question",
    ),
    path(
        "attempt/<int:attempt_id>/save-answer/",
        views.save_quiz_answer,
        name="save_quiz_answer",
    ),
]
