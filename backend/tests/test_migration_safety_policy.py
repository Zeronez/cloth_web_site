from pathlib import Path

from audit.migration_safety import collect_migration_safety_violations


def _write_migration(base_dir: Path, relative_path: str, body: str) -> None:
    migration_path = base_dir / relative_path
    migration_path.parent.mkdir(parents=True, exist_ok=True)
    migration_path.write_text(body, encoding="utf-8")


def test_safe_migration_does_not_require_safety_plan(tmp_path):
    _write_migration(
        tmp_path,
        "catalog/migrations/0001_add_index.py",
        """
from django.db import migrations, models


class Migration(migrations.Migration):
    operations = [
        migrations.AddIndex(
            model_name="product",
            index=models.Index(fields=["slug"], name="catalog_product_slug_idx"),
        ),
    ]
""".strip(),
    )

    violations = collect_migration_safety_violations(tmp_path)

    assert violations == []


def test_destructive_migration_requires_explicit_safety_plan(tmp_path):
    _write_migration(
        tmp_path,
        "catalog/migrations/0002_remove_field.py",
        """
from django.db import migrations


class Migration(migrations.Migration):
    operations = [
        migrations.RemoveField(
            model_name="product",
            name="legacy_code",
        ),
    ]
""".strip(),
    )

    violations = collect_migration_safety_violations(
        tmp_path, legacy_allowed_migrations=set()
    )

    assert len(violations) == 1
    assert violations[0].relative_path == "catalog/migrations/0002_remove_field.py"
    assert violations[0].operations == ("RemoveField",)
    assert "MIGRATION_SAFETY_PLAN" in violations[0].message


def test_destructive_migration_with_safety_plan_passes(tmp_path):
    _write_migration(
        tmp_path,
        "catalog/migrations/0003_remove_legacy_code.py",
        """
from django.db import migrations


MIGRATION_SAFETY_PLAN = {
    "ticket": "OPS-104",
    "summary": "Remove product.legacy_code after reads are gone.",
    "backfill": "No backfill required because the column is unused and already empty in production.",
    "deploy_strategy": "Deploy read-path removal first, run this migration in the next release window.",
    "rollback": "Rollback application first and restore the column from the last pre-drop snapshot if needed.",
}


class Migration(migrations.Migration):
    operations = [
        migrations.RemoveField(
            model_name="product",
            name="legacy_code",
        ),
    ]
""".strip(),
    )

    violations = collect_migration_safety_violations(
        tmp_path, legacy_allowed_migrations=set()
    )

    assert violations == []


def test_legacy_grandfathered_migration_remains_allowed_without_plan(tmp_path):
    legacy_path = "orders/migrations/0003_alter_order_status.py"
    _write_migration(
        tmp_path,
        legacy_path,
        """
from django.db import migrations, models


class Migration(migrations.Migration):
    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(max_length=24),
        ),
    ]
""".strip(),
    )

    violations = collect_migration_safety_violations(tmp_path)

    assert violations == []


def test_production_ci_runs_migration_safety_gate():
    workflow = (
        Path(__file__).resolve().parents[2] / ".github/workflows/production.yml"
    ).read_text(encoding="utf-8")

    assert "python manage.py checkmigrationsafety" in workflow
