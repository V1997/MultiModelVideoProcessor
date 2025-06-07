"""
Production deployment configuration for Phase 3-5 features
"""

import os
from typing import Dict, Any, List

class ProductionConfig:
    """Production deployment configuration"""
    
    # Database Configuration
    DATABASE_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "name": os.getenv("DB_NAME", "multimodelovideo"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600"))
    }
    
    # Redis Configuration (for caching and background tasks)
    REDIS_CONFIG = {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "db": int(os.getenv("REDIS_DB", "0")),
        "password": os.getenv("REDIS_PASSWORD", None),
        "socket_timeout": int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
        "socket_connect_timeout": int(os.getenv("REDIS_CONNECT_TIMEOUT", "5")),
        "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    }
    
    # API Configuration
    API_CONFIG = {
        "host": os.getenv("API_HOST", "0.0.0.0"),
        "port": int(os.getenv("API_PORT", "8000")),
        "workers": int(os.getenv("API_WORKERS", "4")),
        "max_request_size": int(os.getenv("API_MAX_REQUEST_SIZE", "16777216")),  # 16MB
        "timeout": int(os.getenv("API_TIMEOUT", "300")),  # 5 minutes
        "keepalive": int(os.getenv("API_KEEPALIVE", "120")),
        "cors_origins": os.getenv("CORS_ORIGINS", "*").split(",")
    }
    
    # Security Configuration
    SECURITY_CONFIG = {
        "secret_key": os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
        "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
        "jwt_expiration": int(os.getenv("JWT_EXPIRATION", "86400")),  # 24 hours
        "rate_limit_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "100")),
        "max_login_attempts": int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
        "lockout_duration": int(os.getenv("LOCKOUT_DURATION", "900"))  # 15 minutes
    }
    
    # File Storage Configuration
    STORAGE_CONFIG = {
        "upload_dir": os.getenv("UPLOAD_DIR", "./uploads"),
        "cache_dir": os.getenv("CACHE_DIR", "./cache"),
        "logs_dir": os.getenv("LOGS_DIR", "./logs"),
        "max_file_size": int(os.getenv("MAX_FILE_SIZE", "1073741824")),  # 1GB
        "allowed_video_formats": os.getenv("ALLOWED_VIDEO_FORMATS", "mp4,avi,mov,mkv").split(","),
        "cleanup_interval": int(os.getenv("CLEANUP_INTERVAL", "86400"))  # 24 hours
    }
    
    # AI/ML Model Configuration
    MODEL_CONFIG = {
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        "visual_model": os.getenv("VISUAL_MODEL", "yolov8n"),
        "model_cache_dir": os.getenv("MODEL_CACHE_DIR", "./models"),
        "gpu_enabled": os.getenv("GPU_ENABLED", "false").lower() == "true",
        "batch_size": int(os.getenv("MODEL_BATCH_SIZE", "32")),
        "max_sequence_length": int(os.getenv("MAX_SEQUENCE_LENGTH", "512"))
    }
    
    # Monitoring Configuration
    MONITORING_CONFIG = {
        "enable_metrics": os.getenv("ENABLE_METRICS", "true").lower() == "true",
        "metrics_port": int(os.getenv("METRICS_PORT", "9090")),
        "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "enable_debug": os.getenv("ENABLE_DEBUG", "false").lower() == "true",
        "sentry_dsn": os.getenv("SENTRY_DSN", ""),
        "enable_profiling": os.getenv("ENABLE_PROFILING", "false").lower() == "true"
    }
    
    # Background Task Configuration
    CELERY_CONFIG = {
        "broker_url": os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
        "result_backend": os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "timezone": "UTC",
        "enable_utc": True,
        "worker_concurrency": int(os.getenv("CELERY_CONCURRENCY", "4")),
        "worker_max_tasks_per_child": int(os.getenv("CELERY_MAX_TASKS_PER_CHILD", "100")),
        "task_soft_time_limit": int(os.getenv("CELERY_SOFT_TIME_LIMIT", "300")),
        "task_time_limit": int(os.getenv("CELERY_TIME_LIMIT", "600"))
    }

def get_deployment_config() -> Dict[str, Any]:
    """Get complete deployment configuration"""
    return {
        "database": ProductionConfig.DATABASE_CONFIG,
        "redis": ProductionConfig.REDIS_CONFIG,
        "api": ProductionConfig.API_CONFIG,
        "security": ProductionConfig.SECURITY_CONFIG,
        "storage": ProductionConfig.STORAGE_CONFIG,
        "models": ProductionConfig.MODEL_CONFIG,
        "monitoring": ProductionConfig.MONITORING_CONFIG,
        "celery": ProductionConfig.CELERY_CONFIG
    }

def validate_deployment_config() -> Dict[str, Any]:
    """Validate deployment configuration"""
    issues = []
    warnings = []
    
    # Check required environment variables
    required_vars = [
        "DB_PASSWORD",
        "SECRET_KEY",
        "OPENAI_API_KEY"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"Missing required environment variable: {var}")
    
    # Check directory permissions
    dirs_to_check = [
        ProductionConfig.STORAGE_CONFIG["upload_dir"],
        ProductionConfig.STORAGE_CONFIG["cache_dir"],
        ProductionConfig.STORAGE_CONFIG["logs_dir"],
        ProductionConfig.MODEL_CONFIG["model_cache_dir"]
    ]
    
    for dir_path in dirs_to_check:
        try:
            os.makedirs(dir_path, exist_ok=True)
            # Test write permissions
            test_file = os.path.join(dir_path, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            issues.append(f"Cannot write to directory {dir_path}: {str(e)}")
    
    # Check security settings
    if ProductionConfig.SECURITY_CONFIG["secret_key"] == "your-secret-key-change-in-production":
        issues.append("SECRET_KEY is using default value - change in production!")
    
    if ProductionConfig.MONITORING_CONFIG["enable_debug"]:
        warnings.append("Debug mode is enabled - disable in production")
    
    # Check resource limits
    if ProductionConfig.API_CONFIG["workers"] > 8:
        warnings.append("High number of API workers - ensure sufficient resources")
    
    if ProductionConfig.DATABASE_CONFIG["pool_size"] > 50:
        warnings.append("Large database connection pool - monitor resource usage")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "config": get_deployment_config()
    }

def create_environment_template() -> str:
    """Create environment variables template"""
    template = """
# Phase 3-5 MultiModelVideo Production Environment
# Copy this file to .env and update the values

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=multimodelovideo
DB_USER=postgres
DB_PASSWORD=your_secure_password_here
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Redis Configuration  
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password_here
REDIS_MAX_CONNECTIONS=50

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_TIMEOUT=300
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Security Configuration
SECRET_KEY=your_very_secure_secret_key_here
JWT_EXPIRATION=86400
RATE_LIMIT_PER_MINUTE=100

# File Storage
UPLOAD_DIR=./uploads
CACHE_DIR=./cache
LOGS_DIR=./logs
MAX_FILE_SIZE=1073741824

# AI/ML Models
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=all-MiniLM-L6-v2
VISUAL_MODEL=yolov8n
GPU_ENABLED=false
MODEL_BATCH_SIZE=32

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
LOG_LEVEL=INFO
ENABLE_DEBUG=false
SENTRY_DSN=your_sentry_dsn_here

# Background Tasks
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
CELERY_CONCURRENCY=4
CELERY_MAX_TASKS_PER_CHILD=100
"""
    return template.strip()

if __name__ == "__main__":
    # Validate configuration and print results
    validation = validate_deployment_config()
    
    print("🔧 Production Configuration Validation")
    print("=" * 50)
    
    if validation["valid"]:
        print("✅ Configuration is valid!")
    else:
        print("❌ Configuration has issues:")
        for issue in validation["issues"]:
            print(f"  - {issue}")
    
    if validation["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
    
    print("\n📝 Environment Template:")
    print("-" * 30)
    print(create_environment_template())
