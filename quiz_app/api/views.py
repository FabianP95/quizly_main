from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from quiz_app.models import Question, Quiz
from .serializers import QuizSerializer, QuizPostSerializer
from .permissions import IsCreator


class QuizView(viewsets.ModelViewSet):

    def get_queryset(self):
        user = self.request.user
        return Quiz.objects.filter(creator=user)

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
