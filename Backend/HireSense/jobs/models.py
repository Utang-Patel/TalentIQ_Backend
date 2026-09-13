from django.db import models
from accounts.models import User


class Job(models.Model):
    job_id = models.AutoField(primary_key=True)

    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='recruiter_id'
    )

    job_title = models.CharField(max_length=150)
    department = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=150, null=True, blank=True)

    EMPLOYMENT_TYPE_CHOICES = (
        ('Full-time', 'Full-time'),
        ('Part-time', 'Part-time'),
        ('Internship', 'Internship'),
        ('Contract', 'Contract'),
    )

    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        null=True,
        blank=True
    )

    description = models.TextField()

    experience_min = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )

    experience_max = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )

    STATUS_CHOICES = (
        ('Draft', 'Draft'),
        ('Active', 'Active'),
        ('Closed', 'Closed'),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Draft'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jobs'

    def __str__(self):
        return self.job_title


class JobSkill(models.Model):
    job_skill_id = models.AutoField(primary_key=True)

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        db_column='job_id'
    )

    skill = models.ForeignKey(
        'skills.Skill',
        on_delete=models.CASCADE,
        db_column='skill_id'
    )

    IMPORTANCE_CHOICES = (
        ('Required', 'Required'),
        ('Preferred', 'Preferred'),
    )

    importance = models.CharField(
        max_length=20,
        choices=IMPORTANCE_CHOICES
    )

    min_experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_skills'

    def __str__(self):
        return f"{self.job.job_title} - {self.skill.skill_name}"