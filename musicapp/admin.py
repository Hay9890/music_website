from django.contrib import admin
from .models import Song, Artist, Favorite, Playlist

# =========================
# ARTIST
# =========================
@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    search_fields = ('name',)

# =========================
# SONG
# =========================
@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'genre', 'release_date')
    search_fields = ('title', 'artist__name')
    list_filter = ('genre', 'release_date')

# =========================
# FAVORITE
# =========================
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'added_at')
    search_fields = ('user__username', 'song__title')
    list_filter = ('added_at',)

# =========================
# PLAYLIST
# =========================
@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username')
    # Không dùng filter_horizontal vì songs là JSONField
    list_filter = ('created_at',)
