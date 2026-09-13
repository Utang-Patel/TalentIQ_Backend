from django.db import models
from candidates.models import Candidate


class Resume(models.Model):

    resume_id = models.AutoField(primary_key=True)

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        db_column='candidate_id'
    )

    file_name = models.CharField(
        max_length=255
    )

    file_type = models.CharField(
        max_length=50
    )

    file_path = models.CharField(
        max_length=500
    )

    file_size = models.BigIntegerField()

    extracted_text = models.TextField(
        null=True,
        blank=True
    )

    EXTRACTION_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    extraction_status = models.CharField(
        max_length=20,
        choices=EXTRACTION_STATUS_CHOICES,
        default='Pending'
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'resumes'

    def __str__(self):
        return self.file_name