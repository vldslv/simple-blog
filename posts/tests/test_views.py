import tempfile
import shutil
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Group


User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.author = "BulletToothTony"
        cls.post_data = [cls.author, 1]
        cls.text = "Look in the dog"
        cls.user = User.objects.create_user(username=cls.author)
        cls.group = Group.objects.create(slug="snatch")
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client.post(
            reverse("new_post"),
            {"text": cls.text},
            follow=True
        )
        cls.test_gif = (b"\x47\x49\x46\x38\x39\x61\x02"
                b"\x00\x01\x00\x80\x00\x00\x00\x00\x00"
                b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00\x00"
                b"\x00\x00\x2C\x00\x00\x00\x00\x02\x00"
                b"\x01\x00\x00\x02\x02\x0C\x0A\x00\x3B"
        )
        cls.test_text = (b"\xd0\xa2\xd0\xb5\xd1\x85"
                b"\xd0\xbd\xd0\xbe\xd0\xbb\xd0"
                b"\xbe\xd0\xb3\xd0\xb8\xd0\xb8"
        )
        cls.unauthorized_client = Client()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_post_create(self):
        cache.clear()
        self.urls = [
            self.authorized_client.get(reverse("index")).content,
            self.authorized_client.get(reverse("profile", args=[self.author])).content,
            self.authorized_client.get(reverse("post", args=self.post_data)).content
        ]
        for url in self.urls:
            self.assertRegex(str(url), self.text)

    def test_post_edit(self):
        self.new_text = "I mean open him up"
        self.authorized_client.post(
            reverse("post_edit", args=self.post_data),
            {"text": self.new_text},
            follow=True
        )
        cache.clear()
        self.urls = [
            self.authorized_client.get(reverse("index")).content,
            self.authorized_client.get(reverse("profile", args=[self.author])).content,
            self.authorized_client.get(reverse("post", args=self.post_data)).content
        ]
        for url in self.urls:
            self.assertRegex(str(url), self.new_text)

    def test_image(self):
        uploaded = SimpleUploadedFile(
            name="test.gif",
            content=self.test_gif,
            content_type="image/gif"
        )
        self.authorized_client.post(
            reverse(
                "post_edit",
                args=self.post_data),
                {
                    "text": "Do you like dags?",
                    "image": uploaded,
                    "group": 1
                }
            )
        cache.clear()
        self.urls = [
            self.authorized_client.get(reverse("post", args=self.post_data)).content,
            self.authorized_client.get(reverse("index")).content,
            self.authorized_client.get(reverse("profile", args=[self.author])).content,
            self.authorized_client.get(reverse("group", args=[self.group.slug])).content
        ]
        for url in self.urls:
            self.assertRegex(str(url), "<img")

    def test_not_image_file(self):
        uploaded = SimpleUploadedFile(
            name="test.gif",
            content=self.test_text,
            content_type="image/gif"
        )
        error_text = (
            "Загрузите правильное изображение. "
            "Файл, который вы загрузили, "
            "поврежден или не является изображением."
        )
        response = self.authorized_client.post(
            reverse("new_post"),
            {"text": self.text, "image": uploaded},
            follow=True
        )
        self.assertFormError(response, "form", "image", error_text)

    def test_authorized_user_comment(self):
        response = self.authorized_client.post(
            reverse("add_comment", args=self.post_data),
            {"text": "You can call me Susan if it makes you happy"},
            follow=True
        )
        self.assertRedirects(
            response,
            reverse("post", args=self.post_data),
            status_code=302,
            target_status_code=200
        )
        self.assertRegex(
            str(self.authorized_client.get(
                reverse("post", args=self.post_data)).content
            ),
            "You can call me Susan if it makes you happy"
        )

    def test_cache(self):
        self.text_cache = "Do you know what nemesis means?"
        self.assertNotRegex(
            str(self.authorized_client.get(reverse("index")).content),
            self.text_cache
        )
        self.authorized_client.post(
            reverse("new_post"),
            {"text": self.text_cache},
            follow=True
        )
        self.assertNotRegex(
            str(self.authorized_client.get(reverse("index")).content),
            self.text_cache
        )
        cache.clear()
        self.assertRegex(
            str(self.authorized_client.get(reverse("index")).content),
            self.text_cache
        )
