from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


DESTRUCTIVE_OPERATION_NAMES = frozenset(
    {
        "AlterField",
        "AlterModelTable",
        "DeleteModel",
        "RemoveConstraint",
        "RemoveField",
        "RemoveIndex",
        "RenameField",
        "RenameModel",
        "RunSQL",
        "SeparateDatabaseAndState",
    }
)
REQUIRED_SAFETY_PLAN_KEYS = (
    "ticket",
    "summary",
    "backfill",
    "deploy_strategy",
    "rollback",
)
LEGACY_ALLOWED_MIGRATIONS = frozenset(
    {
        "delivery/migrations/0003_alter_deliverytrackingevent_new_status_and_more.py",
        "orders/migrations/0003_alter_order_status.py",
        "payments/migrations/0003_alter_paymentmethod_session_mode.py",
    }
)


@dataclass(frozen=True)
class MigrationSafetyViolation:
    relative_path: str
    operations: tuple[str, ...]
    message: str


def collect_migration_safety_violations(
    base_dir: Path,
    *,
    legacy_allowed_migrations: set[str] | frozenset[str] | None = None,
) -> list[MigrationSafetyViolation]:
    allowed_migrations = legacy_allowed_migrations or LEGACY_ALLOWED_MIGRATIONS
    violations: list[MigrationSafetyViolation] = []

    for migration_path in sorted(
        base_dir.glob("*/migrations/[0-9][0-9][0-9][0-9]_*.py")
    ):
        relative_path = migration_path.relative_to(base_dir).as_posix()
        risky_operations, safety_plan = inspect_migration_file(migration_path)
        if not risky_operations or relative_path in allowed_migrations:
            continue

        missing_keys = tuple(
            key
            for key in REQUIRED_SAFETY_PLAN_KEYS
            if not isinstance(safety_plan.get(key), str) or not safety_plan[key].strip()
        )
        if missing_keys:
            violations.append(
                MigrationSafetyViolation(
                    relative_path=relative_path,
                    operations=risky_operations,
                    message=(
                        "Destructive migration operations require a non-empty "
                        f"MIGRATION_SAFETY_PLAN with keys: {', '.join(REQUIRED_SAFETY_PLAN_KEYS)}. "
                        f"Missing or blank keys: {', '.join(missing_keys)}."
                    ),
                )
            )

    return violations


def inspect_migration_file(
    migration_path: Path,
) -> tuple[tuple[str, ...], dict[str, str]]:
    module = ast.parse(
        migration_path.read_text(encoding="utf-8"), filename=str(migration_path)
    )
    operation_names = tuple(sorted(set(_extract_operation_names(module))))
    risky_operations = tuple(
        operation_name
        for operation_name in operation_names
        if operation_name in DESTRUCTIVE_OPERATION_NAMES
    )
    safety_plan = _extract_safety_plan(module)
    return risky_operations, safety_plan


def format_violations(violations: list[MigrationSafetyViolation]) -> str:
    lines = []
    for violation in violations:
        lines.append(
            f"- {violation.relative_path}: {', '.join(violation.operations)}. {violation.message}"
        )
    return "\n".join(lines)


def _extract_operation_names(module: ast.Module) -> list[str]:
    operation_names: list[str] = []

    for node in ast.walk(module):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "operations"
            for target in node.targets
        ):
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            continue

        for item in node.value.elts:
            if not isinstance(item, ast.Call):
                continue
            operation_name = _resolve_call_name(item.func)
            if operation_name:
                operation_names.append(operation_name)

    return operation_names


def _extract_safety_plan(module: ast.Module) -> dict[str, str]:
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "MIGRATION_SAFETY_PLAN"
            for target in node.targets
        ):
            continue

        try:
            plan = ast.literal_eval(node.value)
        except (SyntaxError, ValueError):
            return {}
        if not isinstance(plan, dict):
            return {}
        return {str(key): str(value) for key, value in plan.items()}

    return {}


def _resolve_call_name(func: ast.AST) -> str | None:
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None
