

from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .models import FilmCache, Film, Comments
from .serializers import FilmSerializer, CommentSerializer
from .utils import getfilms


FILMS_CACHE_KEY = 'films_list'
CACHE_TTL = 60 * 10  # 10 minutes


class FilmsListView(APIView):
    """List all Star Wars films (cached)."""
    
    @extend_schema(
        summary="List all films",
        description="Get all Star Wars films with their comment counts. Results are cached for 10 minutes.",
        responses={
            200: FilmSerializer(many=True),
            500: OpenApiTypes.OBJECT,
        },
        tags=['Films']
    )
    def get(self, request):
        try:
            cached_data = cache.get(FILMS_CACHE_KEY)
            if cached_data is not None:
                return Response(cached_data, status=status.HTTP_200_OK)
            
            films = FilmCache.objects.all().order_by('release_date')
            
            films_data = [] 
            for film in films:
                comment_count = 0 # Comments Initialization
                try:
                    film_record = Film.objects.filter(title=film.title).first()
                    if film_record:
                        comment_count = Comments.objects.filter(film=film_record).count()
                except Exception as e:
                    print(f'Error counting comments: {e}')
                
                films_data.append({
                    'id': film.id,
                    'title': film.title,
                    'release_date': film.release_date,
                    'comment_count': comment_count
                })
            
            serializer = FilmSerializer(films_data, many=True)
            response_data = serializer.data
            
            cache.set(FILMS_CACHE_KEY, response_data, CACHE_TTL)
            print(f'Cached {len(response_data)} films')
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f'Error in FilmsListView: {e}')
            return Response(
                {
                    'error': 'An error occurred while fetching films',
                    'detail': str(e) if request.user.is_staff else 'Internal server error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FilmDetailView(APIView):
    """Get details for a specific film."""
    
    @extend_schema(
        summary="Get film details",
        description="Retrieve details for a specific film by its ID. Results are cached for 10 minutes.",
        parameters=[
            OpenApiParameter(
                name='film_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Film identifier from SWAPI (e.g., "1", "2")'
            ),
        ],
        responses={
            200: FilmSerializer,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        tags=['Films']
    )
    def get(self, request, film_id):
        try:
            cache_key = f'film_{film_id}'
            
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                print(f'Cache hit for film {film_id}')
                return Response(cached_data, status=status.HTTP_200_OK)
            
            print(f'Cache miss for film {film_id} - fetching from database')
            
            try:
                film = FilmCache.objects.get(film_id=film_id)
            except FilmCache.DoesNotExist:
                return Response(
                    {
                        'error': 'Film not found',
                        'detail': f'Film with ID "{film_id}" does not exist'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            comment_count = 0
            try:
                film_record = Film.objects.filter(title=film.title).first()
                if film_record:
                    comment_count = Comments.objects.filter(film=film_record).count()
            except Exception as e:
                print(f'Error counting comments: {e}')
            
            film_data = {
                'id': film.id,
                'title': film.title,
                'release_date': film.release_date,
                'comment_count': comment_count
            }
            
            serializer = FilmSerializer(film_data)
            response_data = serializer.data
            
            cache.set(cache_key, response_data, CACHE_TTL)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f'Error in FilmDetailView: {e}')
            return Response(
                {
                    'error': 'An error occurred while fetching film details',
                    'detail': str(e) if request.user.is_staff else 'Internal server error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class CommentsListView(APIView):
    """List all comments for a specific film (ordered by creation time)."""
    
    @extend_schema(
        summary="List film comments",
        description="Get all comments for a specific film, ordered by creation time (oldest first).",
        parameters=[
            OpenApiParameter(
                name='film_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Film database ID'
            ),
        ],
        responses={
            200: CommentSerializer(many=True),
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        tags=['Comments']
    )
    def get(self, request, film_id):
        try:
            try:
                film = Film.objects.get(id=film_id)
            except Film.DoesNotExist:
                return Response(
                    {
                        'error': 'Film not found',
                        'detail': f'Film with ID {film_id} does not exist'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            comments = Comments.objects.filter(film=film).order_by('created_at')
            serializer = CommentSerializer(comments, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f'Error in CommentsListView: {e}')
            return Response(
                {
                    'error': 'An error occurred while fetching comments',
                    'detail': str(e) if request.user.is_staff else 'Internal server error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class CommentCreateView(APIView):
    """Create a new comment for a film."""
    
    @extend_schema(
        summary="Create a comment",
        description="Add a new comment to a film. Comment must be 1-500 characters.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'comment': {
                        'type': 'string',
                        'maxLength': 500,
                        'description': 'Comment text (1-500 characters)'
                    },
                    'film': {
                        'type': 'integer',
                        'description': 'Film database ID'
                    }
                },
                'required': ['comment', 'film']
            }
        },
        examples=[
            OpenApiExample(
                'Valid Comment',
                value={'comment': 'Best Star Wars movie!', 'film': 1},
                request_only=True,
            ),
        ],
        responses={
            201: CommentSerializer,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
        tags=['Comments']
    )
    def post(self, request):
        try:
            film_id = request.data.get('film')
            if not film_id:
                return Response(
                    {
                        'error': 'Validation error',
                        'detail': 'film ID is required'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                film_id = int(film_id)
            except (ValueError, TypeError):
                return Response(
                    {
                        'error': 'Validation error',
                        'detail': 'film ID must be a valid integer'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                film = Film.objects.get(id=film_id)
            except Film.DoesNotExist:
                return Response(
                    {
                        'error': 'Film not found',
                        'detail': f'Film with ID {film_id} does not exist'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            comment_text = request.data.get('comment')
            if not comment_text:
                return Response(
                    {
                        'error': 'Validation error',
                        'detail': 'comment text is required'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            comment_text = str(comment_text).strip()
            
            if not comment_text:
                return Response(
                    {
                        'error': 'Validation error',
                        'detail': 'comment cannot be empty or whitespace only'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(comment_text) > 500:
                return Response(
                    {
                        'error': 'Validation error',
                        'detail': f'Comment cannot exceed 500 characters (current: {len(comment_text)})'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            comment = Comments.objects.create(
                film=film,
                comment=comment_text
            )
            
            cache.delete(FILMS_CACHE_KEY)
            
            response_serializer = CommentSerializer(comment)
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            print(f'Error in CommentCreateView: {e}')
            return Response(
                {
                    'error': 'An error occurred while creating the comment',
                    'detail': str(e) if request.user.is_staff else 'Internal server error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthCheckView(APIView):
    """Health check endpoint for monitoring."""
    
    @extend_schema(
        summary="Health check",
        description="Check if the API is running and database is accessible.",
        responses={
            200: OpenApiTypes.OBJECT,
            503: OpenApiTypes.OBJECT,
        },
        tags=['System']
    )
    def get(self, request):
        """Check API health and database connectivity."""
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            return Response({
                'status': 'healthy',
                'database': 'connected'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

     