from config.database import (  # 从config.database模块中导入异步引擎、异步会话本地对象和Base类
    AsyncSessionLocal,
    Base,
    async_engine,
)
from utils.log_util import logger  # 从utils.log_util模块中导入logger对象，用于记录日志


async def get_db():
    """
    每一个请求处理完毕后会关闭当前连接，不同的请求使用不同的连接

    :return:
    """
    async with AsyncSessionLocal() as current_db:  # 使用异步上下文管理器创建一个新的数据库会话
        yield current_db  # 返回当前会话，并在使用完毕后自动关闭连接


async def init_create_table():
    """
    应用启动时初始化数据库连接

    :return:
    """
    logger.info('初始化数据库连接...')  # 记录日志，表示正在初始化数据库连接
    async with async_engine.begin() as conn:  # 使用异步上下文管理器开始一个数据库连接
        await conn.run_sync(Base.metadata.create_all)  # 执行同步操作，创建所有数据库表
    logger.info('数据库连接成功')  # 记录日志，表示数据库连接成功
