from datetime import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.errors import ApiError
from app.core.redis_client import get_redis
from app.core.response import ok
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    token_remaining_seconds,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
)
from app.schemas.serializers import serialize_user

router = APIRouter(prefix="/auth", tags=["认证"])


def _issue_tokens(user: User) -> dict:
    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id, user.role),
        "token_type": "Bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": serialize_user(user, mask=False),
    }


@router.post("/login", summary="登录")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client = get_redis()
    fail_key = f"login:fail:{payload.account}"

    if client is not None:
        try:
            fails = int(client.get(fail_key) or 0)
            if fails >= settings.LOGIN_MAX_FAIL:
                raise ApiError(
                    10006,
                    f"密码错误次数过多，请 {settings.LOGIN_LOCK_MINUTES} 分钟后再试",
                    429,
                )
        except ApiError:
            raise
        except Exception:  # noqa: BLE001
            pass

    user = db.execute(
        select(User).where(
            or_(User.phone == payload.account, User.student_no == payload.account)
        )
    ).scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.password_hash):
        if client is not None:
            try:
                count = client.incr(fail_key)
                if count == 1:
                    client.expire(fail_key, settings.LOGIN_LOCK_MINUTES * 60)
            except Exception:  # noqa: BLE001
                pass
        raise ApiError(10006, "账号或密码错误，请重试", 401)

    if user.status != 1:
        raise ApiError(10003, "账号已被禁用，请联系管理员", 403)

    if client is not None:
        try:
            client.delete(fail_key)
        except Exception:  # noqa: BLE001
            pass

    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)

    return ok(request, _issue_tokens(user), "登录成功")


@router.post("/refresh", summary="刷新访问令牌")
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token, "refresh")
    except ValueError as exc:
        raise ApiError(10002, str(exc), 401) from exc

    user = db.get(User, int(decoded["sub"]))
    if user is None or user.status != 1:
        raise ApiError(10003, "账号不可用", 403)

    return ok(request, _issue_tokens(user), "刷新成功")


@router.post("/logout", summary="退出登录")
def logout(request: Request, user: User = Depends(get_current_user)):
    client = get_redis()
    payload = getattr(request.state, "token_payload", {})
    if client is not None and payload.get("jti"):
        try:
            client.setex(
                f"jwt:blacklist:{payload['jti']}",
                token_remaining_seconds(payload),
                "1",
            )
        except Exception:  # noqa: BLE001
            pass
    return ok(request, None, "已退出登录")


@router.get("/me", summary="当前用户信息")
def me(request: Request, user: User = Depends(get_current_user)):
    return ok(request, serialize_user(user, mask=False))


@router.put("/password", summary="修改本人密码")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.old_password, user.password_hash):
        raise ApiError(10006, "原密码不正确", 400)
    if payload.old_password == payload.new_password:
        raise ApiError(10005, "新密码不能与原密码相同", 400)

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return ok(request, None, "密码修改成功，请重新登录")


@router.post("/register", summary="学生注册")
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    exists_phone = db.execute(
        select(User.id).where(User.phone == payload.phone)
    ).scalar_one_or_none()
    if exists_phone:
        raise ApiError(10005, "该手机号已注册", 409)

    exists_no = db.execute(
        select(User.id).where(User.student_no == payload.student_no)
    ).scalar_one_or_none()
    if exists_no:
        raise ApiError(10005, "该学号已注册", 409)

    user = User(
        student_no=payload.student_no,
        name=payload.name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role="student",
        college=payload.college,
        status=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ok(request, serialize_user(user, mask=False), "注册成功", 201)
