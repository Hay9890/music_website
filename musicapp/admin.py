from django.contrib import admin
from .models import Song, Artist, Favorite, PlayList

# Đăng ký Artist
@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'country')
    search_fields = ('name',)

# Đăng ký Song
@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'genre', 'release_date')
    search_fields = ('title', 'artist__name')
    list_filter = ('genre', 'release_date')

# Đăng ký Favorite
@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'added_at')
    search_fields = ('user__username', 'song__title')
    list_filter = ('added_at',)

# Đăng ký PlayList
@admin.register(PlayList)
class PlayListAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username')
    filter_horizontal = ('songs',)  # Cho phép chọn nhiều song dễ dàng
    list_filter = ('created_at',)
