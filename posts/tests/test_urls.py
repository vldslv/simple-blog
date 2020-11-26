from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post, Follow


User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.first_user = User.objects.create_user(username="MickeyONeil")
        cls.first_authorized_client = Client()        
        cls.first_authorized_client.force_login(cls.first_user)
        cls.second_user = User.objects.create_user(username="BorisYurinov")
        cls.second_authorized_client = Client()        
        cls.second_authorized_client.force_login(cls.second_user)
        cls.unauthorized_client = Client()
        cls.text = "You should never underestimate the predictability of stupidity"
        cls.first_authorized_client.post(
            reverse("new_post"),
            {"text": cls.text},
            follow=True
        )

    def test_homepage(self):
        response = self.unauthorized_client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_user_profile_page(self):
        response = self.first_authorized_client.get(
            reverse("profile", args=[self.first_user.username])
        )
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        current_posts_count = Post.objects.count()
        response = self.first_authorized_client.post(
            reverse("new_post"),
            {"text": "Did he have four fingers?"},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), current_posts_count + 1)

    def test_force_login(self):
        response = self.first_authorized_client.get(reverse("new_post"))      
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_user_newpage(self):
        response = self.unauthorized_client.post(
            reverse("new_post"),
            {"text": self.text},
            follow=True
        )
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('new_post')}",
            status_code=302,
            target_status_code=200
        )

    def test_404_page(self):
        response = self.unauthorized_client.get("/723fg7234/")
        self.assertEqual(response.status_code, 404)

    def test_subscribe(self):
        response = self.second_authorized_client.get(
            reverse("profile_follow", args=[self.first_user.username]),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse("profile", args=[self.first_user.username]),
            status_code=302,
            target_status_code=200
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.second_user,
                author=self.first_user
            ).exists()
        )
        self.assertRegex(
            str(self.second_authorized_client.get(reverse("follow_index")).content),
            self.text
        )

    def test_unsubscribe(self):
        response = self.second_authorized_client.get(
            reverse("profile_unfollow", args=[self.first_user.username]),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse("profile", args=[self.first_user.username]),
            status_code=302,
            target_status_code=200
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.second_user,
                author=self.first_user
            ).exists()
        )
        self.assertNotRegex(
            str(self.second_authorized_client.get(reverse("follow_index")).content),
            self.text
        )

    def test_unauthorized_user_comment(self):
        response = self.unauthorized_client.get(
            reverse("add_comment", args=[self.first_user.username, 1]),
            follow=True
        )
        self.assertRedirects(
            response,
            f"{reverse('login')}?next="
                f"{reverse('add_comment', args=[self.first_user.username, 1])}",
            status_code=302,
            target_status_code=200
        )
