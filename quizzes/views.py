from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Count
from django.views.decorators.http import require_POST
from django.utils import timezone

from .forms import QuizForm, QuestionForm, ChoiceFormSet
from .models import Quiz, Question, QuizAttempt, AttemptAnswer


# Create your views here.
@login_required
def dashboard(request):
    my_quizzes = (
        Quiz.objects.filter(owner=request.user)
        .select_related("category")
        .annotate(question_count=Count("questions"))
    )
    return render(request, "quizzes/dashboard.html", {"my_quizzes": my_quizzes})


@login_required
def create_quiz(request):
    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.owner = request.user
            quiz.status = Quiz.Status.DRAFT
            quiz.save()
            return redirect("quizzes:quiz_detail", quiz_id=quiz.id)
    else:
        form = QuizForm()
    return render(request, "quizzes/create_quiz.html", {"form": form})


@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(
        Quiz, id=quiz_id, owner=request.user, status=Quiz.Status.DRAFT
    )
    if request.method == "POST":
        question_form = QuestionForm(request.POST)
        choice_formset = ChoiceFormSet(request.POST)
        if question_form.is_valid() and choice_formset.is_valid():
            correct_choices = [
                form for form in choice_formset if form.cleaned_data.get("is_correct")
            ]
            if len(correct_choices) != 1:
                return render(
                    request,
                    "quizzes/add_question.html",
                    {
                        "quiz": quiz,
                        "question_form": question_form,
                        "choice_formset": choice_formset,
                        "correct_answer_error": (
                            "Please select exactly one correct answer."
                        ),
                    },
                )
            with transaction.atomic():
                question = question_form.save(commit=False)
                question.quiz = quiz
                question.order = quiz.questions.count() + 1
                question.save()
                for choice_form in choice_formset:
                    choice = choice_form.save(commit=False)
                    choice.question = question
                    choice.order = choice_formset.forms.index(choice_form) + 1
                    choice.save()
            return redirect("quizzes:quiz_detail", quiz_id=quiz.id)
    else:
        question_form = QuestionForm()
        choice_formset = ChoiceFormSet()
    return render(
        request,
        "quizzes/add_question.html",
        {
            "quiz": quiz,
            "question_form": question_form,
            "choice_formset": choice_formset,
        },
    )


@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, owner=request.user)
    questions = quiz.questions.prefetch_related("choices")
    return render(
        request, "quizzes/quiz_detail.html", {"quiz": quiz, "questions": questions}
    )


@login_required
@require_POST
def publish_quiz(request, quiz_id):
    quiz = get_object_or_404(
        Quiz, id=quiz_id, owner=request.user, status=Quiz.Status.DRAFT
    )
    questions = quiz.questions.prefetch_related("choices")
    if not questions.exists():
        return render(
            request,
            "quizzes/quiz_detail.html",
            {
                "quiz": quiz,
                "questions": questions,
                "publish_error": "Add at least one question before publishing.",
            },
        )
    for question in questions:
        choices = question.choices.all()
        if choices.count() != 4:
            return render(
                request,
                "quizzes/quiz_detail.html",
                {
                    "quiz": quiz,
                    "questions": questions,
                    "publish_error": (
                        f"Question {question.order} must have exactly four choices."
                    ),
                },
            )
        if choices.filter(is_correct=True).count() != 1:
            return render(
                request,
                "quizzes/quiz_detail.html",
                {
                    "quiz": quiz,
                    "questions": questions,
                    "publish_error": (
                        f"Question {question.order} must have exactly one correct answer."
                    ),
                },
            )
    quiz.status = Quiz.Status.PUBLISHED
    quiz.save(update_fields=["status", "updated_at"])
    return redirect("quizzes:quiz_detail", quiz_id=quiz.id)


@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, status=Quiz.Status.PUBLISHED)
    # Creators cannot attempt their own quizzes.
    if quiz.owner_id == request.user.id:
        return redirect("quizzes:quiz_detail", quiz_id=quiz.id)
    questions = quiz.questions.prefetch_related("choices")
    # Find an existing unfinished attempt.
    if request.method == "POST":
        # A submission must belong to an existing unfinished attempt.
        attempt = get_object_or_404(
            QuizAttempt,
            user=request.user,
            quiz=quiz,
            status=QuizAttempt.Status.IN_PROGRESS,
        )
    else:
        # Reuse an unfinished attempt if the user refreshes the page.
        attempt = (
            QuizAttempt.objects.filter(
                user=request.user, quiz=quiz, status=QuizAttempt.Status.IN_PROGRESS
            )
            .order_by("-started_at")
            .first()
        )
    # Create a new attempt only when opening the quiz.
    if attempt is None:
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            total_marks=sum(question.marks for question in questions),
        )
    if request.method == "POST":
        selected_answers = []
        submission_error = None
        for question in questions:
            choice_id = request.POST.get(f"question_{question.id}")
            if not choice_id:
                submission_error = "Please answer every question before submitting."
                break
            selected_choice = question.choices.filter(id=choice_id).first()
            if not selected_choice:
                submission_error = "Invalid answer detected. Please try again."
                break
            selected_answers.append((question, selected_choice))
        if submission_error:
            return render(
                request,
                "quizzes/take_quiz.html",
                {
                    "quiz": quiz,
                    "questions": questions,
                    "submission_error": submission_error,
                },
            )
        score = sum(
            question.marks for question, choice in selected_answers if choice.is_correct
        )
        with transaction.atomic():
            attempt.score = score
            attempt.total_marks = sum(question.marks for question in questions)
            attempt.completed_at = timezone.now()
            attempt.status = QuizAttempt.Status.COMPLETED
            attempt.save(
                update_fields=["score", "total_marks", "completed_at", "status"]
            )
            for question, selected_choice in selected_answers:
                is_correct = selected_choice.is_correct
                answer = AttemptAnswer(
                    attempt=attempt,
                    question=question,
                    selected_choice=selected_choice,
                    is_correct=is_correct,
                    marks_awarded=question.marks if is_correct else 0,
                )
                answer.full_clean()
                answer.save()
        return redirect("quizzes:attempt_result", attempt_id=attempt.id)
    return render(
        request,
        "quizzes/take_quiz.html",
        {"quiz": quiz, "questions": questions, "attempt": attempt},
    )


@login_required
def attempt_result(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related("quiz", "user"),
        id=attempt_id,
        user=request.user,
        status=QuizAttempt.Status.COMPLETED,
    )
    answers = attempt.answers.select_related(
        "question", "selected_choice"
    ).prefetch_related("question__choices")
    return render(
        request, "quizzes/attempt_result.html", {"attempt": attempt, "answers": answers}
    )


def explore_quizzes(request):
    published_quizzes = (
        Quiz.objects.filter(status=Quiz.Status.PUBLISHED)
        .select_related("category", "owner")
        .annotate(question_count=Count("questions"))
    )
    return render(
        request,
        "quizzes/explore_quizzes.html",
        {"published_quizzes": published_quizzes},
    )
