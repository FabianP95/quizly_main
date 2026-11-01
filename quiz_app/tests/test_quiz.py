from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from quiz_app.models import Question, Quiz
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

QUESTION_KEYS_CREATE = QUESTION_KEYS | {"created_at", "updated_at"}

VIDEO_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
SERVICE_PATH = "quiz_app.api.views.generate_quiz_from_url"


def create_quiz(creator, title):

    quiz = Quiz.objects.create(
        creator=creator,
        title=title,
        description="Some description",
        video_url=VIDEO_URL,
    )
    for i in range(2):
        Question.objects.create(
            quiz=quiz,
            question_title=f"Question {i}",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )
    return quiz


class QuizTestsBase(APITestCase):

    def setUp(self):
        self.url = reverse("quizzes-list")

        self.user = User.objects.create_user(
            "testuser", "test@example.com", "Secret123!"
        )
        self.second_user = User.objects.create_user(
            "seconduser", "test@example.de", "Secret123!"
        )

        self.quiz = create_quiz(self.user, "My Quiz")
        self.second_quiz = create_quiz(self.second_user, "Second Quiz")
        self.client.post(
            reverse("login"),
            {"username": "testuser", "password": "Secret123!"},
            format="json",
        )
        self.detail_quiz_url = reverse("quizzes-detail", kwargs={"pk": self.quiz.id})


class QuizListTests(QuizTestsBase):
    def test_get_quizzes(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_quizzes_without_cookies(self):
        self.client.cookies.clear()
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_quizzes_result_keys(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(set(response.data[0].keys()), QUIZ_KEYS)
        self.assertEqual(set(response.data[0]["questions"][0].keys()), QUESTION_KEYS)

    def test_get_only_own_quizzes(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.data[0]["id"], self.quiz.id)
        self.assertNotEqual(response.data[0]["id"], self.second_quiz.id)

    def test_get_questions_belonging_to_quiz(self):
        response = self.client.get(self.url, format="json")
        self.assertEqual(len(response.data[0]["questions"]), 2)
        

class QuizCreateTests(QuizTestsBase):
    
    def service_function_offline(self, *args, **kwargs):
        
        return create_quiz(self.user, "Offline Quiz")
        
    def test_create_quiz(self):
        with patch(SERVICE_PATH, side_effect=self.service_function_offline) as mock:
            response = self.client.post(
                self.url, {"url": VIDEO_URL}, format="json"
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock.assert_called_once()
    
    def test_create_quiz_result_keys(self):
        with patch(SERVICE_PATH, side_effect=self.service_function_offline):
            response = self.client.post(
                self.url, {"url": VIDEO_URL}, format="json"
            )
        self.assertEqual(set(response.data.keys()), QUIZ_KEYS)
        self.assertEqual(
            set(response.data["questions"][0].keys()), QUESTION_KEYS_CREATE
        )

    def test_create_quiz_without_cookies(self):
        self.client.cookies.clear()
        response = self.client.post(
            self.url, {"url": VIDEO_URL}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_quiz_missing_url(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_quiz_invalid_url(self):
        response = self.client.post(
            self.url, {"url": "not-a-url"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_quiz_non_youtube_url(self):
        response = self.client.post(
            self.url, {"url": "https://example.com/video"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        

