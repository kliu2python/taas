import os
import yaml
from typing import Any, Dict


class Config:
    """Configuration management for Browser Cloud microservice"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), "config.yml"
        )
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from YAML file with fallback to defaults"""
        default_config = {
            "grid_url": os.getenv("GRID_URL", "http://10.160.24.88:31590"),
            "vnc_password": os.getenv("VNC_PASSWORD", "secret"),
            "registration_secret": os.getenv("REGISTRATION_SECRET", ""),
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", "5000")),
            "debug": os.getenv("DEBUG", "False").lower() == "true"
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                    default_config.update(file_config)
            except Exception as e:
                print(f"Warning: Failed to load config file {self.config_file}: {e}")

        return default_config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value

    def save(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config: {e}")
