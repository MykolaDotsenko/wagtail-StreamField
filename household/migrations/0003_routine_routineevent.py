from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("household", "0002_pantryitem"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Routine",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=120)),
                (
                    "room",
                    models.CharField(
                        choices=[
                            ("whole_home", "Whole home"),
                            ("kitchen", "Kitchen"),
                            ("bathroom", "Bathroom"),
                            ("bedroom", "Bedroom"),
                            ("living_room", "Living room"),
                            ("outdoor", "Outdoor"),
                            ("other", "Other"),
                        ],
                        default="whole_home",
                        max_length=20,
                    ),
                ),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("one_time", "One-time"),
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                        ],
                        default="weekly",
                        max_length=12,
                    ),
                ),
                ("due_on", models.DateField()),
                ("postponed_until", models.DateField(blank=True, null=True)),
                (
                    "recurrence_anchor_day",
                    models.PositiveSmallIntegerField(blank=True, null=True),
                ),
                (
                    "expected_duration_minutes",
                    models.PositiveSmallIntegerField(blank=True, null=True),
                ),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="routines",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["due_on", "title", "pk"],
                "indexes": [
                    models.Index(
                        fields=["user", "active", "due_on"],
                        name="routine_due_lookup",
                    )
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(expected_duration_minutes__isnull=True)
                        | models.Q(expected_duration_minutes__gte=1),
                        name="routine_duration_positive",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(postponed_until__isnull=True)
                        | models.Q(postponed_until__gt=models.F("due_on")),
                        name="routine_postpone_after_due",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(
                                frequency="monthly",
                                recurrence_anchor_day__isnull=False,
                                recurrence_anchor_day__gte=1,
                                recurrence_anchor_day__lte=31,
                            )
                            | (
                                ~models.Q(frequency="monthly")
                                & models.Q(recurrence_anchor_day__isnull=True)
                            )
                        ),
                        name="routine_monthly_anchor_consistent",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="RoutineEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("scheduled_for", models.DateField()),
                (
                    "outcome",
                    models.CharField(
                        choices=[
                            ("completed", "Completed"),
                            ("skipped", "Skipped"),
                            ("postponed", "Postponed"),
                        ],
                        max_length=12,
                    ),
                ),
                ("postponed_to", models.DateField(blank=True, null=True)),
                ("acted_at", models.DateTimeField(auto_now_add=True)),
                (
                    "routine",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="household.routine",
                    ),
                ),
            ],
            options={
                "ordering": ["-acted_at", "-pk"],
                "constraints": [
                    models.CheckConstraint(
                        condition=(
                            models.Q(
                                outcome="postponed",
                                postponed_to__isnull=False,
                                postponed_to__gt=models.F("scheduled_for"),
                            )
                            | (
                                models.Q(outcome__in=["completed", "skipped"])
                                & models.Q(postponed_to__isnull=True)
                            )
                        ),
                        name="routine_event_outcome_consistent",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(outcome__in=["completed", "skipped"]),
                        fields=("routine", "scheduled_for"),
                        name="unique_terminal_routine_occurrence",
                    ),
                ],
            },
        ),
    ]
