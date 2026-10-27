# -*- coding: utf-8 -*-
"""阶段一接口冒烟测试（需后端运行在 127.0.0.1:8000）。

运行：python scripts/smoke_stage1.py
"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"
passed = 0
failed = 0


def call(method, path, data=None, token=None, expect=200):
    url = BASE + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        status = exc.code
        payload = json.loads(exc.read().decode())
    return status, payload


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def login(account, password):
    status, body = call("POST", "/auth/login", {"account": account, "password": password})
    token = body.get("data", {}).get("access_token") if body.get("code") == 0 else None
    return status, body, token


print("== 1. 登录 ==")
status, body, admin_token = login("admin", "Admin@123")
check("管理员登录成功", status == 200 and bool(admin_token), body.get("message"))
status, body, refresh_token = (None, None, None)
status, body = call("POST", "/auth/login", {"account": "admin", "password": "wrong-pass"})
check("错误密码被拒绝", status == 401 and body["code"] == 10006, body.get("message"))

print("== 2. 当前用户 ==")
status, body = call("GET", "/auth/me", token=admin_token)
check("获取当前用户", status == 200 and body["data"]["role"] == "admin", body)

print("== 3. 用户列表 ==")
status, body = call("GET", "/users?page=1&page_size=20", token=admin_token)
check("用户列表返回 4 个账号", status == 200 and body["data"]["total"] >= 4,
      body.get("data", {}).get("total"))

print("== 4. 新增用户 ==")
status, body = call("POST", "/users", {
    "student_no": "staff02",
    "name": "测试员工",
    "phone": "13900000002",
    "password": "Test@1234",
    "role": "staff",
    "college": "校园驿站",
}, token=admin_token, expect=201)
new_id = body.get("data", {}).get("id") if status == 201 else None
check("新增工作人员", status == 201 and new_id is not None, body.get("message"))

status, body = call("POST", "/users", {
    "student_no": "staff02",
    "name": "重复手机号",
    "phone": "13900000002",
    "password": "Test@1234",
    "role": "staff",
}, token=admin_token, expect=409)
check("重复手机号被拒绝", status == 409 and body["code"] == 10005, body.get("message"))

print("== 5. 新账号登录与禁用 ==")
status, body, staff_token = login("staff02", "Test@1234")
check("新账号可登录", status == 200 and bool(staff_token), body.get("message"))

status, body = call("PATCH", f"/users/{new_id}/status", {"status": 0}, token=admin_token)
check("禁用账号", status == 200 and body["data"]["status"] == 0, body.get("message"))

status, body, _ = login("staff02", "Test@1234")
check("禁用后无法登录", status == 403 and body["code"] == 10003, body.get("message"))

status, body = call("PATCH", f"/users/{new_id}/status", {"status": 1}, token=admin_token)
check("恢复账号", status == 200 and body["data"]["status"] == 1, body.get("message"))

print("== 6. 越权访问 ==")
status, body, student_token = login("2023010101", "Student@123")
check("学生登录成功", status == 200 and bool(student_token), body.get("message"))
status, body = call("GET", "/users", token=student_token, expect=403)
check("学生访问用户管理被拒绝", status == 403 and body["code"] == 10003, body.get("message"))

status, body = call("GET", "/users", token=None, expect=401)
check("未登录访问被拒绝", status == 401 and body["code"] == 10002, body.get("message"))

print("== 7. 令牌刷新 ==")
status, body, _ = login("admin", "Admin@123")
refresh = body["data"]["refresh_token"]
status, body = call("POST", "/auth/refresh", {"refresh_token": refresh})
check("刷新令牌", status == 200 and bool(body["data"]["access_token"]), body.get("message"))

print("== 8. 修改密码 ==")
status, body = call("POST", "/users", {
    "student_no": "2023999999",
    "name": "改密测试",
    "phone": "13900000009",
    "password": "Init@1234",
    "role": "student",
}, token=admin_token, expect=201)
temp_id = body["data"]["id"]
status, body, temp_token = login("2023999999", "Init@1234")
status, body = call("PUT", "/auth/password", {
    "old_password": "Init@1234",
    "new_password": "Changed@1234",
}, token=temp_token)
check("修改密码成功", status == 200, body.get("message"))
status, body, _ = login("2023999999", "Changed@1234")
check("新密码可登录", status == 200, body.get("message"))
status, body, _ = login("2023999999", "Init@1234")
check("旧密码失效", status == 401, body.get("message"))

print("== 9. 注销 ==")
status, body = call("POST", "/auth/logout", token=temp_token)
check("退出登录", status == 200, body.get("message"))
status, body = call("GET", "/auth/me", token=temp_token, expect=401)
check("注销后令牌失效", status == 401 and body["code"] == 10002, body.get("message"))

print()
print(f"结果：{passed} 通过，{failed} 失败")
raise SystemExit(1 if failed else 0)
