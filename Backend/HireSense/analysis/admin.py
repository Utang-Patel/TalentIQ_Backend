from django.contrib import admin
from .models import ResumeAnalysis,SkillGap, CandidateScore, InterviewQuestion, InterviewSession


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):

    list_display = (
        'analysis_id',
        'resume',
        'job',
        'semantic_score',
        'experience_score',
        'education_score',
        'skill_match_score',
        'overall_score',
        'status',
        'analyzed_at',
    )

    list_filter = (
        'status',
    )

    search_fields = (
        'resume__file_name',
        'job__job_title',
    )


@admin.register(SkillGap)
class SkillGapAdmin(admin.ModelAdmin):

    list_display = (
        'gap_id',
        'analysis',
        'skill',
        'gap_type',
        'candidate_level',
        'required_level',
        'severity',
    )

    list_filter = (
        'gap_type',
        'severity',
    )

    search_fields = (
        'skill__skill_name',
        'explanation',
    )


@admin.register(CandidateScore)
class CandidateScoreAdmin(admin.ModelAdmin):
    list_display = (
        'score_id',
        'analysis',
        'skill_match_score',
        'experience_score',
        'education_score',
        'semantic_score',
        'resume_quality_score',
        'final_score',
        'ranking',
        'scoring_version',
    )

    list_filter = ('scoring_version',)
    search_fields = ('scoring_version',)


@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'question_id',
        'analysis',
        'question',
        'type',
        'difficulty',
        'related_skill',
        'generated_by',
        'created_at',
    )

    list_filter = (
        'type',
        'difficulty',
        'generated_by',
    )

    search_fields = (
        'question',
        'reason',
    )   


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = (
        'session_id',
        'candidate',
        'job',
        'recruiter',
        'status',
        'scheduled_at',
        'started_at',
        'ended_at',
        'created_at',
    )

    list_filter = (
        'status',
    )

    search_fields = (
        'candidate__full_name',
        'job__job_title',
        'recruiter__full_name',
        'notes',
    )