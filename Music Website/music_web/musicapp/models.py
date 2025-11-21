from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Artist(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    genre = models.CharField(max_length=50, blank=True, null=True)
    duration = models.FloatField(help_text="Độ dài (phút)", blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)

    audio_file = models.FileField(
        upload_to='audio/',
        blank=True,
        null=True,
        help_text="Tải lên file MP3 của bài hát"
    )

    cover_image = models.ImageField(
        upload_to='song_covers/',
        blank=True,
        null=True,
        help_text="Ảnh bìa bài hát"
    )

    def __str__(self):
        return self.title


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'song')

    def __str__(self):
        return f"{self.user.username} ❤️ {self.song.title}"


class PlayList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="playlists")
    name = models.CharField(max_length=100)
    songs = models.ManyToManyField("Song", blank=True, related_name="in_playlists")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
class Subscription(models.Model):
    PLAN_CHOICES = [
        ('FREE', 'Free'),
        ('PREMIUM', 'Premium'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='FREE')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.plan}"

    def is_valid(self):
        """
        Kiểm tra xem gói Premium còn hiệu lực hay không.
        """
        return self.is_active and self.end_date and self.end_date > timezone.now()