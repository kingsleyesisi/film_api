from rest_framework import serializers
from .models import FilmCache, Comments


class FilmSerializer(serializers.Serializer):
    """Serializer for film data"""
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=200)
    release_date = serializers.DateField()
    comment_count = serializers.IntegerField(default=0)


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments."""
    film_title = serializers.CharField(source='film.title', read_only=True)
    
    class Meta:
        model = Comments
        fields = ['id', 'comment', 'created_at', 'film_title']
        read_only_fields = ['id', 'created_at', 'film_title']
    
    def validate_comment(self, value):
        if len(value) > 500:
            raise serializers.ValidationError(
                "Comment cannot exceed 500 characters."
            )
        return value
