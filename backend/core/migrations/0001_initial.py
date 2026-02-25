from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Certification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, unique=True)),
                ("difficulty", models.CharField(default="Beginner", max_length=50)),
                ("description", models.TextField()),
                ("link", models.URLField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, unique=True)),
                ("short_intro", models.TextField()),
                ("skills", models.CharField(max_length=400)),
                ("category", models.CharField(max_length=120)),
                ("duration", models.CharField(max_length=80)),
                ("rating", models.CharField(max_length=20)),
                ("site", models.CharField(max_length=80)),
                ("url", models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("password", models.CharField(max_length=255)),
                ("interests_data", models.TextField(default="[]")),
                ("preferences_data", models.TextField(default='{"pace": "Moderate", "content_format": "Video"}')),
                (
                    "performance_data",
                    models.TextField(
                        default='{"learning_hours": 0, "average_score": 0, "skills_mastered": 0, "recent_activity": [], "skill_progress": []}'
                    ),
                ),
                ("completed_courses_data", models.TextField(default="[]")),
                ("earned_certifications_data", models.TextField(default="[]")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_login", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="QuizResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.userprofile"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserActivity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("learning_hours", models.FloatField(default=0)),
                ("score", models.IntegerField(default=0)),
                ("date", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.userprofile"),
                ),
            ],
        ),
    ]
