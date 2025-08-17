import os
import platform
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, computed_field
from dotenv import load_dotenv

def get_user_data_dir() -> Path:
    """Get the appropriate user data directory for the current platform."""
    system = platform.system()
    
    if system == "Windows":
        # Use AppData/Local on Windows
        base_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif system == "Darwin":  # macOS
        # Use Application Support on macOS
        base_dir = Path.home() / "Library" / "Application Support"
    else:  # Linux and other Unix-like systems
        # Use XDG_DATA_HOME or ~/.local/share on Linux
        base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    
    return base_dir / "humble-bundle-inventory"

def get_user_config_dir() -> Path:
    """Get the appropriate user config directory for the current platform."""
    system = platform.system()
    
    if system == "Windows":
        # Use AppData/Roaming on Windows
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "Darwin":  # macOS
        # Use Application Support on macOS (same as data dir)
        base_dir = Path.home() / "Library" / "Application Support"
    else:  # Linux and other Unix-like systems
        # Use XDG_CONFIG_HOME or ~/.config on Linux
        base_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    
    return base_dir / "humble-bundle-inventory"

# Load environment variables from user config directory and current directory
user_config_dir = get_user_config_dir()
load_dotenv(user_config_dir / ".env")  # User-specific config first
load_dotenv()  # Current directory .env second (for development)

class Settings(BaseSettings):
    # User data directories
    user_data_dir: Path = Field(default_factory=get_user_data_dir, env="HUMBLE_USER_DATA_DIR")
    user_config_dir: Path = Field(default_factory=get_user_config_dir, env="HUMBLE_USER_CONFIG_DIR")
    
    # Database settings - computed after user_data_dir is set
    database_path: Optional[str] = Field(default=None, env="DATABASE_PATH")
    
    # Humble Bundle credentials
    humble_email: Optional[str] = Field(default=None, env="HUMBLE_EMAIL")
    humble_password: Optional[str] = Field(default=None, env="HUMBLE_PASSWORD")
    
    # Session persistence - computed after user_data_dir is set  
    session_cache_path: Optional[str] = Field(default=None, env="SESSION_CACHE_PATH")
    
    # Sync settings
    sync_interval_hours: int = Field(default=24, env="SYNC_INTERVAL_HOURS")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    
    # Rate limiting
    requests_per_minute: int = Field(default=30, env="REQUESTS_PER_MINUTE")
    
    # Logging - computed after user_data_dir is set
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    def model_post_init(self, __context) -> None:
        """Set defaults for paths after initialization."""
        if self.database_path is None:
            object.__setattr__(self, 'database_path', str(self.user_data_dir / "humble_bundle.duckdb"))
        if self.session_cache_path is None:
            object.__setattr__(self, 'session_cache_path', str(self.user_data_dir / ".session_cache"))
        if self.log_file is None:
            object.__setattr__(self, 'log_file', str(self.user_data_dir / "humble_sync.log"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

def ensure_user_directories():
    """Ensure all user directories exist and show user where files are stored."""
    from rich.console import Console
    console = Console()
    
    try:
        # Create directories
        settings.user_data_dir.mkdir(parents=True, exist_ok=True)
        settings.user_config_dir.mkdir(parents=True, exist_ok=True)
        Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
        Path(settings.session_cache_path).parent.mkdir(parents=True, exist_ok=True)
        Path(settings.log_file).parent.mkdir(parents=True, exist_ok=True)
        
        return True
    except Exception as e:
        console.print(f"❌ Error creating user directories: {e}", style="red")
        return False

def show_user_paths():
    """Display user paths for transparency."""
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    
    paths_info = f"""[bold]Data Directory:[/bold] {settings.user_data_dir}
  • Database: {settings.database_path}
  • Session cache: {settings.session_cache_path}
  • Logs: {settings.log_file}

[bold]Config Directory:[/bold] {settings.user_config_dir}
  • Environment file (.env): {settings.user_config_dir / '.env'}

[bold]Note:[/bold] You can override these paths with environment variables:
  • DATABASE_PATH, SESSION_CACHE_PATH, LOG_FILE
  • HUMBLE_USER_DATA_DIR, HUMBLE_USER_CONFIG_DIR"""
    
    panel = Panel(
        paths_info,
        title="File Locations",
        border_style="blue"
    )
    console.print(panel)