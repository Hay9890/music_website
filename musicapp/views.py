import json
import os
import hashlib
import hmac
import uuid
import urllib.parse
import pytz
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponseRedirect, JsonResponse
import requests
from dotenv import load_dotenv

from .forms import CustomUserCreationForm, FavoriteForm
from .models import Song, Favorite, Playlist, Subscription

# =======================
# Load env
load_dotenv()

VNP_URL = os.getenv("VNP_URL", "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html")
VNP_TMN_CODE = os.getenv("VNP_TMN_CODE", "")
VNP_HASH_SECRET = os.getenv("VNP_HASH_SECRET", "")
VNP_RETURN_URL = os.getenv("VNP_RETURN_URL", "http://127.0.0.1:8000/upgrade/confirm/")

# =======================
# Home page + search + filter genre
def home(request):
    query = request.GET.get('q', '').strip()
    selected_genre = request.GET.get('genre', '')

    songs = Song.objects.all()
    if query:
        songs = songs.filter(title__icontains=query) | songs.filter(artist__name__icontains=query)
    if selected_genre:
        songs = songs.filter(genre__iexact=selected_genre)

    genres = Song.objects.values_list('genre', flat=True).distinct()
    favorite_song_ids = []

    if request.user.is_authenticated:
        favorite_song_ids = Favorite.objects.filter(user=request.user).values_list('song_id', flat=True)
        user_playlists = Playlist.objects.filter(user=request.user)
    else:
        user_playlists = []   # <<< thêm dòng này

    favorite_forms = {song.id: FavoriteForm(initial={'song': song.id}) for song in songs}

    return render(request, 'home.html', {
        'songs': songs,
        'query': query,
        'genres': genres,
        'selected_genre': selected_genre,
        'favorite_song_ids': favorite_song_ids,
        'favorite_forms': favorite_forms,
        'user_playlists': user_playlists,
    })

# =======================
# Authentication
def login_views(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data["username"],
                                password=form.cleaned_data["password"])
            if user:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect("home")
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            playlist = Playlist(user=user, name="My Playlist")
            playlist.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect("home")
    else:
        form = CustomUserCreationForm()
    return render(request, "register.html", {"form": form})

def logout_views(request):
    logout(request)
    messages.info(request, "You have been logged out")
    return redirect("login")

# =======================
# Play music
@login_required
def play_track(request, track_id):
    sub = Subscription.objects.filter(user=request.user).first()
    is_premium = sub and sub.is_active

    api_url = f"https://discoveryprovider.audius.co/v1/tracks?id={track_id}&app_name=musicapp"
    try:
        resp = requests.get(api_url, timeout=8)
        data_json = resp.json()

        if "data" not in data_json or not data_json["data"]:
            return render(request, "error.html", {"message": "Không tìm thấy bài hát này."})

        data = data_json["data"][0]
        art = data.get("artwork") or {}
        artwork = art.get("1000x1000") or art.get("480x480") or ""
        artist = (data.get("user") or {}).get("name", "Unknown Artist")
        stream_url = f"https://discoveryprovider.audius.co/v1/tracks/{track_id}/stream"

        track = {
            "title": data.get("title", "Unknown"),
            "artist": artist,
            "image": artwork,
            "stream_url": stream_url,
            "is_premium": is_premium,
        }

        if not is_premium:
            return render(request, "ads.html", {"track": track})

        return render(request, "play_track.html", {"track": track})

    except Exception as e:
        print("Audius API error:", e)
        return render(request, "error.html", {"message": "Không thể kết nối API."})

# =======================
# Toggle favorite
@login_required
def add_favorite(request):
    if request.method != "POST":
        return JsonResponse({"success": False}, status=405)

    data = json.loads(request.body) if request.content_type == "application/json" else request.POST
    song_id = data.get('song_id') or data.get('song')
    song = get_object_or_404(Song, id=song_id)

    favorite_qs = Favorite.objects.filter(user=request.user, song=song)
    if favorite_qs.exists():
        favorite_qs.delete()
        is_favorite = False
    else:
        Favorite.objects.create(user=request.user, song=song)
        is_favorite = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"success": True, "song_id": song.id, "is_favorite": is_favorite})

    messages.success(request,
                     f"{'Đã thêm' if is_favorite else 'Đã bỏ'} {song.title} {'vào' if is_favorite else 'khỏi'} yêu thích!")
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# =======================
# Favorite list
@login_required
def favorite_list(request):
    favorite_songs = Favorite.objects.filter(user=request.user).select_related('song')
    return render(request, "favorite.html", {"favorite_songs": favorite_songs})
#=======
@login_required
def create_and_add_playlist(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = json.loads(request.body)
        song_id = data.get('song')
        playlist_name = data.get('name')
        playlist_id = data.get('playlist_id')

        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Bài hát không tồn tại!'})

        if playlist_id:  # thêm vào playlist cũ
            try:
                playlist = Playlist.objects.get(id=playlist_id, user=request.user)
            except Playlist.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Playlist không tồn tại!'})
        elif playlist_name:  # tạo playlist mới
            playlist = Playlist.objects.create(user=request.user, name=playlist_name)
        else:
            return JsonResponse({'success': False, 'message': 'Playlist không hợp lệ!'})

        if song.id not in playlist.songs:
            playlist.songs.append(song.id)
            playlist.save()

        return JsonResponse({'success': True, 'message': 'Đã thêm bài hát vào playlist!'})

    return JsonResponse({'success': False, 'message': 'Yêu cầu không hợp lệ!'})

# Playlist: add song
@login_required
def add_to_playlist(request, playlist_id, song_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    song = get_object_or_404(Song, id=song_id)

    # Kiểm tra bài hát đã có trong playlist chưa
    if any(s['id'] == song.id for s in playlist.songs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "message": "Bài hát đã có trong playlist!"})
        else:
            return redirect("playlist_list")

    # Thêm bài hát vào playlist
    playlist.songs.append({
        "id": song.id,
        "title": song.title,
        "artist": song.artist.name if hasattr(song.artist, 'name') else str(song.artist),
        "audio": song.audio_file.url,
    })
    playlist.save()

    # Nếu AJAX request → trả JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"success": True, "message": "Đã thêm bài hát vào playlist!"})

    # Nếu không phải AJAX → redirect
    return redirect("playlist_list")
# =======================
# Playlist list
@login_required
def playlist_list(request):
    playlists = Playlist.objects.filter(user=request.user)

    for playlist in playlists:
        new_songs = []
        for song_id in playlist.songs:  # songs là list ID
            try:
                song_obj = Song.objects.get(id=song_id)
                new_songs.append(song_obj)
            except Song.DoesNotExist:
                continue
        playlist.songs = new_songs  # giờ playlist.songs là object Song thật

    return render(request, "playlist.html", {"playlists": playlists})
#=====
@login_required
def delete_playlist(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    playlist.delete()
    messages.success(request, "Đã xóa playlist thành công!")
    return redirect("playlist_list")
# =======================
# Upgrade Page
@login_required
def upgrade_page(request):
    plans = [
        {"id": "month", "label": "1 Tháng", "price": 99000, "days": 30},
        {"id": "6months", "label": "6 Tháng", "price": 499000, "days": 180},
        {"id": "year", "label": "1 Năm", "price": 899000, "days": 365},
    ]
    terms = [
        "Nghe nhạc không quảng cáo, chất lượng lossless.",
        "Tải xuống bài hát không giới hạn.",
        "Không hoàn tiền cho chu kỳ đã thanh toán (bản demo).",
        "Khi thanh toán, bạn đồng ý với Điều khoản & Chính sách bảo mật.",
    ]
    return render(request, "upgrade.html", {"plans": plans, "terms": terms})

# =======================
# Start Payment (VNPay chuẩn)
def start_payment(request):
    if request.method != "POST":
        return redirect("upgrade_page")

    # --- 1️⃣ Kiểm tra gói đăng ký ---
    plan_id = request.POST.get("plan_id")
    plan_map = {
        "month": {"label": "1 Tháng", "price": 99000, "days": 30},
        "6months": {"label": "6 Tháng", "price": 499000, "days": 180},
        "year": {"label": "1 Năm", "price": 899000, "days": 365},
    }
    plan = plan_map.get(plan_id)
    if not plan:
        messages.error(request, "❌ Gói không hợp lệ.")
        return redirect("upgrade_page")

    # --- 2️⃣ Lưu session ---
    request.session["pending_payment"] = plan

    # --- 3️⃣ Chuẩn bị dữ liệu VNPay ---
    txn_ref = str(uuid.uuid4().hex)[:20]  # Mã giao dịch duy nhất
    tz = pytz.timezone('Asia/Ho_Chi_Minh')
    vnp_create_date = datetime.now(tz).strftime("%Y%m%d%H%M%S")

    params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": VNP_TMN_CODE,
        "vnp_Amount": plan["price"] * 100,  # VND * 100
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": txn_ref,
        "vnp_OrderInfo": f"Thanh toan goi {plan['label']}",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": VNP_RETURN_URL,
        "vnp_IpAddr": request.META.get("REMOTE_ADDR", "127.0.0.1"),
        "vnp_CreateDate": vnp_create_date,
    }

    # --- 4️⃣ Tạo chuỗi hash (raw values, chưa encode) ---
    sorted_keys = sorted(params.keys())
    hash_data = "&".join(f"{k}={str(params[k])}" for k in sorted_keys)
    vnp_secure_hash = hmac.new(
        VNP_HASH_SECRET.encode(),
        hash_data.encode(),
        hashlib.sha512
    ).hexdigest()

    # --- 5️⃣ Tạo URL thanh toán (encode khi redirect) ---
    query = "&".join(f"{k}={urllib.parse.quote_plus(str(params[k]))}" for k in sorted_keys)
    payment_url = f"{VNP_URL}?{query}&vnp_SecureHash={vnp_secure_hash}"

    # --- 6️⃣ Điều hướng sang VNPay ---
    return HttpResponseRedirect(payment_url)

# =======================
# Confirm Payment
def confirm_payment(request):
    vnp_status = request.GET.get("vnp_TransactionStatus")
    vnp_message = ""

    if vnp_status == "00":
        vnp_message = "🎉 Thanh toán thành công!"
    else:
        vnp_message = "❌ Thanh toán thất bại hoặc bị hủy."

    # Xóa pending session (không dùng để kích hoạt)
    if "pending_payment" in request.session:
        del request.session["pending_payment"]

    return render(request, "payment_success.html", {
        "status": vnp_status,
        "message": vnp_message,
    })

# =======================
# Chat AI by mood
def chat_ai(request):
    mood = request.GET.get("mood", "").lower()
    mood_map = {
        "vui": "Pop, EDM, Dance",
        "buồn": "Lofi, Ballad, Acoustic",
        "cô đơn": "Lofi, Indie, Sad Chill",
        "tức giận": "Rock, Metal, Rap",
        "thư giãn": "Chill, Jazz, Ambient",
        "yêu": "Love songs, R&B, Acoustic",
        "mệt": "Chill, Lofi, Ambient",
    }

    suggestion = "Hmm... tôi chưa rõ tâm trạng bạn 😅, hãy nói 'tôi vui', 'tôi buồn' hoặc 'tôi mệt' nhé!"
    for key, genres in mood_map.items():
        if key in mood:
            suggestion = f"🎧 Có vẻ bạn đang {key}, tôi gợi ý bạn nghe: {genres}"
            break

    return JsonResponse({"reply": suggestion})
