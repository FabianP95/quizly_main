from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from user_auth_app.models import User

QUIZ_KEYS = {
    "id",
    "title",
    "description",
    "created_at",
    "updated_at",
    "video_url",
    "questions",
}

QUESTION_KEYS = {
    "id",
    "question_title",
    "question_options",
    "answer",
}


class QuizTests(APITestCase):

    def setUp(self):
        self.url = reverse("quiz-list")
        self.detail_quiz_url = reverse("quiz-detail", kwargs={"pk": self.quiz.id})
        self.user = User.objects.create_user(
            "testuser", "test@example.com", "Secret123!"
        )
        self.client.post(
            reverse("login"),
            {"username": "testuser", "password": "Secret123!"},
            format="json",
        )
        
    def test_get_quizzes(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_get_quizzes_without_cookies(self):
        self.client.cookies.clear()
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_get_orders_result_keys(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data[0].keys()), QUIZ_KEYS)