from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.core.redis_client import get_redis
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise ApiError(10002, "未登录或令牌失效", 401)

    try:
        payload = decode_token(credentials.credentials, "access")
    except ValueError as exc:
        raise ApiError(10002, str(exc), 401) from exc

    client = get_redis()
    if client is not None:
        try:
            if client.exists(f"jwt:blacklist:{payload.get('jti')}"):
                raise ApiError(10002, "令牌已失效，请重新登录", 401)
        except ApiError:
            raise
        except Exception:  # noqa: BLE001
            pass

    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise ApiError(10002, "用户不存在", 401)
    if user.status != 1:
        raise ApiError(10003, "账号已被禁用，请联系管理员", 403)

    request.state.token_payload = payload
    request.state.token = credentials.credentials
    request.state.user = user
    return user


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ApiError(10003, "无权限访问该资源", 403)
        return user

    return checker
