from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from quiz_app.models import Quiz

from .permissions import IsCreator
from .serializers import QuizPostSerializer, QuizSerializer
from .services import QuizGenerationError, generate_quiz_from_url


class QuizView(viewsets.ModelViewSet):

    def get_queryset(self):
        if self.action == "list":
            return Quiz.objects.filter(creator=self.request.user)
        else:
            return Quiz.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return QuizPostSerializer
        return QuizSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data["video_url"]
        try:
            quiz_data = generate_quiz_from_url(url)
        except QuizGenerationError:
            return Response(
                {"detail": "Something went wrong in generating the quiz"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer.save(
            creator=self.request.user,
            title=quiz_data["title"],
            description=quiz_data["description"],
            questions=quiz_data["questions"],
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_permissions(self):

        if self.action in ("retrieve", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsCreator()]
        return [IsAuthenticated()]
