"""用户相关 Pydantic 模式"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRoleEnum(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"


# ==================== Auth ====================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class LoginResponse(TokenResponse):
    """登录响应"""
    user: "UserResponse" = Field(..., description="用户信息")


# ==================== User ====================

class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")


class UserCreate(UserBase):
    """创建用户"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    role: UserRoleEnum = Field(default=UserRoleEnum.USER, description="用户角色")


class UserUpdate(BaseModel):
    """更新用户"""
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    role: Optional[UserRoleEnum] = Field(None, description="用户角色")
    is_active: Optional[bool] = Field(None, description="是否启用")


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    nickname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: UserRoleEnum
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class ResetPasswordRequest(BaseModel):
    """重置密码请求（管理员用）"""
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class UserProfileUpdate(BaseModel):
    """用户个人资料更新"""
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")


# 解决循环引用
LoginResponse.model_rebuild()
