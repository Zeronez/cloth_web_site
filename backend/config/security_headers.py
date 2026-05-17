from django.conf import settings


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        policy = getattr(settings, "CONTENT_SECURITY_POLICY", "").strip()
        if not policy:
            return response

        header_name = (
            "Content-Security-Policy-Report-Only"
            if settings.CONTENT_SECURITY_POLICY_REPORT_ONLY
            else "Content-Security-Policy"
        )
        if header_name not in response:
            response[header_name] = policy
        return response
