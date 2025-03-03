import uuid
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config.enums import BusinessType, RedisInitKeyConfig
from config.env import AppConfig, JwtConfig
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.entity.vo.login_vo import Token, UserLogin, UserRegister
from module_admin.entity.vo.user_vo import CurrentUserModel, EditUserModel
from module_admin.service.login_service import CustomOAuth2PasswordRequestForm, LoginService, oauth2_scheme
from module_admin.service.user_service import UserService
from utils.log_util import logger
from utils.response_util import ResponseUtil

# 创建 FastAPI 的路由实例
loginController = APIRouter()


@loginController.post('/login', response_model=Token)
@Log(title='用户登录', business_type=BusinessType.OTHER, log_type='login')
async def login(
    request: Request, form_data: CustomOAuth2PasswordRequestForm = Depends(), query_db: AsyncSession = Depends(get_db)
):
    # 判断是否启用了验证码功能，从 Redis 中获取配置
    captcha_enabled = (
        True
        if await request.app.state.redis.get(f'{RedisInitKeyConfig.SYS_CONFIG.key}:sys.account.captchaEnabled')
        == 'true'
        else False
    )

    # 构建用户登录请求对象
    user = UserLogin(
        userName=form_data.username,
        password=form_data.password,
        code=form_data.code,
        uuid=form_data.uuid,
        loginInfo=form_data.login_info,
        captchaEnabled=captcha_enabled,
    )

    # 调用服务层进行用户认证
    result = await LoginService.authenticate_user(request, query_db, user)

    # 设置访问令牌的过期时间
    access_token_expires = timedelta(minutes=JwtConfig.jwt_expire_minutes)

    # 生成唯一的会话 ID
    session_id = str(uuid.uuid4())

    # 创建访问令牌，包含用户信息和会话 ID
    access_token = await LoginService.create_access_token(
        data={
            'user_id': str(result[0].user_id),
            'user_name': result[0].user_name,
            'dept_name': result[1].dept_name if result[1] else None,
            'session_id': session_id,
            'login_info': user.login_info,
        },
        expires_delta=access_token_expires,
    )

    # 如果允许同一时间多次登录，则将令牌存储在 Redis 中，以会话 ID 为键
    if AppConfig.app_same_time_login:
        await request.app.state.redis.set(
            f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{session_id}',
            access_token,
            ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes),
        )
    else:
        # 否则，以用户 ID 为键存储令牌，确保同一账号同一时间只能登录一次
        await request.app.state.redis.set(
            f'{RedisInitKeyConfig.ACCESS_TOKEN.key}:{result[0].user_id}',
            access_token,
            ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes),
        )

    # 更新用户的登录时间和状态
    await UserService.edit_user_services(
        query_db, EditUserModel(userId=result[0].user_id, loginDate=datetime.now(), type='status')
    )

    # 记录成功登录日志
    logger.info('登录成功')

    # 判断请求是否来自 Swagger 或 Redoc 文档，如果是则返回指定格式的结果
    request_from_swagger = request.headers.get('referer').endswith('docs') if request.headers.get('referer') else False
    request_from_redoc = request.headers.get('referer').endswith('redoc') if request.headers.get('referer') else False
    if request_from_swagger or request_from_redoc:
        return {'access_token': access_token, 'token_type': 'Bearer'}

    # 返回成功响应，包含访问令牌
    return ResponseUtil.success(msg='登录成功', dict_content={'token': access_token})


@loginController.get('/getInfo', response_model=CurrentUserModel)
async def get_login_user_info(
    request: Request, current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    # 记录获取用户信息成功日志
    logger.info('获取成功')

    # 返回当前用户信息
    return ResponseUtil.success(model_content=current_user)


@loginController.get('/getRouters')
async def get_login_user_routers(
    request: Request,
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    query_db: AsyncSession = Depends(get_db),
):
    # 记录获取用户路由成功日志
    logger.info('获取成功')

    # 调用服务层获取当前用户的路由信息
    user_routers = await LoginService.get_current_user_routers(current_user.user.user_id, query_db)

    # 返回路由信息
    return ResponseUtil.success(data=user_routers)


@loginController.post('/register', response_model=CrudResponseModel)
async def register_user(request: Request, user_register: UserRegister, query_db: AsyncSession = Depends(get_db)):
    # 调用服务层进行用户注册
    user_register_result = await LoginService.register_user_services(request, query_db, user_register)

    # 记录注册结果日志
    logger.info(user_register_result.message)

    # 返回注册结果
    return ResponseUtil.success(data=user_register_result, msg=user_register_result.message)


@loginController.post('/logout')
async def logout(request: Request, token: Optional[str] = Depends(oauth2_scheme)):
    # 解码 JWT 令牌，获取会话 ID
    payload = jwt.decode(
        token, JwtConfig.jwt_secret_key, algorithms=[JwtConfig.jwt_algorithm], options={'verify_exp': False}
    )
    session_id: str = payload.get('session_id')

    # 调用服务层进行用户退出操作
    await LoginService.logout_services(request, session_id)

    # 记录退出成功日志
    logger.info('退出成功')

    # 返回退出成功响应
    return ResponseUtil.success(msg='退出成功')
