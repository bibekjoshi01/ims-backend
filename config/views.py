from django.shortcuts import render


def home(request):
    """Homepage view for the SaaS app."""
    return render(request, "home.html")
