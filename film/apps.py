from django.apps import AppConfig


class FilmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'film'
    
    def ready(self):
        """
        Run startup tasks when Django initializes.
        Populates the cache with films on server start.
        """
        import os
        from django.core.cache import cache
        from .models import FilmCache
        from .serializers import FilmSerializer
        
        if os.environ.get('RUN_MAIN') == 'true':
            try:
                # Check if cache is empty
                cache_key = 'films_list'
                cached_data = cache.get(cache_key)
                
                if cached_data is None:
                    print('🚀 Populating cache on startup...')
                    
                    # Get films from database
                    films = FilmCache.objects.all().order_by('release_date')
                    
                    if films.exists():
                        # Prepare data
                        from .models import Film, Comments
                        films_data = []
                        for film in films:
                            comment_count = 0
                            try:
                                film_record = Film.objects.filter(title=film.title).first()
                                if film_record:
                                    comment_count = Comments.objects.filter(film=film_record).count()
                            except:
                                pass
                            
                            films_data.append({
                                'id': film.id,
                                'title': film.title,
                                'release_date': film.release_date,
                                'comment_count': comment_count
                            })
                        
                        # Serialize and cache
                        serializer = FilmSerializer(films_data, many=True)
                        cache.set(cache_key, serializer.data, 60 * 10)  # 10 minutes
                        print(f'✅ Cached {len(films_data)} films')
                    else:
                        print('⚠️  No films in database. Run: python manage.py sync_films')
                else:
                    print('✅ Cache already populated')
                    
            except Exception as e:
                print(f'⚠️  Could not populate cache on startup: {e}')
