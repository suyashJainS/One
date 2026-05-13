"""manage.py sentry_test — raises a deliberate exception to verify Sentry is wired."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Trigger a deliberate exception to verify Sentry capture."

    def handle(self, *args: object, **options: object) -> None:
        raise RuntimeError("sentry-test: this is a deliberate test event")
