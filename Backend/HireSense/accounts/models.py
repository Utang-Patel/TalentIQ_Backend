from django.db import models


class User(models.Model):

    user_id = models.AutoField(primary_key=True)

    full_name = models.CharField(max_length=100)

    email = models.EmailField(
        max_length=150,
        unique=True
    )

    password_hash = models.CharField(max_length=255)

    ROLE_CHOICES = (
        ('recruiter', 'Recruiter'),
        ('admin', 'Admin'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.full_name