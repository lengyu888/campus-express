from fastapi import Request
from fastapi.responses import JSONResponse


def ok(request: Request, data=None, message: str = "success", status_code: int = 200):
    return JSONResponse(
        status_code=status_code,
        content={
            "code": 0,
            "message": message,
            "data": data,
            "request_id": getattr(request.state, "request_id", ""),
        },
    )


def fail(request: Request, code: int, message: str, status_code: int = 400, data=None):
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "data": data,
            "request_id": getattr(request.state, "request_id", ""),
        },
    )
