import secrets


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(16)
        response = self.get_response(request)
        csp = self._build_csp_value(request)
        if csp:
            response["Content-Security-Policy"] = csp
        return response

    def _build_csp_value(self, request):
        from django.conf import settings

        policy = getattr(settings, "CONTENT_SECURITY_POLICY", None)
        if not isinstance(policy, dict) or not policy:
            return ""

        directives = []
        for key, value in policy.items():
            if isinstance(value, (list, tuple)):
                rendered_value = " ".join(str(item) for item in value if item)
            else:
                rendered_value = str(value).strip()

            rendered_value = rendered_value.replace("{nonce}", f"'nonce-{request.csp_nonce}'")

            if not key or not rendered_value:
                continue

            directives.append(f"{key} {rendered_value}")

        return "; ".join(directives)
