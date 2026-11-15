from django.conf import settings
from django.db import models


# Create your models here.
class Category(models.Model):

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Quiz(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quizzes"
    )

    category = models.ForeignKey(
        "Category", on_delete=models.PROTECT, related_name="quizzes"
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    time_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time limit in minutes. Leave empty for no time limit.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Question(models.Model):

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")

    question_text = models.TextField()

    marks = models.PositiveIntegerField(default=1)

    order = models.PositiveIntegerField(
        help_text="Position of this question within the quiz."
    )

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "order"], name="unique_question_order_per_quiz"
            )
        ]

    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"
