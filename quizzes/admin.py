from django.contrib import admin

from .models import Category, Quiz, Question, Choice, QuizAttempt, AttemptAnswer


# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "category", "status", "created_at")
    list_filter = ("status", "category", "created_at")
    search_fields = ("title", "description", "owner__username")
    ordering = ("-created_at",)

    def has_change_permission(self, request, obj=None):
        if obj and obj.attempts.exists():
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.attempts.exists():
            return False
        return super().has_delete_permission(request, obj)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    max_num = 4

    def has_add_permission(self, request, obj=None):
        if obj and obj.quiz.attempts.exists():
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.quiz.attempts.exists():
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.quiz.attempts.exists():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "quiz", "marks", "order")
    list_filter = ("quiz",)
    search_fields = ("question_text", "quiz__title")
    ordering = ("quiz", "order")
    inlines = [ChoiceInline]

    def has_change_permission(self, request, obj=None):
        if obj and obj.quiz.attempts.exists():
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.quiz.attempts.exists():
            return False
        return super().has_delete_permission(request, obj)


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    readonly_fields = ("question", "selected_choice", "is_correct", "marks_awarded")
    can_delete = False


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "quiz",
        "score",
        "total_marks",
        "status",
        "started_at",
        "completed_at",
    )
    list_filter = ("status", "started_at", "completed_at")
    search_fields = ("user__username", "quiz__title")
    ordering = ("-started_at",)
    inlines = [AttemptAnswerInline]

    def has_change_permission(self, request, obj=None):
        if obj and obj.status == QuizAttempt.Status.COMPLETED:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == QuizAttempt.Status.COMPLETED:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    list_display = (
        "attempt",
        "question",
        "selected_choice",
        "is_correct",
        "marks_awarded",
    )
    list_filter = ("is_correct",)
    search_fields = ("attempt__user__username", "question__question_text")

    def has_change_permission(self, request, obj=None):
        if obj and obj.attempt.status == QuizAttempt.Status.COMPLETED:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.attempt.status == QuizAttempt.Status.COMPLETED:
            return False
        return super().has_delete_permission(request, obj)
