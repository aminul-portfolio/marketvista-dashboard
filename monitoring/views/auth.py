"""Views for user registration and authentication-related pages."""

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render


def register(request):
    if request.user.is_authenticated:
        return redirect("monitoring:dashboard")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("monitoring:dashboard")
    else:
        form = UserCreationForm()

    return render(request, "monitoring/register.html", {"form": form})