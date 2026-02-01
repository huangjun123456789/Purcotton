"""数据库连接模块"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import select
from app.config import settings

# 根据数据库类型配置引擎参数
engine_kwargs = {
    "echo": settings.DEBUG,
}

# SQLite 不支持连接池参数
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20
    })

# 创建异步引擎
engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 声明基类
Base = declarative_base()


async def get_db():
    """获取数据库会话的依赖函数"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def init_default_admin():
    """初始化默认管理员账户"""
    from app.models.user import User, UserRole
    from app.auth import get_password_hash
    
    async with AsyncSessionLocal() as session:
        # 检查是否已存在管理员
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        existing_admin = result.scalar_one_or_none()
        
        if not existing_admin:
            # 创建默认管理员
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                nickname="系统管理员",
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(admin)
            await session.commit()
            print("默认管理员账户创建成功: admin / admin123")
        else:
            print("管理员账户已存在，跳过创建")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
