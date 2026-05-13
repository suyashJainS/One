from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import ClientForm
from .models import Client


@login_required
def client_list(request: HttpRequest) -> HttpResponse:
    clients = Client.objects.all().order_by("-is_active", "name")
    return render(request, "clients/list.html", {"clients": clients})


@login_required
@require_http_methods(["GET", "POST"])
def client_new(request: HttpRequest) -> HttpResponse:
    form = ClientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("clients:list")
    return render(request, "clients/edit.html", {"form": form, "is_new": True})


@login_required
@require_http_methods(["GET", "POST"])
def client_edit(request: HttpRequest, slug: str) -> HttpResponse:
    client = get_object_or_404(Client, slug=slug)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("clients:list")
    return render(request, "clients/edit.html", {"form": form, "client": client, "is_new": False})


@login_required
@require_http_methods(["POST"])
def client_delete(request: HttpRequest, slug: str) -> HttpResponse:
    client = get_object_or_404(Client, slug=slug)
    client.delete()
    return redirect("clients:list")
