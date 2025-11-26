from django.urls import path
from . import views

urlpatterns = [
    # Trang chủ
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.login_views, name="login"),
    path("logout/", views.logout_views, name="logout"),
    path("track/<int:track_id>/", views.play_track, name="play_track"),
    path("favorite/add/", views.add_favorite, name="add_favorite"),
    path("favorite/", views.favorite_list, name="favorite_list"),
    path("chat-ai/", views.chat_ai, name="chat_ai"),
    path("upgrade/", views.upgrade_page, name="upgrade_page"),
    path("playlist/add/<int:playlist_id>/<int:song_id>/",views.add_to_playlist,name="add_to_playlist"),
    path("playlist/", views.playlist_list, name="playlist_list"),
path('playlist/create-and-add/', views.create_and_add_playlist, name='create-and-add-playlist'),
path("playlist/delete/<int:playlist_id>/", views.delete_playlist, name="delete_playlist"),
    path("upgrade/start/", views.start_payment, name="start_payment"),
    path("upgrade/confirm/", views.confirm_payment, name="confirm_payment"),

]
