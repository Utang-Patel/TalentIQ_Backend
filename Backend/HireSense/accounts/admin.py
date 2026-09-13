from django.contrib import admin

# Register your models here.
from .models import User
from django import forms

class UserAdminForm(forms.ModelForm):

    password_hash = forms.CharField(
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    form = UserAdminForm

    readonly_fields = ('created_at', 'updated_at')
