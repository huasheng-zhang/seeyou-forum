"""accounts/forms.py — 注册表单"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    """注册表单：用户名 + 邮箱 + 密码"""

    email = forms.EmailField(
        label='邮箱',
        widget=forms.EmailInput(attrs={'class': 'form-input'}),
    )
    display_name = forms.CharField(
        label='显示名（笔名）',
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-input'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'display_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            from accounts.models import Profile
            Profile.objects.create(
                user=user,
                display_name=self.cleaned_data['display_name'],
                avatar_char=self.cleaned_data['display_name'][:1] or '客',
            )
        return user


class LoginForm(forms.Form):
    """登录表单（用户名或邮箱）"""

    username = forms.CharField(
        label='用户名',
        widget=forms.TextInput(attrs={'class': 'form-input', 'autofocus': True}),
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
    )
