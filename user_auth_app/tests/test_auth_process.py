from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from user_auth_app.models import User


class RegistrationTests(APITestCase):
    def setUp(self):
        """Set the registration url and valid registration data."""
        self.url = reverse("registration")
        self.valid_data = {
            "username": "testuser",
            "password": "Secret123!",
            "confirmed_password": "Secret123!",
            "email": "test@example.com",
        }

    def test_register_success(self):
        """Test that a valid registration returns 201 and creates the user."""
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {"detail": "User created successfully!"})
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_password_is_hashed(self):
        """Test that the password is stored hashed and not in plain text."""
        self.client.post(self.url, self.valid_data, format="json")
        user = User.objects.get(username="testuser")
        self.assertNotEqual(user.password, "Secret123!")
        self.assertTrue(user.check_password("Secret123!"))

    def test_register_passwords_do_not_match(self):
        """Test that different passwords return 400 with a confirmed_password error."""
        self.valid_data["confirmed_password"] = "Other123!"
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirmed_password", response.data)

    def test_register_duplicate_email_case_insensitive(self):
        """Test that an already used email (case insensitive) returns 400."""
        User.objects.create_user("other", "TEST@example.com", "Secret123!")
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_duplicate_username(self):
        """Test that an already used username returns 400."""
        User.objects.create_user("testuser", "x@example.com", "Secret123!")
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_register_missing_fields(self):
        """Test that a missing required field returns 400."""
        for field in ["username", "password", "confirmed_password", "email"]:
            data = self.valid_data.copy()
            data.pop(field)
            response = self.client.post(self.url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, field)

    def test_password_not_in_response(self):
        """Test that the password is not returned in the response."""
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertNotIn("password", response.data)


class LoginTests(APITestCase):
    def setUp(self):
        """Set the login url and create a test user."""
        self.url = reverse("login")
        self.user = User.objects.create_user("testuser", "test@example.com", "Secret123!")

    def test_login_success_sets_cookies(self):
        """Test that a valid login returns the user data and sets httponly auth cookies."""
        response = self.client.post(
            self.url, {"username": "testuser", "password": "Secret123!"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Login successfully!")
        self.assertEqual(
            response.data["user"],
            {"id": self.user.id, "username": "testuser", "email": "test@example.com"},
        )
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])

    def test_tokens_not_in_body(self):
        """Test that the tokens are not returned in the response body."""
        response = self.client.post(
            self.url, {"username": "testuser", "password": "Secret123!"}, format="json"
        )
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_wrong_password(self):
        """Test that a wrong password returns 401 and sets no cookie."""
        response = self.client.post(
            self.url, {"username": "testuser", "password": "wrong"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", response.cookies)

    def test_login_unknown_user(self):
        """Test that an unknown username returns 401."""
        response = self.client.post(
            self.url, {"username": "nobody", "password": "Secret123!"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self):
        """Test that a login without credentials returns 401."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTestCase(APITestCase):
    """Base class that logs in a user, so the test client holds the auth cookies."""

    def setUp(self):
        """Create a test user and log in to set the auth cookies."""
        self.user = User.objects.create_user("testuser", "test@example.com", "Secret123!")
        self.client.post(
            reverse("login"),
            {"username": "testuser", "password": "Secret123!"},
            format="json",
        )


class LogoutTests(AuthenticatedTestCase):
    def setUp(self):
        """Log in the test user and set the logout url."""
        super().setUp()
        self.url = reverse("logout")

    def test_logout_success_deletes_cookies(self):
        """Test that a logout returns 200 and empties both auth cookies."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid.",
        )
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")

    def test_refresh_token_blacklisted_after_logout(self):
        """Test that the refresh token can not be used anymore after logout."""
        refresh_token = self.client.cookies["refresh_token"].value
        self.client.post(self.url)
        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post(reverse("token_refresh"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_auth(self):
        """Test that a logout without auth cookies returns 401."""
        self.client.cookies.clear()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_access_token(self):
        """Test that a logout with an invalid access token returns 401."""
        self.client.cookies["access_token"] = "invalid"
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenRefreshTests(AuthenticatedTestCase):
    def setUp(self):
        """Log in the test user and set the token refresh url."""
        super().setUp()
        self.url = reverse("token_refresh")

    def test_refresh_success(self):
        """Test that a valid refresh returns 200 and sets a new httponly access cookie."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "Token refreshed"})
        self.assertIn("access_token", response.cookies)
        self.assertNotEqual(response.cookies["access_token"].value, "")
        self.assertTrue(response.cookies["access_token"]["httponly"])

    def test_refresh_without_cookie(self):
        """Test that a refresh without refresh token cookie returns 401."""
        self.client.cookies.clear()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_invalid_cookie(self):
        """Test that a refresh with an invalid refresh token returns 401."""
        self.client.cookies["refresh_token"] = "invalid"
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)