from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            username='me'
        )
        cls.user_not_the_author = User.objects.create(
            username='him'
        )
        cls.group = Group.objects.create(
            title='Название',
            slug='test_slug',
            description='test_desc'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.not_the_author_client = Client()
        self.not_the_author_client.force_login(self.user_not_the_author)
        self.authorized_client.force_login(self.user)

    def test_homepage(self):
        """Главна страница корректно отображается
        для неавторизованного пользователя.
        """
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_page(self):
        """Страница группы корректно отображается
        для неавторизованного пользователя.
        """
        adress = f'/group/{self.group.slug}/'
        response = self.guest_client.get(adress)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_page(self):
        """Страница профайла корректно отображается
        для неавторизованного пользователя.
        """
        adress = f'/profile/{self.user.username}/'
        response = self.guest_client.get(adress)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_page(self):
        """Страница поста корректно отображается
        для неавторизованного пользователя.
        """
        adress = f'/posts/{self.post.id}/'
        response = self.guest_client.get(adress)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page_exists_for_authorized_user(self):
        """Страница редактирования поста корректно отображается
        для авторизованного пользователя
        """
        adress = f'/posts/{self.post.id}/edit/'
        response = self.authorized_client.get(adress)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page_redirects_anonymous(self):
        """Страница редактирования поста редиректит
        неавторизованного пользователя.
        """
        adress = f'/posts/{self.post.id}/edit/'
        response = self.guest_client.get(adress)

        target = '/auth/login/'
        full_path = f'{target}?next={adress}'

        self.assertRedirects(response, full_path)

    def test_create_page_exists_at_desired_destination(self):
        """Страница создания поста корректно отображается
        для авторизованного пользователя.
        """
        response = self.authorized_client.get('/create/')

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page_redirects_anonymous(self):
        """Страница создания поста редиректит
        неавторизованного пользователя.
        """
        adress = '/create/'
        response = self.guest_client.get('/create/')

        target = '/auth/login/'
        full_path = f'{target}?next={adress}'
        self.assertRedirects(response, full_path)

    def test_edit_page_returns_404_for_not_the_author(self):
        """Страница edit_page редиректит не автора на главную."""
        adress = f'/posts/{self.post.id}/edit/'
        response = self.not_the_author_client.get(adress)
        target_page = '/'
        self.assertRedirects(response, target_page)

    def test_unexisting_page_returns_404(self):
        """Несуществующая страница возвращает 404"""
        response = self.guest_client.get('random_page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """Шаблоны страниц соответствуют адресам."""
        for adress, template in PostsURLTests.templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_exists_at_desired_destination(self):
        """ Однотипные тесты через сабтест:
        страницы: index, group_posts, profile и post_edit
        корректно отображаются для авторизованного пользователя.
        """
        for adress in PostsURLTests.templates_url_names:
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_comment_page_redirects_anonymous(self):
        """Страница комментирования поста редиректит
        неавторизованного пользователя.
        """
        adress = f'/posts/{self.post.id}/comment'
        response = self.guest_client.get(adress)
        target = '/auth/login/'
        full_path = f'{target}?next={adress}'
        self.assertRedirects(response, full_path)
