import os
from django.utils.timezone import now
from django.conf import settings

class UsageTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.log_file = os.path.join(settings.BASE_DIR, "url_usage_log.txt")

    def __call__(self, request):
        response = self.get_response(request)

        # Get user info
        user_id = request.user.id if request.user.is_authenticated else "Anonymous"
        username = request.user.username if request.user.is_authenticated else "Anonymous"

        # Build log line
        log_line = f"{now()} - User:{user_id} ({username}) - {request.method} - {request.path}\n"

        # Append to file
        with open(self.log_file, "a") as f:
            f.write(log_line)

        return response
