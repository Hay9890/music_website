from django.urls import path
from . import views

urlpatterns = [
    # Trang chủ
    path("", views.home, name="home"),

    # Đăng ký, đăng nhập, đăng xuất
    path("register/", views.register, name="register"),
    path("login/", views.login_views, name="login"),
    path("logout/", views.logout_views, name="logout"),

    # Trang chơi nhạc
    path("track/<int:track_id>/", views.play_track, name="play_track"),

    # Thêm / bỏ yêu thích (toggle) - AJAX
    path("favorite/add/", views.add_favorite, name="add_favorite"),
    # Danh sách bài hát yêu thích
    path("favorite/", views.favorite_list, name="favorite_list"),

# urls.py
path(
    "playlist/add-to-user/<int:track_id>/<int:playlist_id>/",
    views.add_to_playlist,
    name="add_to_playlist"
),

    # Danh sách playlist của người dùng
    path("playlist/", views.playlist_list, name="playlist_list"),

    # AI chat gợi ý
    path("chat-ai/", views.chat_ai, name="chat_ai"),
path("upgrade/", views.upgrade_page, name="upgrade_page"),                  # Trang điều khoản + chọn gói
    path("upgrade/start/", views.start_payment, name="start_payment"),          # Chọn phương thức thanh toán
    path("upgrade/confirm/", views.confirm_payment, name="confirm_payment"),    # Xác nhận thanh toán (mock)
]
