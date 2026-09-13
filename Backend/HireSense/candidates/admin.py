from django.contrib import admin
from .models import Candidate


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):

    list_display = (
        'candidate_id',
        'full_name',
        'email',
        'phone',
        'location',
        'total_experience',
        'highest_education',
        'created_at',
    )

    search_fields = (
        'full_name',
        'email',
        'phone',
    )

    list_filter = (
        'highest_education',
        'location',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )