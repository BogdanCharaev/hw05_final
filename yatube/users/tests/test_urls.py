from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            username='me'
        )

        cls.templates_url_names = {
            reverse('users:logout'): 'users/logged_out.html',
            reverse('users:login'): 'users/login.html',
            # reverse(
            #     'users:password_change'
            # ): 'users/password_change_form.html',
            reverse(
                'users:password_reset'
            ): 'users/password_reset_form.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_login_page_exists_at_desired_destination(self):

        response = self.guest_client.get(
            reverse('users:login')
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_logout_page_exists_at_desired_destination(self):

        response = self.authorized_client.get(
            reverse('users:logout')
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pass_change_page_exists_at_desired_destination(self):

        response = self.authorized_client.get(
            reverse('users:password_change')
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pass_change_page_redirects_anonymous(self):

        response = self.guest_client.get(
            reverse('users:password_change')
        )
        target = reverse('users:login')
        base = reverse('users:password_change')
        full_path = f'{target}?next={base}'
        self.assertRedirects(response, full_path)

    def test_pages_exists_at_desired_destination(self):

        for path, template in UsersURLTests.templates_url_names.items():
            with self.subTest(path=path):
                response = self.authorized_client.get(path)
                self.assertTemplateUsed(response, template)
