"""应用配置模块"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 数据库配置
    # Railway PostgreSQL: DATABASE_URL 会自动设置
    # 本地开发使用 SQLite
    DATABASE_URL: str = "sqlite+aiosqlite:///./warehouse_heatmap.db"
    
    # 应用配置
    SECRET_KEY: str = "your-super-secret-key"
    DEBUG: bool = True
    
    # CORS 配置（支持 * 表示允许所有源）
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # 热度计算权重
    HEAT_WEIGHT_FREQUENCY: float = 0.6
    HEAT_WEIGHT_TURNOVER: float = 0.4
    
    @property
    def cors_origins_list(self) -> List[str]:
        """获取 CORS 允许的源列表"""
        origins = self.CORS_ORIGINS.strip()
        # 支持 * 表示允许所有源
        if origins == "*":
            return ["*"]
        return [origin.strip() for origin in origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
