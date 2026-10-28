import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import ApiError
from app.core.redis_client import get_redis
from app.core.response import ok
from app.db.session import SessionLocal, engine
from app.services.audit import resolve, write_log

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("campus-express")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="校园快递收发系统后端接口",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = uuid.uuid4().hex
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Process-Time"] = f"{(time.perf_counter() - start) * 1000:.1f}ms"
    return response


AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@app.middleware("http")
async def audit_trail(request: Request, call_next):
    """对成功的写操作统一记录操作日志，失败请求不落库。"""
    response = await call_next(request)
    try:
        if (
            request.url.path.startswith(settings.API_V1_PREFIX)
            and request.method in AUDIT_METHODS
            and response.status_code < 400
        ):
            user = getattr(request.state, "user", None)
            module, action, target_type, target_id = resolve(request.url.path, request.method)
            with SessionLocal() as db:
                write_log(
                    db,
                    user.id if user else None,
                    module,
                    action,
                    target_type,
                    target_id,
                    {
                        "method": request.method,
                        "path": request.url.path,
                        "status": response.status_code,
                    },
                    request.client.host if request.client else None,
                )
    except Exception as exc:  # noqa: BLE001
        logger.warning("audit log failed: %s", exc)
    return response


@app.exception_handler(ApiError)
async def handle_api_error(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": exc.data,
            "request_id": getattr(request.state, "request_id", ""),
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = ".".join(str(x) for x in err.get("loc", []) if x != "body")
        errors.append({"field": field, "message": err.get("msg", "参数错误")})
    first = errors[0]["message"] if errors else "参数校验失败"
    return JSONResponse(
        status_code=422,
        content={
            "code": 10001,
            "message": first,
            "data": {"errors": errors},
            "request_id": getattr(request.state, "request_id", ""),
        },
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, exc: StarletteHTTPException):
    mapping = {401: 10002, 403: 10003, 404: 10004, 409: 10005}
    code = mapping.get(exc.status_code, 50000 if exc.status_code >= 500 else 10005)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": code,
            "message": str(exc.detail),
            "data": None,
            "request_id": getattr(request.state, "request_id", ""),
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception):
    logger.exception("unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "code": 50000,
            "message": "服务器内部错误，请稍后重试",
            "data": None,
            "request_id": getattr(request.state, "request_id", ""),
        },
    )


@app.get("/health", tags=["系统"], summary="健康检查")
@app.get(f"{settings.API_V1_PREFIX}/health", tags=["系统"], summary="健康检查（API 前缀）", include_in_schema=False)
def health(request: Request):
    db_ok = True
    redis_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False
    try:
        redis_ok = get_redis() is not None
    except Exception:  # noqa: BLE001
        redis_ok = False

    status = "ok" if db_ok else "degraded"
    return ok(
        request,
        {
            "status": status,
            "database": "up" if db_ok else "down",
            "redis": "up" if redis_ok else "down",
            "version": settings.APP_VERSION,
        },
    )


@app.get("/", tags=["系统"], summary="服务信息")
def index(request: Request):
    return ok(
        request,
        {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "api": settings.API_V1_PREFIX,
        },
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
def on_startup():
    logger.info("%s %s started", settings.APP_NAME, settings.APP_VERSION)
