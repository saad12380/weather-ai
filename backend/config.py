"""
Configuration module for Weather AI Platform
Handles environment-specific settings and secrets management
"""

import os
from typing import List
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # ============ ENVIRONMENT ============
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT == "development"
    
    # ============ SERVER CONFIGURATION ============
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", 3000))
    WEBSITE_URL: str = os.getenv("WEBSITE_URL", "http://localhost:3000")
    API_URL: str = os.getenv("API_URL", "http://localhost:3000/api")
    
    # ============ SECURITY ============
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ============ CORS ============
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    
    # Parse CORS_ORIGINS from env variable (comma-separated)
    @classmethod
    def parse_cors_origins(cls):
        origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        return [origin.strip() for origin in origins_str.split(",")]
    
    # ============ DATABASE ============
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./weather.db")
    
    # ============ REDIS ============
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    
    # ============ API KEYS ============
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    
    # ============ EMAIL CONFIGURATION ============
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "")
    
    # ============ OAUTH ============
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_CLIENT_SECRET: str = os.getenv("MICROSOFT_CLIENT_SECRET", "")
    
    # ============ FEATURES ============
    ENABLE_NOTIFICATIONS: bool = os.getenv("ENABLE_NOTIFICATIONS", "true").lower() == "true"
    ENABLE_WEBSOCKET: bool = os.getenv("ENABLE_WEBSOCKET", "true").lower() == "true"
    ENABLE_DYNAMIC_THRESHOLDS: bool = os.getenv("ENABLE_DYNAMIC_THRESHOLDS", "true").lower() == "true"
    ENABLE_MONITORING: bool = os.getenv("ENABLE_MONITORING", "true").lower() == "true"
    
    # ============ RATE LIMITING ============
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", 60))
    
    # ============ LOGGING ============
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "/var/log/weather-ai/backend.log")
    
    # ============ HTTPS ============
    HTTPS_ENABLED: bool = os.getenv("HTTPS_ENABLED", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"
    
    def validate_production(self) -> bool:
        """Validate production configuration"""
        errors = []
        
        if self.is_production():
            # Check required keys
            if self.SECRET_KEY == "change-me-in-production":
                errors.append("SECRET_KEY must be changed for production")
            
            if self.SESSION_SECRET_KEY == "change-me-in-production":
                errors.append("SESSION_SECRET_KEY must be changed for production")
            
            if not self.OPENWEATHER_API_KEY:
                errors.append("OPENWEATHER_API_KEY is required for production")
            
            if not self.SMTP_USERNAME or not self.SMTP_PASSWORD:
                errors.append("SMTP credentials are required for production")
            
            if "localhost" in self.WEBSITE_URL or "127.0.0.1" in self.WEBSITE_URL:
                errors.append("WEBSITE_URL must not be localhost in production")
            
            if not self.HTTPS_ENABLED and "https://" not in self.WEBSITE_URL:
                errors.append("HTTPS must be enabled in production")
        
        if errors:
            error_msg = "Production Configuration Issues:\n" + "\n".join([f"  - {e}" for e in errors])
            print(f"⚠️ {error_msg}")
            return False
        
        return True


# Cache the settings
@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached)"""
    settings = Settings()
    settings.CORS_ORIGINS = settings.parse_cors_origins()
    return settings


# Create global settings instance
settings = get_settings()

# Validate production settings
if settings.is_production():
    if not settings.validate_production():
        print("⚠️ WARNING: Production configuration is incomplete. Some features may not work correctly.")
        print("         Please review .env file and complete required configuration.")


# Configuration summary
if __name__ == "__main__":
    print("=" * 60)
    print("🔧 WEATHER AI PLATFORM - CONFIGURATION")
    print("=" * 60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Backend URL: {settings.API_URL}")
    print(f"CORS Origins: {len(settings.CORS_ORIGINS)} configured")
    print(f"Database: {settings.DATABASE_URL}")
    print(f"Cache Enabled: {settings.ENABLE_CACHE}")
    print(f"OpenWeatherMap API: {'✓' if settings.OPENWEATHER_API_KEY else '✗'}")
    print(f"Email Configured: {'✓' if settings.SMTP_USERNAME else '✗'}")
    print(f"OAuth Configured: {'✓' if settings.GOOGLE_CLIENT_ID else '✗'}")
    print("=" * 60)
