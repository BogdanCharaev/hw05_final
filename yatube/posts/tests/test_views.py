import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            username='me'
        )
        cls.fake_group = Group.objects.create(
            title='фейк группа',
            slug='fake_test_slug',
            description='Фейк группа для теста'
        )
        cls.group = Group.objects.create(
            title='Название',
            slug='test_slug',
            description='test_desc'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Пост',
            group=cls.group,
            author=cls.user,
            image=cls.uploaded
        )

        cls.templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts', args=[PostsViewsTests.group.slug]
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', args=[PostsViewsTests.user.username]
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', args=[PostsViewsTests.post.id]
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', args=[PostsViewsTests.post.id]
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image, self.post.image)

    def test_index_page_show_correct_context(self):
        """Страница posts:index сформирована с правильным
        контекстом
        """
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        first_object = response.context['page_obj'][0]
        self.check_post(first_object)

    def test_group_page_show_correct_context(self):
        """Страница posts:group_posts сформирована с правильным
        контекстом
        """
        response = self.authorized_client.get(
            reverse('posts:group_posts', args=[PostsViewsTests.group.slug])
        )
        first_object = response.context['page_obj'][0]
        self.check_post(first_object)

    def test_profile_page_show_correct_context(self):
        """Страница posts:profile_page сформирована с правильным
        контекстом
        """
        response = self.authorized_client.get(
            reverse('posts:profile', args=[PostsViewsTests.user.username])
        )
        first_object = response.context['page_obj'][0]
        self.check_post(first_object)

    def test_post_detail_page_show_correct_context(self):
        """Страница posts:post_detail сформирована с правильным
        контекстом
        """
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=[PostsViewsTests.post.id])
        )
        post = response.context['post']
        count = response.context['count']
        exact_number_of_posts = PostsViewsTests.user.posts.count()
        self.assertEqual(count, exact_number_of_posts)
        self.check_post(post)

    def test_post_create_page_show_correct_context(self):
        """Страница posts:post_create сформирована с правильным
        контекстом
        """
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Страница posts:post_edit сформирована с правильным
        контекстом
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[PostsViewsTests.post.id])
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_urls_uses_correct_template(self):
        """Шаблоны страниц соответствуют путям(адресам)."""
        for path, template in PostsViewsTests.templates_url_names.items():
            with self.subTest(path=path):
                response = self.authorized_client.get(path)
                self.assertTemplateUsed(response, template)

    def test_post_exists_at_index_page(self):
        """Созданный пост присутствует на главной"""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.group.slug, PostsViewsTests.group.slug)

    def test_post_exists_at_group_page(self):
        """Созданный пост присутствует на странице группы"""
        response = self.authorized_client.get(
            reverse('posts:group_posts', args=[PostsViewsTests.group.slug])
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.group.slug, PostsViewsTests.group.slug)

    def test_post_exists_at_profile_page(self):
        """Созданный пост присутствует на странице профайла"""
        response = self.authorized_client.get(
            reverse('posts:profile', args=[PostsViewsTests.user.username])
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.group.slug, PostsViewsTests.group.slug)

    def test_post_not_exists_at_fake_group_page(self):
        """Созданный пост не присутствует на странице не своей группы"""
        response = self.authorized_client.get(
            reverse('posts:group_posts',
                    args=[PostsViewsTests.fake_group.slug]))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_authorized_user_can_comment(self):
        response = self.authorized_client.get(
            reverse('posts:add_comment', args=[self.post.id])
        )
        self.assertEqual(response.status_code, 302)


class CacheTestView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='me')
        cls.post = Post.objects.create(text='Text',
                                       author=cls.user)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_cache(self):
        """Проверяет работу кэша."""
        self.post.delete()
        response_post_deleted = self.authorized_client.get(
            reverse('posts:index')
        )
        cache.clear()
        response_post_deleted_cache_cleared = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(
            response_post_deleted.content,
            response_post_deleted_cache_cleared.content
        )


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.NUMBER_OF_POSTS_FOR_SECOND_PAGE = 3

        cls.user = User.objects.create(
            username='me'
        )
        cls.group = Group.objects.create(
            title='Название',
            slug='test_slug',
            description='test_desc'
        )
        for i in range(
                settings.POSTS_PER_PAGE + cls.NUMBER_OF_POSTS_FOR_SECOND_PAGE):
            cls.post = Post.objects.create(
                text=f'Пост{i}',
                group=cls.group,
                author=cls.user,
            )

    def test_first_index_page_contains_ten_records(self):
        """Первая страница posts:index содержит 10 постов"""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_PER_PAGE
        )

    def test_second_index_page_contains_three_records(self):
        """Вторая страница posts:index содержит 3 поста"""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(
                response.context['page_obj']),
            PaginatorViewsTest.NUMBER_OF_POSTS_FOR_SECOND_PAGE
        )

    def test_first_group_page_contains_ten_records(self):
        """Первая страница posts:group_page содержит 10 постов"""
        response = self.client.get(
            reverse('posts:group_posts', args=[PaginatorViewsTest.group.slug]))
        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_PER_PAGE
        )

    def test_second_group_page_contains_three_records(self):
        """Вторая страница posts:group_posts содержит 3 поста"""
        response = self.client.get(
            reverse('posts:group_posts',
                    args=[PaginatorViewsTest.group.slug]) + '?page=2')
        self.assertEqual(
            len(
                response.context['page_obj']),
            PaginatorViewsTest.NUMBER_OF_POSTS_FOR_SECOND_PAGE)

    def test_first_profile_page_contains_ten_records(self):
        """Первая страница posts:profile содержит 10 постов"""
        response = self.client.get(
            reverse('posts:profile', args=[PaginatorViewsTest.user.username]))
        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_PER_PAGE
        )

    def test_second_profile_page_contains_three_records(self):
        """Вторая страница posts:profile содержит 3 поста"""
        response = self.client.get(
            reverse('posts:profile',
                    args=[PaginatorViewsTest.user.username]) + '?page=2')
        self.assertEqual(
            len(
                response.context['page_obj']),
            PaginatorViewsTest.NUMBER_OF_POSTS_FOR_SECOND_PAGE)


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='me')
        cls.post = Post.objects.create(text='Text',
                                       author=cls.user)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_user_can_follow(self):
        """Пользователь может подписаться"""
        new_user_to_follow = User.objects.create(username='him')
        self.assertFalse(
            new_user_to_follow.following.filter(user=self.user)
            .exists())
        self.authorized_client.get(
            reverse(
                'posts:profile_follow', args=[new_user_to_follow.username]
            )
        )
        self.assertTrue(
            new_user_to_follow.following.filter(user=self.user)
            .exists())

    def test_user_can_unfollow(self):
        """Пользователь может отписаться"""
        new_user_to_follow = User.objects.create(username='him')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow', args=[new_user_to_follow.username]
            )
        )
        self.assertTrue(
            new_user_to_follow.following.filter(user=self.user)
            .exists())
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow', args=[new_user_to_follow.username]
            )
        )
        self.assertFalse(
            new_user_to_follow.following.filter(user=self.user)
            .exists())

    def test_page_exists_on_follow_index(self):
        user_to_follow = User.objects.create(username='him')
        post_to_exist = Post.objects.create(text='test',
                                            author=user_to_follow)
        user_not_to_follow = User.objects.create(username='al')

        self.authorized_client.get(
            reverse(
                'posts:profile_follow', args=[user_to_follow.username]
            )
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context.get('page_obj')[0].text,
                         post_to_exist.text)
        length = len(response.context.get('page_obj').object_list)

        Post.objects.create(text='test', author=user_not_to_follow)

        len_after_post_creation = len(
            response.context.get('page_obj').object_list)

        self.assertEqual(length, len_after_post_creation)
