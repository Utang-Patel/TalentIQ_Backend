from django.contrib import admin
from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):

    list_display = (
        'resume_id',
        'candidate',
        'file_name',
        'file_type',
        'file_size',
        'extraction_status',
        'uploaded_at',
    )

    list_filter = (
        'extraction_status',
        'file_type',
    )

    search_fields = (
        'file_name',
        'candidate__full_name',
        'candidate__email',
    )

    readonly_fields = (
        'uploaded_at',
    )