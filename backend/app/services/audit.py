"""操作日志：按请求路径与方法推导模块、动作，并由中间件统一落库。"""
import re

from sqlalchemy.orm import Session

from app.models.operation_log import OperationLog

MODULE_LABELS = {
    "auth": "认证",
    "users": "用户",
    "stations": "驿站",
    "shelves": "货架",
    "packages": "包裹",
    "pickup-records": "取件记录",
    "shipments": "寄件",
    "notifications": "通知",
    "announcements": "公告",
    "exceptions": "异常",
    "stats": "统计",
    "logs": "日志",
}

ACTION_LABELS = {
    "login": "登录",
    "logout": "退出登录",
    "refresh": "刷新令牌",
    "change_password": "修改密码",
    "register": "注册",
    "create": "新增",
    "batch_inbound": "批量入库",
    "inbound": "入库",
    "pickup": "取件出库",
    "return": "登记退回",
    "exception": "登记异常",
    "move_shelf": "调整格口",
    "update": "修改",
    "delete": "删除",
    "toggle_status": "启停",
    "shipment_create": "寄件下单",
    "accept": "揽收",
    "ship": "登记发出",
    "complete": "确认完成",
    "cancel": "取消",
    "read": "标记已读",
    "read_all": "全部已读",
    "handle": "处理异常",
    "publish": "发布公告",
    "offline": "下架公告",
}

LAST_ACTIONS = {
    "batch": "batch_inbound",
    "pickup": "pickup",
    "return": "return",
    "exception": "exception",
    "shelf": "move_shelf",
    "accept": "accept",
    "ship": "ship",
    "complete": "complete",
    "cancel": "cancel",
    "status": "toggle_status",
    "read": "read",
    "read-all": "read_all",
    "password": "change_password",
    "login": "login",
    "logout": "logout",
    "refresh": "refresh",
    "register": "register",
}

METHOD_ACTIONS = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}


def resolve(path: str, method: str) -> tuple[str, str, str | None, int | None]:
    """返回（模块、动作、目标类型、目标 ID）。"""
    clean = path.split("?")[0]
    parts = [p for p in clean.strip("/").split("/") if p]
    if len(parts) >= 3 and parts[0] == "api":
        parts = parts[2:]
    elif parts and parts[0] == "api":
        parts = parts[1:]
    if not parts:
        return "system", method.lower(), None, None

    module = parts[0]
    if module == "pickup-records":
        module = "packages"

    action = METHOD_ACTIONS.get(method, method.lower())
    if module == "packages" and method == "POST":
        action = "inbound"
    if module == "shipments" and method == "POST":
        action = "shipment_create"
    if module == "announcements":
        action = "publish" if method == "POST" else (
            "offline" if method == "DELETE" else "update"
        )
    if module == "exceptions" and method == "PATCH":
        action = "handle"

    if len(parts) > 1:
        action = LAST_ACTIONS.get(parts[-1], action)

    target_id = None
    for part in reversed(parts):
        if part.isdigit():
            target_id = int(part)
            break

    return module, action, module if target_id else None, target_id


def write_log(
    db: Session,
    user_id: int | None,
    module: str,
    action: str,
    target_type: str | None,
    target_id: int | None,
    detail: dict,
    ip: str | None,
) -> None:
    db.add(
        OperationLog(
            user_id=user_id,
            module=module,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip=ip,
        )
    )
    db.commit()
