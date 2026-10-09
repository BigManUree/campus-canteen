from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置
    
    优先级：环境变量 > .env 文件 > 默认值
    """
    
    # ============================================================
    # 数据库配置
    # ============================================================
    database_url: str = "mysql+pymysql://root:password@localhost:3306/campus_canteen_order"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600
    
    # ============================================================
    # JWT 安全配置
    # ============================================================
    jwt_secret: str = "change_me"
    jwt_expire: int = 7200
    
    # ============================================================
    # 文件上传配置
    # 默认固定到项目根目录 uploads，避免不同机器上的绝对路径权限问题
    media_upload_path: str = "uploads"
    max_upload_size: int = 10  # MB
    
    # ============================================================
    # 管理员注册配置
    # ============================================================
    admin_register_key: str = ""  # 管理员注册密钥，为空则不允许通过密钥注册
    
    # ============================================================
    # 服务器配置
    # ============================================================
    host: str = "0.0.0.0"
    port: int = 8000
    env: str = "development"  # development/production
    base_url: str = "http://localhost:8000"  # 服务器基础URL，用于生成完整的图片访问路径
    
    # ============================================================
    # 日志配置
    # ============================================================
    log_level: str = "INFO"
    log_file: str = ""
    
    # ============================================================
    # CORS 配置
    # ============================================================
    cors_origins: str = "*"  # 多个用逗号分隔，生产环境建议指定具体域名
    cors_allow_credentials: bool = True  # 是否允许携带凭证（cookies）
    cors_allow_methods: str = "*"  # 允许的 HTTP 方法，多个用逗号分隔
    cors_allow_headers: str = "*"  # 允许的请求头，多个用逗号分隔
    cors_expose_headers: str = ""  # 暴露给前端的响应头，多个用逗号分隔
    cors_max_age: int = 600  # 预检请求的缓存时间（秒）
    
    # ============================================================
    # 业务配置
    # ============================================================
    order_auto_cancel_minutes: int = 30  # 未支付订单自动取消时间
    pickup_code_expire_hours: int = 24  # 取餐码有效期
    
    # ============================================================
    # 消息通知配置
    # ============================================================
    enable_message_notification: bool = True  # 是否启用消息通知
    enable_wechat_notification: bool = False  # 是否启用微信通知
    enable_sms_notification: bool = False  # 是否启用短信通知
    
    # 微信配置（如果启用微信通知）
    wechat_template_id: str = ""  # 微信模板消息ID
    
    # 短信配置（如果启用短信通知）
    sms_sign_name: str = "校园食堂点餐"  # 短信签名
    sms_template_code: str = ""  # 短信模板代码
    
    # ============================================================
    # 短信/邮件配置（可选）
    # ============================================================
    sms_api_key: str = ""
    sms_api_secret: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    
    # ============================================================
    # 支付配置（可选）
    # ============================================================
    wechat_app_id: str = ""
    wechat_mch_id: str = ""
    wechat_api_key: str = ""
    alipay_app_id: str = ""
    alipay_private_key: str = ""
    alipay_public_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_cors_origins_list(self) -> list[str]:
        """获取 CORS 允许的来源列表"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    def get_cors_methods_list(self) -> list[str]:
        """获取 CORS 允许的方法列表"""
        if self.cors_allow_methods == "*":
            return ["*"]
        return [method.strip().upper() for method in self.cors_allow_methods.split(",") if method.strip()]
    
    def get_cors_headers_list(self) -> list[str]:
        """获取 CORS 允许的请求头列表"""
        if self.cors_allow_headers == "*":
            return ["*"]
        return [header.strip() for header in self.cors_allow_headers.split(",") if header.strip()]
    
    def get_cors_expose_headers_list(self) -> list[str]:
        """获取 CORS 暴露的响应头列表"""
        if not self.cors_expose_headers:
            return []
        return [header.strip() for header in self.cors_expose_headers.split(",") if header.strip()]
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.env.lower() == "production"
    
    def validate_required_settings(self):
        """验证必需的配置项（生产环境）"""
        if self.is_production():
            errors = []
            
            if self.jwt_secret == "change_me":
                errors.append("JWT_SECRET 必须在生产环境中修改")
            
            if len(self.jwt_secret) < 32:
                errors.append("JWT_SECRET 长度应至少为32位")
            
            if "password" in self.database_url.lower() and "your_password" in self.database_url.lower():
                errors.append("DATABASE_URL 必须配置正确的数据库密码")
            
            # 生产环境 CORS 安全检查
            if self.cors_origins == "*" and self.cors_allow_credentials:
                errors.append("生产环境不建议同时使用 CORS_ORIGINS=* 和 CORS_ALLOW_CREDENTIALS=True")
            
            if errors:
                raise ValueError(f"生产环境配置错误：\n" + "\n".join(f"  - {e}" for e in errors))


@lru_cache()
def get_settings() -> Settings:
    """获取配置（单例模式）
    
    Pydantic Settings 会自动从环境变量读取，无需手动处理
    优先级：环境变量 > .env 文件 > 默认值
    """
    settings = Settings()
    
    # 生产环境验证配置
    try:
        settings.validate_required_settings()
    except ValueError as e:
        from app.core.logging import logger
        logger.warning(str(e))
    
    return settings

