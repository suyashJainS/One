from __future__ import annotations

from typing import ClassVar

from django import forms

from .models import Client, ClientMetaCredentials


class ClientForm(forms.ModelForm):  # type: ignore[type-arg]
    access_token = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = Client
        fields: ClassVar = [
            "name",
            "slug",
            "is_active",
            "target_roas",
            "target_cpl",
            "target_cpa",
            "min_test_spend",
            "notes",
        ]

    def save(self, commit: bool = True) -> Client:
        client: Client = super().save(commit=commit)
        token = self.cleaned_data.get("access_token")
        if token:
            creds, _ = ClientMetaCredentials.objects.get_or_create(client=client)
            creds.access_token = token
            creds.save()
        return client
