import os

from django.conf import settings
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.db.utils import OperationalError
from django.http import JsonResponse


class RangesMiddleware(MiddlewareMixin):
    """Quick solution. See:
    https://stackoverflow.com/questions/14324250/byte-ranges-in-django/35928017#35928017
    """

    def process_response(self, request, response):
        if response.status_code != 200 or not hasattr(response, "file_to_stream"):
            return response
        http_range = request.META.get("HTTP_RANGE")
        if not (http_range and http_range.startswith("bytes=") and http_range.count("-") == 1):
            return response
        if_range = request.META.get("HTTP_IF_RANGE")
        if if_range and if_range != response.get("Last-Modified") and if_range != response.get("ETag"):
            return response
        f = response.file_to_stream
        statobj = os.fstat(f.fileno())
        start, end = http_range.split("=")[1].split("-")
        if not start:  # requesting the last N bytes
            start = max(0, statobj.st_size - int(end))
            end = ""
        start, end = int(start or 0), int(end or statobj.st_size - 1)
        assert 0 <= start < statobj.st_size, (start, statobj.st_size)
        end = min(end, statobj.st_size - 1)
        f.seek(start)
        old_read = f.read
        f.read = lambda n: old_read(min(n, end + 1 - f.tell()))
        response.status_code = 206
        response["Content-Length"] = end + 1 - start
        response["Content-Range"] = "bytes %d-%d/%d" % (start, end, statobj.st_size)
        return response


def to_django_header(header):
    return f"HTTP_{header.replace('-', '_').upper()}"


class HeaderAuthMiddleware(RemoteUserMiddleware):
    header = to_django_header(settings.HEADER_AUTH_USER_NAME)

    def process_request(self, request):
        if request.user.is_authenticated:
            return

        username = request.META.get(self.header)
        if not username:
            return

        super().process_request(request)
        self.process_user_groups(request.user, request.META)

    @classmethod
    def process_user_groups(cls, user, headers):
        if not user.is_authenticated:
            return

        groups = cls.parse_user_groups_from_header(headers)

        is_superuser = settings.HEADER_AUTH_ADMIN_GROUP_NAME in groups
        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            user.save()

    @classmethod
    def parse_user_groups_from_header(cls, headers):
        try:
            groups_header = headers[to_django_header(settings.HEADER_AUTH_USER_GROUPS)]
        except KeyError:
            return []
        else:
            return groups_header.split(settings.HEADER_AUTH_GROUPS_SEPERATOR)


class DatabaseHealthMiddleware(MiddlewareMixin):
    """Return 503 Service Unavailable when the application cannot reach the DB.

    This middleware tries to open a DB connection for every incoming request that
    reaches Django. If the connection fails (e.g. the DB service is down), a JSON
    response with HTTP status 503 is returned so that clients can react (for
    example, by showing a pop-up message).
    """

    def process_request(self, request):
        # Import lazily to avoid circular-import issues and unnecessary cost when
        # Django is running without a DB (e.g. some management commands).
        from django.db import connection
        from django.db.utils import OperationalError
        from django.http import JsonResponse

        try:
            # ``ensure_connection`` will try to connect only if the connection is
            # unusable or closed, therefore the overhead is minimal once the DB
            # is healthy.
            connection.ensure_connection()
        except OperationalError:
            # Database is down. Signal the problem so that reverse-proxies,
            # monitoring and the front-end can handle it properly.
            return JsonResponse({"detail": "Database unavailable"}, status=503)
