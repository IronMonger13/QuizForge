from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import RegistrationForm, LoginForm, ProfileForm


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


@login_required
def profile(request):

    # Fetch a separate User instance instead of modifying request.user.
    profile_user = request.user.__class__.objects.get(pk=request.user.pk)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile_user)

        if form.is_valid():
            form.save()

            messages.success(request, "Your profile has been updated successfully.")

            return redirect("accounts:profile")

    else:
        form = ProfileForm(instance=profile_user)

    return render(
        request,
        "accounts/profile.html",
        {"form": form},
    )
