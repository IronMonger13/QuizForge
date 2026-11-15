from django.shortcuts import render, redirect
from django.contrib.auth import login, logout

from .forms import RegistrationForm, LoginForm


# Create your views here.
def register(request):

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            return redirect("quizzes:dashboard")

    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def user_login(request):

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            return redirect("quizzes:dashboard")

    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def user_logout(request):

    if request.method == "POST":
        logout(request)

    return redirect("accounts:login")
