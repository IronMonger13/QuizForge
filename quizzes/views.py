from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField, Max, Q
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages
from datetime import timedelta

from .forms import (
    QuizForm,
    QuestionForm,
    ChoiceFormSet,
    EditChoiceFormSet,
    QuizFeedbackForm,
)
from .models import (
    Category,
    Quiz,
    Question,
    QuizAttempt,
    AttemptAnswer,
    Choice,
    QuizFeedback,
)


# Create your views here.
@login_required
def dashboard(request):
    # Quizzes created by the logged-in user.
    my_quizzes = (
        Quiz.objects.filter(owner=request.user)
        .select_related("category")
        .annotate(
            question_count=Count("questions", distinct=True),
            attempt_count=Count("attempts", distinct=True),
            completed_attempt_count=Count(
                "attempts",
                filter=Q(attempts__status=QuizAttempt.Status.COMPLETED),
                distinct=True,
            ),
        )
    )

    # Quiz creation statistics.
    quiz_stats = my_quizzes.aggregate(
        total_quizzes=Count("id"),
        published_quizzes=Count(
            "id",
            filter=Q(status=Quiz.Status.PUBLISHED),
        ),
        draft_quizzes=Count(
            "id",
            filter=Q(status=Quiz.Status.DRAFT),
        ),
    )

    # Completed attempts by the logged-in user.
    completed_attempts = QuizAttempt.objects.filter(
        user=request.user,
        status=QuizAttempt.Status.COMPLETED,
        total_marks__gt=0,
    )

    percentage_expression = ExpressionWrapper(
        F("score") * 100.0 / F("total_marks"),
        output_field=FloatField(),
    )

    attempt_stats = completed_attempts.aggregate(
        total_attempts=Count("id"),
        average_score=Avg(percentage_expression),
        highest_score=Max(percentage_expression),
    )

    # Performance statistics for quizzes created by the user.
    creator_attempts = QuizAttempt.objects.filter(
        quiz__owner=request.user,
        status=QuizAttempt.Status.COMPLETED,
        total_marks__gt=0,
    )

    creator_performance_stats = creator_attempts.aggregate(
        total_attempts=Count("id"),
        average_score=Avg(percentage_expression),
    )

    most_popular_quiz = (
        my_quizzes.filter(completed_attempt_count__gt=0)
        .order_by("-completed_attempt_count", "-created_at")
        .first()
    )

    # Latest three completed quiz attempts.
    recent_attempts = (
        QuizAttempt.objects.filter(
            user=request.user,
            status=QuizAttempt.Status.COMPLETED,
        )
        .select_related("quiz")
        .order_by("-completed_at")[:3]
    )

    for attempt in recent_attempts:
        attempt.percentage = (
            (attempt.score / attempt.total_marks) * 100
            if attempt.total_marks > 0
            else 0
        )

    return render(
        request,
        "quizzes/dashboard.html",
        {
            "my_quizzes": my_quizzes,
            "quiz_stats": quiz_stats,
            "attempt_stats": attempt_stats,
            "recent_attempts": recent_attempts,
            "creator_performance_stats": creator_performance_stats,
            "most_popular_quiz": most_popular_quiz,
        },
    )


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
def edit_quiz(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        owner=request.user,
        status=Quiz.Status.DRAFT,
        is_sample=False,
    )

    # Prevent editing quizzes that already have attempts.
    if quiz.attempts.exists():
        return redirect("quizzes:quiz_detail", quiz_id=quiz.id)

    if request.method == "POST":
        form = QuizForm(request.POST, instance=quiz)

        if form.is_valid():
            form.save()
            return redirect("quizzes:quiz_detail", quiz_id=quiz.id)

    else:
        form = QuizForm(instance=quiz)

    return render(
        request,
        "quizzes/edit_quiz.html",
        {
            "form": form,
            "quiz": quiz,
        },
    )


@login_required
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        owner=request.user,
        is_sample=False,
    )

    # Prevent deletion if the quiz has existing attempts.
    if quiz.attempts.exists():
        return redirect("quizzes:quiz_detail", quiz_id=quiz.id)

    if request.method == "POST":
        quiz.delete()
        return redirect("quizzes:dashboard")

    return render(
        request,
        "quizzes/delete_quiz.html",
        {"quiz": quiz},
    )


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
def edit_question(request, question_id):
    question = get_object_or_404(
        Question,
        id=question_id,
        quiz__owner=request.user,
        quiz__status=Quiz.Status.DRAFT,
        quiz__is_sample=False,
    )

    quiz = question.quiz

    # Prevent editing questions if the quiz already has attempts.
    if quiz.attempts.exists():
        return redirect("quizzes:quiz_detail", quiz_id=quiz.id)

    if request.method == "POST":
        question_form = QuestionForm(
            request.POST,
            instance=question,
        )

        correct_answer_error = None

        with transaction.atomic():
            # Clear the existing correct answer before validating the
            # formset. This avoids a temporary conflict with the
            # database constraint allowing only one correct choice.
            Choice.objects.filter(question=question).update(is_correct=False)

            choice_formset = EditChoiceFormSet(
                request.POST,
                queryset=question.choices.order_by("order"),
            )

            question_valid = question_form.is_valid()
            choices_valid = choice_formset.is_valid()

            if question_valid and choices_valid:
                correct_count = sum(
                    1 for form in choice_formset if form.cleaned_data.get("is_correct")
                )

                if correct_count == 1:
                    question_form.save()

                    for form in choice_formset:
                        choice = form.save(commit=False)
                        choice.question = question
                        choice.full_clean()
                        choice.save()

                    return redirect(
                        "quizzes:quiz_detail",
                        quiz_id=quiz.id,
                    )

                correct_answer_error = "Please select exactly one correct answer."

            # Invalid submissions must not leave the existing correct
            # answer cleared in the database.
            transaction.set_rollback(True)

    else:
        question_form = QuestionForm(instance=question)

        choice_formset = EditChoiceFormSet(
            queryset=question.choices.order_by("order"),
        )

        correct_answer_error = None

    return render(
        request,
        "quizzes/edit_question.html",
        {
            "quiz": quiz,
            "question": question,
            "question_form": question_form,
            "choice_formset": choice_formset,
            "correct_answer_error": correct_answer_error,
        },
    )


@login_required
def delete_question(request, question_id):
    question = get_object_or_404(
        Question,
        id=question_id,
        quiz__owner=request.user,
        quiz__status=Quiz.Status.DRAFT,
        quiz__is_sample=False,
    )

    quiz = question.quiz

    # Prevent deletion if the quiz already has attempts.
    if quiz.attempts.exists():
        return redirect("quizzes:quiz_detail", quiz_id=quiz.id)

    if request.method == "POST":
        with transaction.atomic():
            question.delete()

            # Renumber the remaining questions.
            remaining_questions = quiz.questions.order_by("order", "id")

            for new_order, remaining_question in enumerate(
                remaining_questions,
                start=1,
            ):
                if remaining_question.order != new_order:
                    remaining_question.order = new_order
                    remaining_question.save(update_fields=["order"])

        return redirect("quizzes:quiz_detail", quiz_id=quiz.id)

    return render(
        request,
        "quizzes/delete_question.html",
        {
            "question": question,
            "quiz": quiz,
        },
    )


@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        owner=request.user,
    )

    questions = quiz.questions.prefetch_related("choices")
    question_count = quiz.questions.count()

    # Completed attempts for this quiz.
    completed_attempts = quiz.attempts.filter(
        status=QuizAttempt.Status.COMPLETED,
        total_marks__gt=0,
    ).annotate(
        answered_count=Count(
            "answers",
            filter=Q(answers__selected_choice__isnull=False),
            distinct=True,
        )
    )

    # Calculate performance metrics.
    score_percentage = ExpressionWrapper(
        F("score") * 100.0 / F("total_marks"),
        output_field=FloatField(),
    )

    quiz_stats = completed_attempts.aggregate(
        total_attempts=Count("id"),
        average_score=Avg(score_percentage),
        highest_score=Max(score_percentage),
    )

    # Average percentage of questions answered per attempt.
    if question_count > 0:
        completion_percentage = ExpressionWrapper(
            F("answered_count") * 100.0 / question_count,
            output_field=FloatField(),
        )

        quiz_stats["average_completion"] = completed_attempts.aggregate(
            average_completion=Avg(completion_percentage)
        )["average_completion"]
    else:
        quiz_stats["average_completion"] = None

    # Feedback statistics.
    feedback_queryset = quiz.feedback.select_related("user")

    feedback_stats = feedback_queryset.aggregate(
        total_reviews=Count("id"),
        average_rating=Avg("rating"),
    )

    # Retrieve all feedback.
    feedback_list = feedback_queryset.order_by("-created_at")

    return render(
        request,
        "quizzes/quiz_detail.html",
        {
            "quiz": quiz,
            "questions": questions,
            "quiz_stats": quiz_stats,
            "feedback_stats": feedback_stats,
            "feedback_list": feedback_list,
        },
    )


@login_required
def quiz_attempt_history(request, quiz_id):
    # Only the quiz creator can access this page.
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        owner=request.user,
    )

    total_questions = quiz.questions.count()

    # Retrieve completed attempts and calculate answer statistics.
    attempts = (
        quiz.attempts.filter(
            status=QuizAttempt.Status.COMPLETED,
        )
        .select_related("user")
        .annotate(
            answered_questions=Count(
                "answers",
                filter=Q(answers__selected_choice__isnull=False),
                distinct=True,
            ),
            correct_answers=Count(
                "answers",
                filter=Q(
                    answers__selected_choice__isnull=False,
                    answers__is_correct=True,
                ),
                distinct=True,
            ),
        )
        .order_by("-completed_at")
    )

    # Calculate individual attempt statistics.
    for attempt in attempts:
        attempt.incorrect_answers = attempt.answered_questions - attempt.correct_answers

        attempt.unanswered_questions = total_questions - attempt.answered_questions

        attempt.percentage = (
            (attempt.score / attempt.total_marks) * 100
            if attempt.total_marks > 0
            else 0
        )

    return render(
        request,
        "quizzes/quiz_attempt_history.html",
        {
            "quiz": quiz,
            "attempts": attempts,
            "total_questions": total_questions,
        },
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
@require_POST
def unpublish_quiz(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        owner=request.user,
        status=Quiz.Status.PUBLISHED,
        is_sample=False,
    )

    quiz.status = Quiz.Status.DRAFT
    quiz.save(update_fields=["status", "updated_at"])

    return redirect("quizzes:quiz_detail", quiz_id=quiz.id)


@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        status=Quiz.Status.PUBLISHED,
    )

    # Creators cannot attempt their own quizzes.
    if quiz.owner_id == request.user.id:
        return redirect("quizzes:quiz_detail", quiz_id=quiz.id)

    questions = quiz.questions.prefetch_related("choices")

    # POST request: process quiz submission.
    if request.method == "POST":
        with transaction.atomic():

            # Lock the attempt while processing submission.
            attempt = get_object_or_404(
                QuizAttempt.objects.select_for_update(),
                user=request.user,
                quiz=quiz,
                status=QuizAttempt.Status.IN_PROGRESS,
            )

            # Check expiration using the server's clock.
            is_expired = (
                attempt.expires_at is not None and timezone.now() >= attempt.expires_at
            )

            # Retrieve answers saved in the database.
            saved_answers = {
                answer.question_id: answer.selected_choice
                for answer in AttemptAnswer.objects.filter(
                    attempt=attempt
                ).select_related("selected_choice")
            }

            selected_answers = []
            submission_error = None

            for question in questions:
                selected_choice = saved_answers.get(question.id)

                # Before expiration, every question must be answered.
                if selected_choice is None and not is_expired:
                    submission_error = "Please answer every question before submitting."
                    break

                selected_answers.append((question, selected_choice))

            if submission_error:
                return render(
                    request,
                    "quizzes/take_quiz.html",
                    {
                        "quiz": quiz,
                        "questions": questions,
                        "attempt": attempt,
                        "submission_error": submission_error,
                        "saved_answers": {
                            question_id: choice.id
                            for question_id, choice in saved_answers.items()
                            if choice is not None
                        },
                    },
                )

            # Calculate the score using only saved answers.
            score = sum(
                question.marks
                for question, choice in selected_answers
                if choice is not None and choice.is_correct
            )

            # Complete the attempt.
            attempt.score = score
            attempt.total_marks = sum(question.marks for question in questions)
            attempt.completed_at = timezone.now()
            attempt.status = QuizAttempt.Status.COMPLETED

            attempt.save(
                update_fields=[
                    "score",
                    "total_marks",
                    "completed_at",
                    "status",
                ]
            )

            # Update individual answer records.
            for question, selected_choice in selected_answers:
                is_correct = selected_choice is not None and selected_choice.is_correct

                AttemptAnswer.objects.filter(
                    attempt=attempt,
                    question=question,
                ).update(
                    is_correct=is_correct,
                    marks_awarded=(question.marks if is_correct else 0),
                )

        return redirect(
            "quizzes:attempt_result",
            attempt_id=attempt.id,
        )

    # GET request: reuse an unfinished attempt if one exists.
    attempt = (
        QuizAttempt.objects.filter(
            user=request.user,
            quiz=quiz,
            status=QuizAttempt.Status.IN_PROGRESS,
        )
        .order_by("-started_at")
        .first()
    )

    # Automatically complete expired attempts.
    if (
        attempt is not None
        and attempt.expires_at is not None
        and timezone.now() >= attempt.expires_at
    ):
        with transaction.atomic():

            # Lock the attempt before completing it.
            attempt = (
                QuizAttempt.objects.select_for_update()
                .filter(
                    id=attempt.id,
                    user=request.user,
                    status=QuizAttempt.Status.IN_PROGRESS,
                )
                .first()
            )

            if attempt is not None:
                # Retrieve answers saved before expiration.
                saved_answers = {
                    answer.question_id: answer.selected_choice
                    for answer in AttemptAnswer.objects.filter(
                        attempt=attempt
                    ).select_related("selected_choice")
                }

                # Calculate the score using saved answers only.
                score = sum(
                    question.marks
                    for question in questions
                    if (
                        saved_answers.get(question.id) is not None
                        and saved_answers[question.id].is_correct
                    )
                )

                attempt.score = score
                attempt.total_marks = sum(question.marks for question in questions)
                attempt.completed_at = timezone.now()
                attempt.status = QuizAttempt.Status.COMPLETED

                attempt.save(
                    update_fields=[
                        "score",
                        "total_marks",
                        "completed_at",
                        "status",
                    ]
                )

                # Update correctness and marks for saved answers.
                for question in questions:
                    selected_choice = saved_answers.get(question.id)

                    if selected_choice is not None:
                        is_correct = selected_choice.is_correct

                        AttemptAnswer.objects.filter(
                            attempt=attempt,
                            question=question,
                        ).update(
                            is_correct=is_correct,
                            marks_awarded=(question.marks if is_correct else 0),
                        )

                return redirect(
                    "quizzes:attempt_result",
                    attempt_id=attempt.id,
                )

            # Another request may have completed the attempt already.
            completed_attempt = (
                QuizAttempt.objects.filter(
                    user=request.user,
                    quiz=quiz,
                    status=QuizAttempt.Status.COMPLETED,
                )
                .order_by("-completed_at")
                .first()
            )

            if completed_attempt:
                return redirect(
                    "quizzes:attempt_result",
                    attempt_id=completed_attempt.id,
                )

    # Create a new attempt only when one does not already exist.
    if attempt is None:
        expires_at = None

        if quiz.time_limit:
            expires_at = timezone.now() + timedelta(minutes=quiz.time_limit)

        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            total_marks=sum(question.marks for question in questions),
            expires_at=expires_at,
        )

    # Retrieve previously saved answers for this attempt.

    saved_answers = dict(
        AttemptAnswer.objects.filter(attempt=attempt).values_list(
            "question_id",
            "selected_choice_id",
        )
    )

    # Attach the saved choice ID to each question for the template.
    for question in questions:
        question.saved_choice_id = saved_answers.get(question.id)

    return render(
        request,
        "quizzes/take_quiz.html",
        {
            "quiz": quiz,
            "questions": questions,
            "attempt": attempt,
        },
    )


@login_required
def save_quiz_answer(request, attempt_id):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Invalid request method."},
            status=405,
        )

    with transaction.atomic():
        # Lock the attempt while saving the answer.
        attempt = get_object_or_404(
            QuizAttempt.objects.select_for_update(),
            id=attempt_id,
            user=request.user,
            status=QuizAttempt.Status.IN_PROGRESS,
        )

        # Prevent answers from being changed after expiration.
        if attempt.expires_at is not None and timezone.now() >= attempt.expires_at:
            return JsonResponse(
                {"error": "Time has expired."},
                status=400,
            )

        question_id = request.POST.get("question_id")
        choice_id = request.POST.get("choice_id")

        # Verify that the question belongs to this quiz.
        question = get_object_or_404(
            Question,
            id=question_id,
            quiz=attempt.quiz,
        )

        # Verify that the selected choice belongs to this question.
        selected_choice = get_object_or_404(
            Choice,
            id=choice_id,
            question=question,
        )

        is_correct = selected_choice.is_correct

        answer, created = AttemptAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                "selected_choice": selected_choice,
                "is_correct": is_correct,
                "marks_awarded": (question.marks if is_correct else 0),
            },
        )

    return JsonResponse(
        {
            "success": True,
            "message": "Answer saved successfully.",
        }
    )


@login_required
def submit_quiz_feedback(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        status=Quiz.Status.PUBLISHED,
    )

    # Quiz creators cannot review their own quizzes.
    if quiz.owner_id == request.user.id:
        return redirect("quizzes:quiz_overview", quiz_id=quiz.id)

    # Only users who have completed an attempt can submit feedback.
    has_completed_attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        status=QuizAttempt.Status.COMPLETED,
    ).exists()

    if not has_completed_attempt:
        return redirect("quizzes:quiz_overview", quiz_id=quiz.id)

    # Retrieve an existing review without creating a new one.
    feedback = QuizFeedback.objects.filter(
        user=request.user,
        quiz=quiz,
    ).first()

    if request.method == "POST":
        form = QuizFeedbackForm(
            request.POST,
            instance=feedback,
        )

        if form.is_valid():
            saved_feedback = form.save(commit=False)
            saved_feedback.user = request.user
            saved_feedback.quiz = quiz
            saved_feedback.save()

            messages.success(
                request,
                "Your feedback has been saved successfully.",
            )

            return redirect(
                "quizzes:quiz_overview",
                quiz_id=quiz.id,
            )

    else:
        form = QuizFeedbackForm(instance=feedback)

    return render(
        request,
        "quizzes/submit_feedback.html",
        {
            "quiz": quiz,
            "form": form,
            "is_update": feedback is not None,
        },
    )


@login_required
@require_POST
def delete_quiz_feedback(request, quiz_id):
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
    )

    # Quiz creators cannot manage participant feedback.
    if quiz.owner_id == request.user.id:
        return redirect("quizzes:explore_quizzes")

    feedback = get_object_or_404(
        QuizFeedback,
        quiz=quiz,
        user=request.user,
    )

    feedback.delete()

    messages.success(
        request,
        "Your feedback has been deleted successfully.",
    )

    if quiz.status == Quiz.Status.PUBLISHED:
        return redirect("quizzes:quiz_overview", quiz_id=quiz.id)

    return redirect("quizzes:explore_quizzes")


@login_required
def attempt_result(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related("quiz", "user").filter(
            Q(user=request.user) | Q(quiz__owner=request.user),
            status=QuizAttempt.Status.COMPLETED,
        ),
        id=attempt_id,
    )

    # Retrieve every question from the quiz.
    questions = attempt.quiz.questions.prefetch_related("choices").order_by("order")

    # Retrieve answers saved during the attempt.
    answers = {
        answer.question_id: answer
        for answer in attempt.answers.select_related("selected_choice")
    }

    # Match every question with its answer, if one exists.
    review_items = []

    for question in questions:
        answer = answers.get(question.id)

        review_items.append(
            {
                "question": question,
                "answer": answer,
            }
        )

    # Calculate statistics across ALL questions.
    total_questions = len(review_items)

    correct_answers = sum(
        1 for item in review_items if item["answer"] and item["answer"].is_correct
    )

    unanswered_questions = sum(
        1
        for item in review_items
        if (item["answer"] is None or item["answer"].selected_choice is None)
    )

    incorrect_answers = total_questions - correct_answers - unanswered_questions

    percentage = (
        (attempt.score / attempt.total_marks) * 100 if attempt.total_marks > 0 else 0
    )

    return render(
        request,
        "quizzes/attempt_result.html",
        {
            "attempt": attempt,
            "review_items": review_items,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "incorrect_answers": incorrect_answers,
            "unanswered_questions": unanswered_questions,
            "percentage": round(percentage, 2),
        },
    )


def explore_quizzes(request):
    search_query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")

    categories = Category.objects.all().order_by("name")

    published_quizzes = (
        Quiz.objects.filter(status=Quiz.Status.PUBLISHED)
        .select_related("category", "owner")
        .annotate(
            question_count=Count("questions", distinct=True),
            attempt_count=Count("attempts", distinct=True),
        )
    )

    if search_query:
        published_quizzes = published_quizzes.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    if category_id:
        if Category.objects.filter(id=category_id).exists():
            published_quizzes = published_quizzes.filter(category_id=category_id)
        else:
            category_id = ""

    # Sorting options.
    sort_options = {
        "newest": ("-created_at", "-id"),
        "most_attempted": ("-attempt_count", "-created_at"),
        "alphabetical": ("title", "-created_at"),
    }

    selected_sort = request.GET.get("sort", "newest")

    # Fall back to newest if an invalid sorting option is provided.
    if selected_sort not in sort_options:
        selected_sort = "newest"

    published_quizzes = published_quizzes.order_by(*sort_options[selected_sort])

    sample_paginator = Paginator(
        published_quizzes.filter(is_sample=True),
        6,
    )
    community_paginator = Paginator(
        published_quizzes.filter(is_sample=False),
        6,
    )

    sample_quizzes = sample_paginator.get_page(request.GET.get("sample_page"))
    community_quizzes = community_paginator.get_page(request.GET.get("community_page"))

    return render(
        request,
        "quizzes/explore_quizzes.html",
        {
            "sample_quizzes": sample_quizzes,
            "community_quizzes": community_quizzes,
            "categories": categories,
            "search_query": search_query,
            "selected_category": category_id,
        },
    )


def quiz_overview(request, quiz_id):
    quiz = get_object_or_404(
        Quiz.objects.select_related("category", "owner"),
        id=quiz_id,
        status=Quiz.Status.PUBLISHED,
    )

    # Fetch participant feedback.
    feedback_list = quiz.feedback.select_related("user").order_by("-created_at")

    feedback_stats = feedback_list.aggregate(
        total_reviews=Count("id"),
        average_rating=Avg("rating"),
    )

    # Check whether the current user is eligible to submit feedback.
    can_submit_feedback = False
    existing_feedback = None

    if request.user.is_authenticated:
        has_completed_attempt = QuizAttempt.objects.filter(
            user=request.user,
            quiz=quiz,
            status=QuizAttempt.Status.COMPLETED,
        ).exists()

        can_submit_feedback = has_completed_attempt and quiz.owner_id != request.user.id

        if can_submit_feedback:
            existing_feedback = quiz.feedback.filter(user=request.user).first()

    context = {
        "quiz": quiz,
        "question_count": quiz.questions.count(),
        "attempt_count": quiz.attempts.filter(
            status=QuizAttempt.Status.COMPLETED
        ).count(),
        "feedback_list": feedback_list,
        "feedback_stats": feedback_stats,
        "can_submit_feedback": can_submit_feedback,
        "existing_feedback": existing_feedback,
    }

    return render(request, "quizzes/quiz_overview.html", context)


@login_required
def attempt_history(request):
    attempts = list(
        QuizAttempt.objects.filter(
            user=request.user,
            status=QuizAttempt.Status.COMPLETED,
        )
        .select_related("quiz")
        .prefetch_related("answers", "quiz__questions")
        .order_by("-completed_at")
    )

    for attempt in attempts:
        answers = list(attempt.answers.all())

        total_questions = attempt.quiz.questions.count()

        correct_answers = sum(1 for answer in answers if answer.is_correct)

        answered_questions = sum(
            1 for answer in answers if answer.selected_choice_id is not None
        )

        incorrect_answers = answered_questions - correct_answers

        unanswered_questions = total_questions - answered_questions

        percentage = (
            (attempt.score / attempt.total_marks) * 100
            if attempt.total_marks > 0
            else 0
        )

        attempt.total_questions = total_questions
        attempt.correct_answers = correct_answers
        attempt.incorrect_answers = incorrect_answers
        attempt.unanswered_questions = unanswered_questions
        attempt.percentage = round(percentage, 2)

    return render(
        request,
        "quizzes/attempt_history.html",
        {"attempts": attempts},
    )
