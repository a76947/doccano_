

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("projects", "0008_project_allow_member_to_create_label_type_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Perspective",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("question", models.CharField(max_length=100)),
                (
                    "data_type",
                    models.CharField(
                        choices=[("int", "Integer"), ("string", "String"), ("boolean", "Boolean")], max_length=20
                    ),
                ),
                ("options", models.JSONField(blank=True, default=list)),
            ],
        ),
        migrations.CreateModel(
            name="PerspectiveGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="perspective_groups",
                        to="projects.project",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PerspectiveAnswer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("answer", models.TextField()),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "perspective",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="projects.perspective"
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="perspective_answers",
                        to="projects.project",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="perspective",
            name="group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="questions",
                to="projects.perspectivegroup",
            ),
        ),
        migrations.AddField(
            model_name="perspective",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="perspectives", to="projects.project"
            ),
        ),

        migrations.AlterUniqueTogether(
            name="perspective",
            unique_together={("group", "question")},
        ),

    ]
