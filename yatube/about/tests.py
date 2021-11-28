from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_about_author_exists_at_desired_location(self):
        """Страница об авторе корректно отображается
        для неавторизованного пользователя.
        """
        target_path = reverse('about:author')
        response = self.guest_client.get(target_path)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_tech_exists_at_desired_location(self):
        """Страница о технологиях корректно отображается
        для неавторизованного пользователя.
        """
        target_path = reverse('about:tech')
        response = self.guest_client.get(target_path)
        self.assertEqual(response.status_code, HTTPStatus.OK)
