from django.http import HttpRequest


def request_id(request: HttpRequest) -> dict[str, str]:
    return {"request_id": getattr(request, "request_id", "")}
