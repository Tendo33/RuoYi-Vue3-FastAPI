# 导入SQLAlchemy的异步引擎创建函数
# 导入用于URL编码的函数
from urllib.parse import quote_plus

# 导入SQLAlchemy的异步会话创建函数
# 导入SQLAlchemy的异步属性支持类
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

# 导入SQLAlchemy的ORM基类
from sqlalchemy.orm import DeclarativeBase

# 导入数据库配置类
from config.env import DataBaseConfig

# 根据数据库配置生成MySQL的异步数据库连接URL
ASYNC_SQLALCHEMY_DATABASE_URL = (
    f'mysql+asyncmy://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
    f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
)

# 如果数据库类型是PostgreSQL，则生成PostgreSQL的异步数据库连接URL
if DataBaseConfig.db_type == 'postgresql':
    ASYNC_SQLALCHEMY_DATABASE_URL = (
        f'postgresql+asyncpg://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@'
        f'{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}'
    )

# 创建异步数据库引擎，使用生成的数据库连接URL，并根据配置设置相关参数
async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,  # 数据库连接URL
    echo=DataBaseConfig.db_echo,  # 是否打印SQL语句
    max_overflow=DataBaseConfig.db_max_overflow,  # 连接池的最大溢出连接数
    pool_size=DataBaseConfig.db_pool_size,  # 连接池的大小
    pool_recycle=DataBaseConfig.db_pool_recycle,  # 连接池中连接的重用时间
    pool_timeout=DataBaseConfig.db_pool_timeout,  # 从连接池获取连接的超时时间
)

# 创建异步会话工厂，设置自动提交和自动刷新为False，并绑定到异步引擎
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine)


# 定义ORM基类，继承自AsyncAttrs和DeclarativeBase，用于定义数据库模型
class Base(AsyncAttrs, DeclarativeBase):
    pass
