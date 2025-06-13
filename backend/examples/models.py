import uuid

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django_drf_filepond.models import DrfFilePondStoredStorage

from .managers import ExampleManager, ExampleStateManager
from projects.models import Project


class Example(models.Model):
    objects = ExampleManager()

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True, unique=True)
    meta        = models.JSONField(default=dict)
    filename    = models.FileField(default=".", max_length=1024,
                                   storage=DrfFilePondStoredStorage())
    upload_name = models.CharField(max_length=512)
    project     = models.ForeignKey(to=Project, on_delete=models.CASCADE,
                                    related_name="examples")
    annotations_approved_by = models.ForeignKey(
        to=User, on_delete=models.SET_NULL, null=True, blank=True
    )
    text       = models.TextField(null=True, blank=True)
    score      = models.FloatField(default=100)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def comment_count(self):
        """Total de comentários deste exemplo (qualquer label)."""
        return Comment.objects.filter(example=self.id).count()

    @property
    def data(self):
        return self.text if self.project.is_text_project else str(self.filename)

    class Meta:
        ordering = ["created_at"]


class Assignment(models.Model):
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project  = models.ForeignKey(to=Project, on_delete=models.CASCADE,
                                 related_name="assignments")
    example  = models.ForeignKey(to=Example, on_delete=models.CASCADE,
                                 related_name="assignments")
    assignee = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("example", "assignee")

    def clean(self):
        if not self.project.members.filter(id=self.assignee.id).exists():
            raise ValidationError("Assignee must be a member of the project")
        if not self.project.examples.filter(id=self.example.id).exists():
            raise ValidationError("Example must be in the project")
        return super().clean()


class ExampleState(models.Model):
    objects = ExampleStateManager()

    example      = models.ForeignKey(to=Example, on_delete=models.CASCADE,
                                     related_name="states")
    confirmed_by = models.ForeignKey(to=User, on_delete=models.CASCADE)
    confirmed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("example", "confirmed_by")


class Comment(models.Model):
    """Comentário associado a um Example e (opcionalmente) a um Label."""

    text    = models.TextField()
    example = models.ForeignKey(to=Example, on_delete=models.CASCADE,
                                related_name="comments")
    user    = models.ForeignKey(to=User, on_delete=models.CASCADE, null=True)

    # ► Importação preguiçosa para evitar ciclo
    label = models.ForeignKey(
        'label_types.CategoryType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comments'
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def username(self):
        return self.user.username if self.user else "(deleted)"

    class Meta:
        ordering = ["created_at"]
