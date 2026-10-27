from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.errors import ApiError
from app.core.response import ok
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.serializers import serialize_user
from app.schemas.user import StatusUpdate, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", summary="用户列表")
def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = None,
    status: int | None = None,
    keyword: str | None = None,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    if status is not None:
        stmt = stmt.where(User.status == status)
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(User.name.like(like), User.phone.like(like), User.student_no.like(like))
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        db.execute(
            stmt.order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    return ok(
        request,
        {
            "items": [serialize_user(u) for u in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    )


@router.post("", summary="新增用户")
def create_user(
    payload: UserCreate,
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if db.execute(select(User.id).where(User.phone == payload.phone)).scalar_one_or_none():
        raise ApiError(10005, "该手机号已存在", 409)
    if payload.student_no and db.execute(
        select(User.id).where(User.student_no == payload.student_no)
    ).scalar_one_or_none():
        raise ApiError(10005, "该学号/工号已存在", 409)
    if payload.role != "student" and not payload.student_no:
        raise ApiError(10001, "工作人员与管理员必须填写工号", 422)

    user = User(
        student_no=payload.student_no,
        name=payload.name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role=payload.role,
        college=payload.college,
        status=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ok(request, serialize_user(user), "用户创建成功", 201)


@router.get("/{user_id}", summary="用户详情")
def get_user(
    user_id: int,
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise ApiError(10004, "用户不存在", 404)
    return ok(request, serialize_user(user, mask=False))


@router.put("/{user_id}", summary="修改用户")
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise ApiError(10004, "用户不存在", 404)

    if payload.name is not None:
        user.name = payload.name
    if payload.college is not None:
        user.college = payload.college
    if payload.role is not None:
        user.role = payload.role

    db.commit()
    db.refresh(user)
    return ok(request, serialize_user(user), "用户信息已更新")


@router.patch("/{user_id}/status", summary="启用或禁用用户")
def update_status(
    user_id: int,
    payload: StatusUpdate,
    request: Request,
    current: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if user_id == current.id:
        raise ApiError(10005, "不能禁用当前登录账号", 400)

    user = db.get(User, user_id)
    if user is None:
        raise ApiError(10004, "用户不存在", 404)

    user.status = payload.status
    db.commit()
    db.refresh(user)
    return ok(request, serialize_user(user), "账号状态已更新")
