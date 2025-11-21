from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Favorite

# ========================
# Form đăng ký user
# ========================
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email address",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


# ========================
# Form thêm bài yêu thích
# ========================
class FavoriteForm(forms.ModelForm):
    class Meta:
        model = Favorite
        fields = ['song']  # user sẽ lấy từ request.user
        widgets = {
            'song': forms.HiddenInput()
        }
