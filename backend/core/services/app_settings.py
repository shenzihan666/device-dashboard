"""Canonical app-settings keys, defaults, and typed accessor."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULTS: dict[str, str] = {
    "grafana_enabled": "false",
    "point_to_point_enabled": "true",
    "langsmith_enabled": "false",
}


@dataclass
class AppSettingsState:
    grafana_enabled: bool
    point_to_point_enabled: bool
    langsmith_enabled: bool

    def to_dict(self) -> dict[str, bool]:
        return {
            "grafana_enabled": self.grafana_enabled,
            "point_to_point_enabled": self.point_to_point_enabled,
            "langsmith_enabled": self.langsmith_enabled,
        }


def _parse_bool(val: str) -> bool:
    return val.lower() in ("true", "1", "yes")


async def load_effective(repo: object) -> AppSettingsState:
    """Overlay DB values on top of DEFAULTS and return typed state.

    ``repo`` must expose an async ``get_all() -> dict[str, str]`` method
    (duck-typed to avoid a hard import cycle).
    """
    stored: dict[str, str] = await repo.get_all()  # type: ignore[attr-defined]
    merged = {**DEFAULTS, **stored}
    return AppSettingsState(
        grafana_enabled=_parse_bool(merged["grafana_enabled"]),
        point_to_point_enabled=_parse_bool(merged["point_to_point_enabled"]),
        langsmith_enabled=_parse_bool(merged["langsmith_enabled"]),
    )
