class ApiError(Exception):
    """业务异常，由全局异常处理器转换为统一响应。"""

    def __init__(self, code: int, message: str, status_code: int = 400, data=None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.data = data
        super().__init__(message)
