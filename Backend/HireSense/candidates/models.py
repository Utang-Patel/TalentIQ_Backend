from django.db import models


class Candidate(models.Model):

    candidate_id = models.AutoField(primary_key=True)

    full_name = models.CharField(
        max_length=150
    )

    email = models.EmailField(
        max_length=150,
        unique=True
    )

    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    location = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )

    total_experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )

    highest_education = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )

    linkedin_url = models.URLField(
        max_length=255,
        null=True,
        blank=True
    )

    github_url = models.URLField(
        max_length=255,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = 'candidates'

    def __str__(self):
        return self.full_name