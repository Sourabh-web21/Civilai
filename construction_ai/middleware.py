from django.http import HttpResponse


class DesktopPrivateNetworkCorsMiddleware:
    """Allow packaged WebView2 pages to call the localhost backend."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.method == "OPTIONS"
            and request.headers.get("Access-Control-Request-Private-Network")
        ):
            response = HttpResponse()
        else:
            response = self.get_response(request)

        response["Access-Control-Allow-Private-Network"] = "true"
        response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
        response["Access-Control-Allow-Methods"] = "DELETE, GET, OPTIONS, PATCH, POST, PUT"
        response["Access-Control-Allow-Headers"] = (
            "accept, authorization, content-type, user-agent, x-csrftoken, x-requested-with"
        )
        return response
