from django.db import models


class Film(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    release_date = models.DateField()
    comment_count = models.IntegerField(default=0)


class FilmCache(models.Model):
    """Stores film metadata from SWAPI."""
    film_id = models.CharField(max_length=10, unique=True, db_index=True)
    title = models.CharField(max_length=200)
    release_date = models.DateField()
    last_synced_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['release_date']
        verbose_name = 'Film Cache'
        verbose_name_plural = 'Film Caches'
    
    def __str__(self):
        return f"{self.title} ({self.film_id})"

class Comments(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE)
    comment = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
    
    def __str__(self):
        return f"{self.comment}"