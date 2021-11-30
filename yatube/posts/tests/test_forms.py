import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            username='me'
        )
        cls.group = Group.objects.create(
            title='Название',
            slug='test_slug',
            description='test_desc'
        )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.id,
            'text': 'Test_text',
            'image': uploaded
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(
            response, reverse('posts:profile', args=[self.user.username]))

        self.assertTrue(
            Post.objects.filter(
                group=form_data['group'],
                text=form_data['text'],
                image__endswith=form_data['image'].name
            ).exists()
        )

    def test_post_edit_apply_to_db(self):
        """Изменения поста отражаются в базе"""

        post = Post.objects.create(
            text='Тестовый текст',
            group=self.group,
            author=self.user
        )

        base = Post.objects.get(id=post.id)

        form_data = {
            'text': 'changed_text'
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=[self.user.id]),
            data=form_data,
            follow=True
        )
        result = Post.objects.get(id=post.id)

        self.assertEqual(result.text, form_data['text'])

        self.assertFalse(
            Post.objects.filter(
                text=base.text,
            ).exists()
        )


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            username='me'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='text'
        )

    def setUp(self):

        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_form(self):

        form_data = {
            'text': 'some_text'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=[self.post.id])
        )
        self.assertEqual(self.post.comments.all()[0].text, form_data['text'])
        first_object = response.context['comments'][0]
        self.assertEqual(first_object.text, form_data['text'])
