"""
Django management command to sync films from SWAPI.

Usage:
    python manage.py sync_films

This command fetches film data from the SWAPI API and stores it locally
in the FilmCache table, updating the last_synced_at timestamp.
It also invalidates the films list cache to ensure fresh data on next request.
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone
from film.models import FilmCache
from film.utils import getfilms


class Command(BaseCommand):
    help = 'Sync films from SWAPI and update the local cache'

    def handle(self, *args, **options):
        """
        Fetch films from SWAPI and upsert into FilmCache table.
        """
        self.stdout.write('Starting film sync...')
        
        swapi_url = 'https://swapi.info/api/films/'
        films_data = getfilms(swapi_url)
        
        if isinstance(films_data, str):
            self.stdout.write(self.style.ERROR(f'Failed to fetch films: {films_data}'))
            return
        
        synced_count = 0
        updated_count = 0
        created_count = 0
        
        for film_data in films_data:
            film_id = str(synced_count + 1)
            
            film_cache, created = FilmCache.objects.update_or_create(
                film_id=film_id,
                defaults={
                    'title': film_data.get('title', ''),
                    'release_date': film_data.get('release_date', timezone.now().date()),
                    # last_synced_at is automatically updated by auto_now=True
                }
            )
            
            synced_count += 1
            if created:
                created_count += 1
            else:
                updated_count += 1
            
            self.stdout.write(f'  {"Created" if created else "Updated"}: {film_cache.title}')
        
        # Invalidate the films list cache key
        cache_key = 'films_list'
        cache.delete(cache_key)
        self.stdout.write(self.style.WARNING(f'Invalidated cache key: {cache_key}'))
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSync complete! Total: {synced_count}, '
                f'Created: {created_count}, Updated: {updated_count}'
            )
        )
