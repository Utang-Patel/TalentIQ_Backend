from django.contrib import admin

from .models import Skill, CandidateSkill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):

    list_display = (
        'skill_id',
        'skill_name',
        'category',
        'created_at',
    )

    search_fields = (
        'skill_name',
        'category',
    )

    list_filter = (
        'category',
    )

    readonly_fields = (
        'created_at',
    )


@admin.register(CandidateSkill)
class CandidateSkillAdmin(admin.ModelAdmin):

    list_display = (
        'candidate_skill_id',
        'candidate',
        'skill',
        'proficiency',
        'years_experience',
        'source',
        'confidence_score',
        'created_at',
    )

    search_fields = (
        'candidate__full_name',
        'candidate__email',
        'skill__skill_name',
    )

    list_filter = (
        'proficiency',
        'source',
    )

    readonly_fields = (
        'created_at',
    )