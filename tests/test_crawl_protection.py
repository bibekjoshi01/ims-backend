from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from config.robots import robots_txt
from src.libs.middleware import NoIndexMiddleware


@override_settings(DEBUG=False)
class CrawlProtectionTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_noindex_middleware_adds_response_header(self) -> None:
        request = self.factory.get("/dashboard")

        response = NoIndexMiddleware(lambda incoming_request: HttpResponse("ok"))(request)

        assert response["X-Robots-Tag"] == "noindex, nofollow, noarchive"

    def test_robots_txt_blocks_all_crawling_in_production(self) -> None:
        request = self.factory.get("/robots.txt")

        response = robots_txt(request)

        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/plain")
        assert response.content.decode() == "User-agent: *\nDisallow: /\n"
