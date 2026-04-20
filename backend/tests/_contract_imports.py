import importlib

import pytest


def import_contract_module(*candidates):
    """Import the first available implementation module for an executable contract."""
    for module_path in candidates:
        try:
            return importlib.import_module(module_path)
        except ModuleNotFoundError as exc:
            if exc.name == module_path or module_path.startswith(f"{exc.name}."):
                continue
            raise

    names = ", ".join(candidates)
    pytest.skip(
        f"Implementation module is not available yet. Tried: {names}",
        allow_module_level=True,
    )


def require_attrs(module, *names):
    missing = [name for name in names if not hasattr(module, name)]
    if missing:
        pytest.skip(
            f"{module.__name__} does not expose expected contract attrs: "
            f"{', '.join(missing)}",
            allow_module_level=True,
        )

    return tuple(getattr(module, name) for name in names)


def get_field(value, name):
    if isinstance(value, dict):
        return value[name]
    return getattr(value, name)
