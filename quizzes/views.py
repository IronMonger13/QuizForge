from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import QuizForm
from .models import Quiz


# Create your views here.
@login_required
def dashboard(request):
    return render(request, "quizzes/dashboard.html")


@login_required
def create_quiz(request):

    if request.method == "POST":
        form = QuizForm(request.POST)

        if form.is_valid():
            quiz = form.save(commit=False)

            quiz.owner = request.user
            quiz.status = Quiz.Status.DRAFT

            quiz.save()

            return redirect("quizzes:dashboard")

    else:
        form = QuizForm()

    return render(request, "quizzes/create_quiz.html", {"form": form})
