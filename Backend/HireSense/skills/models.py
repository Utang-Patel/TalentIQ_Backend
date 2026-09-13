from django.db import models

from candidates.models import Candidate


class Skill(models.Model):

    skill_id = models.AutoField(primary_key=True)

    skill_name = models.CharField(
        max_length=100,
        unique=True
    )

    category = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    aliases = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'skills'

    def __str__(self):
        return self.skill_name


class CandidateSkill(models.Model):

    candidate_skill_id = models.AutoField(
        primary_key=True
    )

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        db_column='candidate_id'
    )

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        db_column='skill_id'
    )

    proficiency = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    years_experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )

    evidence_text = models.TextField(
        null=True,
        blank=True
    )

    source = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'candidate_skills'

        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'skill'],
                name='unique_candidate_skill'
            )
        ]

    def __str__(self):
        return f"{self.candidate.full_name} - {self.skill.skill_name}"