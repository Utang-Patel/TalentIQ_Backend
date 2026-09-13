from django.db import models
from resumes.models import Resume
from jobs.models import Job


class ResumeAnalysis(models.Model):

    analysis_id = models.AutoField(primary_key=True)

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        db_column='resume_id'
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        db_column='job_id'
    )

    summary = models.TextField(null=True, blank=True)

    semantic_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    experience_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    education_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    skill_match_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    resume_quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    model_name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    analyzed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'resume_analysis'
        constraints = [
        models.UniqueConstraint(
            fields=['resume', 'job'],
            name='unique_resume_job_analysis'
        )
    ]

    def __str__(self):
        return f"Analysis {self.analysis_id}"


class SkillGap(models.Model):

    gap_id = models.AutoField(primary_key=True)

    analysis = models.ForeignKey(
        ResumeAnalysis,
        on_delete=models.CASCADE,
        db_column='analysis_id'
    )

    skill = models.ForeignKey(
        'skills.Skill',
        on_delete=models.CASCADE,
        db_column='skill_id'
    )

    GAP_TYPE_CHOICES = (
        ('Missing', 'Missing'),
        ('Partial', 'Partial'),
    )

    gap_type = models.CharField(
        max_length=20,
        choices=GAP_TYPE_CHOICES
    )

    candidate_level = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    required_level = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    explanation = models.TextField(
        null=True,
        blank=True
    )

    SEVERITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'skill_gaps'

    def __str__(self):
        return f"{self.analysis} - {self.skill.skill_name}"


class CandidateScore(models.Model):
    score_id = models.AutoField(primary_key=True)

    analysis = models.ForeignKey(
        ResumeAnalysis,
        on_delete=models.CASCADE,
        db_column='analysis_id'
    )

    skill_match_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    experience_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    education_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    semantic_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    resume_quality_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    final_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    ranking = models.IntegerField(null=True, blank=True)

    scoring_version = models.CharField(
        max_length=50, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'candidate_scores'

    def __str__(self):
        return f"Score {self.score_id}"


class InterviewQuestion(models.Model):
    question_id = models.AutoField(primary_key=True)

    analysis = models.ForeignKey(
        ResumeAnalysis,
        on_delete=models.CASCADE,
        db_column='analysis_id'
    )

    question = models.TextField()

    TYPE_CHOICES = (
        ('Technical', 'Technical'),
        ('Behavioral', 'Behavioral'),
        ('Experience', 'Experience'),
        ('Skill Gap', 'Skill Gap'),
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    difficulty = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    related_skill = models.ForeignKey(
        'skills.Skill',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='related_skill_id'
    )

    reason = models.TextField(
        null=True,
        blank=True
    )

    generated_by = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'interview_questions'

    def __str__(self):
        return self.question


from accounts.models import User
from candidates.models import Candidate


class InterviewSession(models.Model):
    session_id = models.AutoField(primary_key=True)

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        db_column='candidate_id'
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        db_column='job_id'
    )

    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='recruiter_id'
    )

    STATUS_CHOICES = (
        ('Scheduled', 'Scheduled'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Scheduled'
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True
    )

    ended_at = models.DateTimeField(
        null=True,
        blank=True
    )

    notes = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'interview_sessions'

    def __str__(self):
        return f"Interview {self.session_id}"