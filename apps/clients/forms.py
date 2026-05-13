from __future__ import annotations

from typing import ClassVar

from django import forms

from .models import Client, ClientMetaCredentials


class ClientForm(forms.ModelForm):  # type: ignore[type-arg]
    access_token = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            render_value=False,
            attrs={
                "class": (
                    "block w-full rounded border border-surface-border bg-surface"
                    " px-3 py-1.5 text-sm text-ink"
                    " focus:border-brand-600 focus:ring-2 focus:ring-brand-100"
                ),
                "autocomplete": "off",
            },
        ),
        help_text="Leave blank to keep the current token.",
    )

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
