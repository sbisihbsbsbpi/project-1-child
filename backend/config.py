"""
✅ PHASE 3: Configuration Management
Centralized configuration using Pydantic BaseSettings
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from pathlib import Path
from typing import List
import os


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables or .env file.
    Pydantic automatically validates types and provides defaults.
    """

    # ===== API Settings =====
    api_host: str = Field(default="127.0.0.1", description="API server host")
    api_port: int = Field(default=8001, description="API server port")

    # ===== CORS Settings =====
    allowed_origins: str = Field(
        default="http://localhost:5174,tauri://localhost,https://tauri.localhost",
        description="Comma-separated list of allowed CORS origins"
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse allowed_origins string into list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # ===== Performance Settings =====
    max_concurrent_captures: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of concurrent screenshot captures"
    )

    # ===== Logging Settings =====
    log_level: str = Field(default="INFO", description="Logging level")
    log_file_max_bytes: int = Field(
        default=10_485_760,  # 10MB
        description="Maximum log file size before rotation"
    )
    log_file_backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep"
    )

    @validator("log_level")
    def validate_log_level(cls, v):
        """Ensure log level is valid"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v

    # ===== Screenshot Settings =====
    screenshots_dir: Path = Field(
        default=Path("screenshots"),
        description="Directory for saving screenshots"
    )

    default_viewport_width: int = Field(
        default=1920,
        ge=800,
        le=3840,
        description="Default viewport width"
    )

    default_viewport_height: int = Field(
        default=1080,
        ge=600,
        le=2160,
        description="Default viewport height"
    )

    # ===== Timeout Settings =====
    timeout_normal: float = Field(
        default=35.0,
        description="Timeout for normal headless captures (seconds)"
    )

    timeout_real_browser: float = Field(
        default=60.0,
        description="Timeout for real browser mode (seconds)"
    )

    timeout_stealth: float = Field(
        default=70.0,
        description="Timeout for stealth mode (seconds)"
    )

    timeout_segmented: float = Field(
        default=120.0,
        description="Timeout for segmented captures (seconds)"
    )

    # ===== Quality Check Settings =====
    quality_min_score: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Minimum quality score to pass"
    )

    quality_blank_threshold: int = Field(
        default=10,
        description="Brightness range threshold for blank detection"
    )

    # ===== Stealth Mode Settings =====
    stealth_user_agents: List[str] = Field(
        default=[
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ],
        description="User agents for stealth mode rotation"
    )

    stealth_viewport_randomization: int = Field(
        default=50,
        description="Pixels to randomize viewport size (+/-)"
    )

    # ===== Segmented Capture Settings =====
    segment_default_overlap: int = Field(
        default=20,
        ge=0,
        le=50,
        description="Default overlap percentage for segmented captures"
    )

    segment_default_scroll_delay: int = Field(
        default=1000,
        description="Default scroll delay in milliseconds"
    )

    segment_default_max_segments: int = Field(
        default=50,
        description="Default maximum number of segments"
    )

    # ===== Auth State Settings =====
    auth_state_file: Path = Field(
        default=Path("auth_state.json"),
        description="Path to authentication state file"
    )

    browser_sessions_dir: Path = Field(
        default=Path("browser_sessions"),
        description="Directory for browser session data"
    )

    # ===== Microservice URLs =====
    document_service_url: str = Field(
        default="http://localhost:8002",
        description="Document Service base URL"
    )

    quality_service_url: str = Field(
        default="http://localhost:8003",
        description="Quality Service base URL"
    )

    api_service_url: str = Field(
        default="http://localhost:8004",
        description="API Extraction Service base URL"
    )

    # ===== Development Settings =====
    debug: bool = Field(default=False, description="Enable debug mode")
    reload: bool = Field(default=False, description="Enable auto-reload")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        # Allow extra fields for forward compatibility
        extra = "ignore"


# Global settings instance
settings = Settings()


# Helper functions for common operations
def get_timeout(capture_mode: str, use_real_browser: bool, use_stealth: bool) -> float:
    """
    Get appropriate timeout based on capture mode.
    
    Args:
        capture_mode: "viewport", "fullpage", or "segmented"
        use_real_browser: Whether using real browser mode
        use_stealth: Whether using stealth mode
        
    Returns:
        Timeout in seconds
    """
    if use_real_browser:
        return settings.timeout_real_browser
    elif use_stealth:
        return settings.timeout_stealth
    elif capture_mode == "segmented":
        return settings.timeout_segmented
    else:
        return settings.timeout_normal


def ensure_directories():
    """Create required directories if they don't exist"""
    settings.screenshots_dir.mkdir(exist_ok=True)
    settings.browser_sessions_dir.mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)


# Initialize directories on import
ensure_directories()
