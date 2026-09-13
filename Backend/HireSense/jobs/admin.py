from django.contrib import admin
from .models import Job, JobSkill


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'job_id',
        'job_title',
        'recruiter',
        'department',
        'location',
        'employment_type',
        'status',
    )

    search_fields = (
        'job_title',
        'department',
        'location',
    )

    list_filter = (
        'status',
        'employment_type',
    )


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    list_display = (
        'job_skill_id',
        'job',
        'skill',
        'importance',
        'min_experience',
        'weight',
    )

    list_filter = (
        'importance',
    )

    search_fields = (
        'job__job_title',
        'skill__skill_name',
    )