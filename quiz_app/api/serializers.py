import re
from rest_framework import serializers

from quiz_app.models import Quiz, Question

YOUTUBE_URL_PATTERN = (
    r"^https://"
    r"(?:[\w-]+\.)?"
    r"(?:youtube\.com|youtu\.be)/"
    r"(?:watch\?(?:.*&)?v=|shorts/|embed/)?"
    r"([A-Za-z0-9_-]{11})"
)


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "question_title",
            "question_options",
            "answer",
        ]


class QuestionPostSerializer(QuestionSerializer):
    class Meta(QuestionSerializer.Meta):
        fields = QuestionSerializer.Meta.fields + [
            "created_at",
            "updated_at",
        ]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    video_url = serializers.CharField(read_only=True)
    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]


class QuizPostSerializer(QuizSerializer):
    questions = QuestionPostSerializer(many=True, read_only=True)
    url = serializers.CharField(source="video_url", write_only=True)

    class Meta(QuizSerializer.Meta):
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
            "url"
        ]
        read_only_fields = ["title", "description", "video_url"]

    def validate_url(self, value):

        test = re.match(YOUTUBE_URL_PATTERN, value)
        if test is None:
            raise serializers.ValidationError("Only links from Youtube are allowed")
        video_id = test.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
