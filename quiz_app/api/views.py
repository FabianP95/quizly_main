from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from quiz_app.models import Question, Quiz
from .serializers import QuizSerializer, QuizPostSerializer
from .permissions import IsCreator
from .services import generate_quiz_from_url



class QuizView(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()

    def get_serializer_class(self):

        if self.action == "create":
            return QuizPostSerializer
        return QuizSerializer

    def perform_create(self, serializer):

        serializer.save(creator=self.request.user)

    def get_permissions(self):

        if self.action == "retrieve":
            return [IsAuthenticated(), IsCreator()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsCreator()]
        return [IsAuthenticated()]
