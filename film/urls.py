from django.urls import path 
from . import views

urlpatterns = [
    path('films/', views.FilmsListView.as_view(), name='films-list'),
    path('films/<int:film_id>/', views.FilmDetailView.as_view(), name='film-detail'),
    path('films/<int:film_id>/comments/', views.CommentsListView.as_view(), name='list-comments'),
    path('comments/', views.CommentCreateView.as_view(), name='create-comment'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
]