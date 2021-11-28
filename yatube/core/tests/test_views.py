from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class CoreViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            username='me'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_404_uses_correct_template(self):
        response = self.authorized_client.get(
            reverse('posts:group_posts', args=['unexisting_group'])
        )
        self.assertTemplateUsed(response, 'core/404.html')
