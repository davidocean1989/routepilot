import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    database_path: str = 'data/trips.sqlite3'
    map_mode: str = 'tencent'
    tencent_map_key: str = field(default='', repr=False)
    tencent_js_key: str = field(default='', repr=False)
    tencent_nav_key: str = field(default='', repr=False)
    map_interval: float = 5.0
    operation_timeout: float = 180.0

    def __post_init__(self):
        if self.map_mode not in ('tencent', 'demo'):
            raise ValueError('ROUTEPILOT_MAP_MODE must be tencent or demo')
        if self.map_interval < 0 or self.operation_timeout <= 0:
            raise ValueError('Invalid map timing settings')
        if self.tencent_map_key and self.tencent_map_key in (self.tencent_js_key, self.tencent_nav_key):
            raise ValueError('Browser keys must be separate from the server key')

    @classmethod
    def from_env(cls):
        return cls(
            database_path=os.getenv('ROUTEPILOT_DATABASE', 'data/trips.sqlite3'),
            map_mode=os.getenv('ROUTEPILOT_MAP_MODE', 'tencent'),
            tencent_map_key=os.getenv('TENCENT_MAP_KEY', ''),
            tencent_js_key=os.getenv('TENCENT_JS_KEY', ''),
            tencent_nav_key=os.getenv('TENCENT_NAV_KEY', ''),
            map_interval=float(os.getenv('ROUTEPILOT_MAP_INTERVAL', '5')),
            operation_timeout=float(os.getenv('ROUTEPILOT_OPERATION_TIMEOUT', '180')),
        )
