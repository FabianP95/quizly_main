from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from quiz_app.models import Quiz

from .permissions import IsCreator
from .serializers import QuizPostSerializer, QuizSerializer
from .services import QuizGenerationError, generate_quiz_from_url


class QuizView(viewsets.ModelViewSet):

    def get_queryset(self):
        """Return the queryset depending on the current action.

        Returns:
            QuerySet: Only the quizzes of the current user for "list", otherwise
            all quizzes, so that the permission check can return 403 instead of 404.
        """
        if self.action == "list":
            return Quiz.objects.filter(creator=self.request.user)
        else:
            return Quiz.objects.all()

    def get_serializer_class(self):
        """Return the serializer class depending on the current action.

        Returns:
            type: QuizPostSerializer for "create", otherwise QuizSerializer.
        """
        if self.action == "create":
            return QuizPostSerializer
        return QuizSerializer

    def create(self, request, *args, **kwargs):
        """Validate the url, generate a quiz from it and save it.

        Args:
            request: The incoming request containing the "url" field.

        Returns:
            Response: 201 with the created quiz, 400 if the url is invalid or
            500 if the quiz generation failed.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data["video_url"]
        try:
            quiz_data = generate_quiz_from_url(url)
        except QuizGenerationError as error:
            return Response(
                 {"detail": f"Error {error.status_code}: {error}"},
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
        """Return the permissions depending on the current action.

        Returns:
            list: IsAuthenticated and IsCreator for object actions (retrieve,
            update, partial_update, destroy), otherwise only IsAuthenticated.
        """

        if self.action in ("retrieve", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsCreator()]
        return [IsAuthenticated()]
