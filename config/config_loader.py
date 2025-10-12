"""
Configuration Loader Module
Loads and manages YAML configuration files
"""

import yaml
import os
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and manage configuration files"""

    def __init__(self, config_dir: str = "config"):
        """
        Initialize config loader

        Args:
            config_dir: Directory containing config files
        """
        self.config_dir = config_dir
        self.configs: Dict[str, Any] = {}

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        Load a configuration file

        Args:
            config_name: Name of config file (without .yaml extension)

        Returns:
            Configuration dictionary

        Example:
            >>> loader = ConfigLoader()
            >>> capture_config = loader.load_config('capture_config')
        """
        config_path = os.path.join(self.config_dir, f"{config_name}.yaml")

        if not os.path.exists(config_path):
            logger.error(f"Config file not found: {config_path}")
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            self.configs[config_name] = config
            logger.info(f"Loaded configuration: {config_name}")
            return config

        except Exception as e:
            logger.error(f"Error loading config {config_name}: {e}")
            raise

    def get_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached configuration or load if not cached

        Args:
            config_name: Name of config file

        Returns:
            Configuration dictionary
        """
        if config_name not in self.configs:
            return self.load_config(config_name)
        return self.configs[config_name]

    def get_value(self, config_name: str, key_path: str, default: Any = None) -> Any:
        """
        Get a specific value from config using dot notation

        Args:
            config_name: Name of config file
            key_path: Dot-separated path to value (e.g., 'network.interface')
            default: Default value if key not found

        Returns:
            Configuration value

        Example:
            >>> loader.get_value('capture_config', 'network.interface', 'eth0')
        """
        config = self.get_config(config_name)
        keys = key_path.split('.')

        value = config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def reload_config(self, config_name: str):
        """Reload a configuration file"""
        if config_name in self.configs:
            del self.configs[config_name]
        return self.load_config(config_name)

    def load_all_configs(self):
        """Load all YAML config files in config directory"""
        if not os.path.exists(self.config_dir):
            logger.warning(f"Config directory not found: {self.config_dir}")
            return

        for filename in os.listdir(self.config_dir):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                config_name = os.path.splitext(filename)[0]
                self.load_config(config_name)

        logger.info(f"Loaded {len(self.configs)} configuration files")


# Global config loader instance
_config_loader = ConfigLoader()


def get_config(config_name: str) -> Dict[str, Any]:
    """Get configuration (convenience function)"""
    return _config_loader.get_config(config_name)


def get_value(config_name: str, key_path: str, default: Any = None) -> Any:
    """Get configuration value (convenience function)"""
    return _config_loader.get_value(config_name, key_path, default)
