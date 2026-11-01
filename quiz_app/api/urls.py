from django.urls import include, path
from rest_framework import routers

from .views import QuizView

router = routers.SimpleRouter()
router.register(r"quizzes", QuizView, basename="quizzes")

urlpatterns = [
    path("", include(router.urls))]