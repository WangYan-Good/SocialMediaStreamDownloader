"""Platform configuration module to manage supported platforms dynamically"""

import yaml
from pathlib import Path
from backend.src.base.log import get_logger


class PlatformConfig:
    """Manages platform configurations and supported platforms"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize platform configuration
        
        Args:
            config_path: Path to platform configuration file
        """
        if config_path is None:
            config_path = "./config/platforms.yml"
            
        self.config_path = Path(config_path)
        self.platforms = self.load_platforms()
    
    def load_platforms(self):
        """Load platform configurations from YAML file"""
        default_platforms = {
            'douyin': {
                'handler': 'backend.src.platform.douyin.douyin_handler',
                'domains': ['douyin.com', 'v.douyin.com'],
                'enabled': True
            },
            'other': {
                'handler': 'backend.src.platform.other.other_handler',
                'domains': [],
                'enabled': True
            }
        }
        
        if not self.config_path.exists():
            # Create default config file if it doesn't exist
            self.save_platforms(default_platforms)
            return default_platforms
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
                if loaded_config is None:
                    return default_platforms
                # Merge with defaults to ensure all required fields exist
                for platform, default_config in default_platforms.items():
                    if platform not in loaded_config:
                        loaded_config[platform] = default_config
                    else:
                        # Ensure required fields exist
                        for key, value in default_config.items():
                            if key not in loaded_config[platform]:
                                loaded_config[platform][key] = value
                return loaded_config
        except Exception as e:
            get_logger().error(f"Error loading platform config: {e}")
            return default_platforms
    
    def save_platforms(self, platforms):
        """Save platform configurations to YAML file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(platforms, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            get_logger().error(f"Error saving platform config: {e}")
            raise
    
    def get_platform_list(self):
        """Get list of enabled platforms"""
        return [platform for platform, config in self.platforms.items() if config.get('enabled', False)]
    
    def get_handler_dict(self):
        """Get dictionary mapping platforms to their handlers"""
        return {platform: self.get_handler_function(platform) 
                for platform, config in self.platforms.items() 
                if config.get('enabled', False)}
    
    def get_domains_for_platform(self, platform):
        """Get list of domains associated with a platform"""
        if platform in self.platforms:
            return self.platforms[platform].get('domains', [])
        return []
    
    def get_handler_function(self, platform):
        """Dynamically import and return the handler function for a platform"""
        if platform not in self.platforms:
            raise ValueError(f"Platform {platform} not found in configuration")
        
        handler_path = self.platforms[platform]['handler']
        try:
            # Split the module path and function name
            parts = handler_path.split('.')
            func_name = parts[-1]
            module_path = '.'.join(parts[:-1])
            
            # Import the module and get the function
            module = __import__(module_path, fromlist=[func_name])
            handler_func = getattr(module, func_name)
            return handler_func
        except ImportError as e:
            get_logger().error(f"Could not import handler {handler_path} for platform {platform}: {e}")
            raise
        except AttributeError as e:
            get_logger().error(f"Handler function {func_name} not found in module {module_path}: {e}")
            raise