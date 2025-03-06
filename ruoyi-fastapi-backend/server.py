from contextlib import asynccontextmanager  # 导入异步上下文管理器，用于管理FastAPI的生命周期

from fastapi import FastAPI  # 导入FastAPI框架，用于创建Web应用

from config.env import AppConfig  # 导入应用配置，获取应用的名称、版本等信息
from config.get_db import init_create_table  # 导入数据库初始化函数，用于创建数据库表
from config.get_redis import RedisUtil  # 导入Redis工具类，用于操作Redis
from config.get_scheduler import SchedulerUtil  # 导入调度器工具类，用于管理定时任务
from exceptions.handle import handle_exception  # 导入全局异常处理函数，用于捕获和处理异常
from middlewares.handle import handle_middleware  # 导入中间件处理函数，用于添加中间件
from module_admin.controller.cache_controller import cacheController  # 导入缓存管理控制器
from module_admin.controller.captcha_controller import captchaController  # 导入验证码管理控制器
from module_admin.controller.common_controller import commonController  # 导入通用模块控制器
from module_admin.controller.config_controller import configController  # 导入参数管理控制器
from module_admin.controller.dept_controller import deptController  # 导入部门管理控制器
from module_admin.controller.dict_controller import dictController  # 导入字典管理控制器
from module_admin.controller.job_controller import jobController  # 导入定时任务管理控制器
from module_admin.controller.log_controller import logController  # 导入日志管理控制器
from module_admin.controller.login_controller import loginController  # 导入登录管理控制器
from module_admin.controller.menu_controller import menuController  # 导入菜单管理控制器
from module_admin.controller.notice_controller import noticeController  # 导入通知公告管理控制器
from module_admin.controller.online_controller import onlineController  # 导入在线用户管理控制器
from module_admin.controller.post_controler import postController  # 导入岗位管理控制器
from module_admin.controller.role_controller import roleController  # 导入角色管理控制器
from module_admin.controller.server_controller import serverController  # 导入服务器管理控制器
from module_admin.controller.user_controller import userController  # 导入用户管理控制器
from module_generator.controller.gen_controller import genController  # 导入代码生成控制器
from sub_applications.handle import handle_sub_applications  # 导入子应用处理函数，用于挂载子应用
from utils.common_util import worship  # 导入通用工具函数，用于执行一些通用操作
from utils.log_util import logger  # 导入日志工具，用于记录日志


# 生命周期事件
@asynccontextmanager
async def lifespan(app: FastAPI):  # 定义异步上下文管理器，用于管理FastAPI的生命周期
    logger.info(f'{AppConfig.app_name}开始启动')  # 记录应用启动日志
    worship()  # 执行通用操作
    await init_create_table()  # 初始化数据库表
    app.state.redis = await RedisUtil.create_redis_pool()  # 创建Redis连接池，并将其存储在应用状态中
    await RedisUtil.init_sys_dict(app.state.redis)  # 初始化系统字典数据到 Redis
    await RedisUtil.init_sys_config(app.state.redis)  # 初始化系统配置数据到 Redis
    await SchedulerUtil.init_system_scheduler()  # 初始化系统调度器
    logger.info(f'{AppConfig.app_name}启动成功')  # 记录应用启动成功日志
    yield  # 暂停执行，等待应用运行
    await RedisUtil.close_redis_pool(app)  # 关闭Redis连接池
    await SchedulerUtil.close_system_scheduler()  # 关闭系统调度器


# 初始化FastAPI对象
app = FastAPI(  # 创建FastAPI应用实例
    title=AppConfig.app_name,  # 设置应用标题
    description=f'{AppConfig.app_name}接口文档',  # 设置应用描述
    version=AppConfig.app_version,  # 设置应用版本
    lifespan=lifespan,  # 设置应用的生命周期管理函数
    docs_url='/docs',
    openapi_url='/openapi.json',
)

# 挂载子应用
handle_sub_applications(app)  # 挂载子应用到主应用
# 加载中间件处理方法
handle_middleware(app)  # 添加中间件到应用
# 加载全局异常处理方法
handle_exception(app)  # 添加全局异常处理到应用


# 加载路由列表
controller_list = [  # 定义控制器列表，每个控制器对应一个模块
    {'router': loginController, 'tags': ['登录模块']},  # 登录模块控制器
    {'router': captchaController, 'tags': ['验证码模块']},  # 验证码模块控制器
    {'router': userController, 'tags': ['系统管理-用户管理']},  # 用户管理控制器
    {'router': roleController, 'tags': ['系统管理-角色管理']},  # 角色管理控制器
    {'router': menuController, 'tags': ['系统管理-菜单管理']},  # 菜单管理控制器
    {'router': deptController, 'tags': ['系统管理-部门管理']},  # 部门管理控制器
    {'router': postController, 'tags': ['系统管理-岗位管理']},  # 岗位管理控制器
    {'router': dictController, 'tags': ['系统管理-字典管理']},  # 字典管理控制器
    {'router': configController, 'tags': ['系统管理-参数管理']},  # 参数管理控制器
    {'router': noticeController, 'tags': ['系统管理-通知公告管理']},  # 通知公告管理控制器
    {'router': logController, 'tags': ['系统管理-日志管理']},  # 日志管理控制器
    {'router': onlineController, 'tags': ['系统监控-在线用户']},  # 在线用户管理控制器
    {'router': jobController, 'tags': ['系统监控-定时任务']},  # 定时任务管理控制器
    {'router': serverController, 'tags': ['系统监控-菜单管理']},  # 服务器管理控制器
    {'router': cacheController, 'tags': ['系统监控-缓存监控']},  # 缓存监控控制器
    {'router': commonController, 'tags': ['通用模块']},  # 通用模块控制器
    {'router': genController, 'tags': ['代码生成']},  # 代码生成控制器
]

for controller in controller_list:  # 遍历控制器列表
    app.include_router(
        router=controller.get('router'), tags=controller.get('tags')
    )  # 将每个控制器的路由添加到应用中，并设置标签
