from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any

CONFIG_DIR = Path.home() / '.config' / 'hyperx-saga-control'
PROFILES_PATH = CONFIG_DIR / 'profiles.json'
SETTINGS_PATH = CONFIG_DIR / 'settings.json'


@dataclass
class Profile:
    name: str = 'Default'
    color: str = '#00aaff'
    brightness: int = 100
    dpi: list[int] = None  # type: ignore[assignment]
    active_stage: int = 0
    polling_hz: int = 1000

    def __post_init__(self) -> None:
        if self.dpi is None:
            self.dpi = [400, 800, 1600, 3200]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        dpi = data.get('dpi', [400, 800, 1600, 3200])
        if not isinstance(dpi, list) or len(dpi) != 4:
            dpi = [400, 800, 1600, 3200]
        return cls(
            name=str(data.get('name', 'Default')),
            color=str(data.get('color', '#00aaff')),
            brightness=int(data.get('brightness', 100)),
            dpi=[int(x) for x in dpi],
            active_stage=int(data.get('active_stage', 0)),
            polling_hz=int(data.get('polling_hz', data.get('polling_rate', 1000))),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProfileStore:
    def __init__(self, path: Path = PROFILES_PATH):
        self.path = path
        self.profiles: dict[str, Profile] = {}
        self.load()

    def load(self) -> None:
        self.profiles = {}
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text())
                for item in raw.get('profiles', []):
                    p = Profile.from_dict(item)
                    self.profiles[p.name] = p
            except Exception:
                self.profiles = {}
        if not self.profiles:
            p = Profile()
            self.profiles[p.name] = p
            self.save()

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {'profiles': [p.to_dict() for p in self.profiles.values()]}
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')

    def names(self) -> list[str]:
        return sorted(self.profiles.keys())

    def get(self, name: str) -> Profile:
        return self.profiles.get(name) or next(iter(self.profiles.values()))

    def put(self, profile: Profile) -> None:
        self.profiles[profile.name] = profile
        self.save()

    def delete(self, name: str) -> None:
        if name in self.profiles and len(self.profiles) > 1:
            del self.profiles[name]
            self.save()


def load_settings() -> dict[str, Any]:
    if SETTINGS_PATH.exists():
        try:
            return json.loads(SETTINGS_PATH.read_text())
        except Exception:
            return {}
    return {}


def save_settings(settings: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2, sort_keys=True) + '\n')
