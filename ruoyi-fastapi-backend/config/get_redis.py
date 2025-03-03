from fastapi import FastAPI
from redis import Redis
from redis import asyncio as aioredis
from redis.exceptions import AuthenticationError, RedisError, TimeoutError

from config.database import AsyncSessionLocal
from config.env import RedisConfig
from module_admin.service.config_service import ConfigService
from module_admin.service.dict_service import DictDataService
from utils.log_util import logger


class RedisUtil:
    """
    Redis相关方法
    """

    @classmethod
    async def create_redis_pool(cls) -> aioredis.Redis:
        """
        应用启动时初始化redis连接

        :return: aioredis.Redis: Redis连接对象
        """
        logger.info('开始连接redis...')
        # 使用aioredis.from_url方法创建Redis连接池
        redis:Redis = await aioredis.from_url(
            url=f'redis://{RedisConfig.redis_host}',  # Redis服务器地址
            port=RedisConfig.redis_port,  # Redis服务器端口
            username=RedisConfig.redis_username,  # Redis用户名
            password=RedisConfig.redis_password,  # Redis密码
            db=RedisConfig.redis_database,  # Redis数据库编号
            encoding='utf-8',  # 编码格式
            decode_responses=True,  # 是否自动解码响应
        )
        try:
            # 测试Redis连接是否成功
            connection = await redis.ping()
            if connection:
                logger.info('redis连接成功')
            else:
                logger.error('redis连接失败')
        except AuthenticationError as e:
            # 处理认证错误
            logger.error(f'redis用户名或密码错误，详细错误信息：{e}')
        except TimeoutError as e:
            # 处理连接超时错误
            logger.error(f'redis连接超时，详细错误信息：{e}')
        except RedisError as e:
            # 处理其他Redis错误
            logger.error(f'redis连接错误，详细错误信息：{e}')
        return redis

    @classmethod
    async def close_redis_pool(cls, app: FastAPI):
        """
        应用关闭时关闭redis连接

        :param app: fastapi对象
        :return: None
        """
        # 关闭Redis连接
        await app.state.redis.close()
        logger.info('关闭redis连接成功')

    @classmethod
    async def init_sys_dict(cls, redis: aioredis.Redis):
        """
        应用启动时缓存字典表

        :param redis: aioredis.Redis: Redis对象
        :return: None
        """
        # 初始化字典表缓存
        async with AsyncSessionLocal() as session:
            await DictDataService.init_cache_sys_dict_services(session, redis)

    @classmethod
    async def init_sys_config(cls, redis: aioredis.Redis):
        """
        应用启动时缓存参数配置表

        :param redis: aioredis.Redis: Redis对象
        :return: None
        """
        # 初始化参数配置表缓存
        async with AsyncSessionLocal() as session:
            await ConfigService.init_cache_sys_config_services(session, redis)
