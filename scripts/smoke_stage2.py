# -*- coding: utf-8 -*-
"""阶段二接口冒烟测试（需后端运行在 127.0.0.1:8000）。

运行：python scripts/smoke_stage2.py
"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"
passed = 0
failed = 0


def call(method, path, data=None, token=None):
    url = BASE + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())


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
    return status, body, body.get("data", {}).get("access_token") if body.get("code") == 0 else None


print("== 1. 登录准备 ==")
_, _, admin = login("admin", "Admin@123")
_, _, staff = login("staff01", "Staff@123")
_, _, student = login("2023010101", "Student@123")
check("三个角色登录成功", all([admin, staff, student]))

print("== 2. 驿站列表 ==")
status, body = call("GET", "/stations", token=admin)
items = body.get("data", {}).get("items", []) if status == 200 else []
check("驿站列表返回 2 个驿站", status == 200 and len(items) >= 2, len(items))
st_a = next((s for s in items if s["code"] == "ST-A"), None)
check("ST-A 容量为 84", st_a and st_a["capacity"] == 84, st_a and st_a["capacity"])
check("ST-A 有 3 个货架", st_a and st_a["shelf_count"] == 3, st_a and st_a["shelf_count"])
check("负责人姓名已返回", st_a and st_a["manager_name"] == "驿站值班员", st_a and st_a["manager_name"])

print("== 3. 新增驿站 ==")
payload = {
    "code": "ST-T",
    "name": "测试驿站",
    "address": "测试地址 1 号",
    "phone": "13800009999",
    "open_time": "09:00",
    "close_time": "18:00",
    "manager_id": 2,
}
status, body = call("POST", "/stations", payload, token=admin)
test_id = body.get("data", {}).get("id") if status == 201 else None
check("新增驿站成功", status == 201 and test_id, body.get("message"))

status, body = call("POST", "/stations", payload, token=admin)
check("重复编码被拒绝", status == 409 and body["code"] == 10005, body.get("message"))

status, body = call("POST", "/stations", {**payload, "code": "ST-X", "close_time": "08:00"}, token=admin)
check("结束时间早于开始时间被拒绝", status == 422, body.get("message"))

status, body = call("POST", "/stations", {**payload, "code": "ST-Y", "manager_id": 3}, token=admin)
check("负责人不能是学生", status == 422, body.get("message"))

print("== 4. 修改与状态 ==")
status, body = call("PUT", f"/stations/{test_id}", {"name": "测试驿站（改）"}, token=admin)
check("修改驿站名称", status == 200 and body["data"]["name"] == "测试驿站（改）", body.get("message"))

status, body = call("PATCH", f"/stations/{test_id}/status", {"status": 0}, token=admin)
check("停用驿站", status == 200 and body["data"]["status"] == 0, body.get("message"))
call("PATCH", f"/stations/{test_id}/status", {"status": 1}, token=admin)

print("== 5. 货架管理 ==")
status, body = call("POST", f"/stations/{test_id}/shelves", {"code": "T-01", "zone": "A 区", "capacity": 10}, token=admin)
shelf_id = body.get("data", {}).get("id") if status == 201 else None
check("新增货架成功", status == 201 and shelf_id, body.get("message"))

status, body = call("POST", f"/stations/{test_id}/shelves", {"code": "T-01", "capacity": 10}, token=admin)
check("重复货架编号被拒绝", status == 409 and body["code"] == 10005, body.get("message"))

status, body = call("GET", f"/stations/{test_id}/shelves", token=admin)
check("驿站容量随货架更新", status == 200 and body["data"]["station"]["capacity"] == 10,
      body.get("data", {}).get("station", {}).get("capacity"))

status, body = call("PUT", f"/shelves/{shelf_id}", {"capacity": 12}, token=admin)
check("修改货架容量", status == 200 and body["data"]["capacity"] == 12, body.get("message"))

status, body = call("PUT", f"/shelves/{shelf_id}", {"capacity": 0}, token=admin)
check("容量小于 1 被拒绝", status == 422, body.get("message"))

status, body = call("DELETE", f"/shelves/{shelf_id}", token=admin)
check("删除空闲货架", status == 200, body.get("message"))

status, body = call("GET", f"/stations/{test_id}", token=admin)
check("删除后驿站容量归零", status == 200 and body["data"]["capacity"] == 0, body.get("data", {}).get("capacity"))

print("== 6. 权限控制 ==")
status, body = call("GET", "/stations", token=staff)
check("工作人员可查看驿站", status == 200, body.get("message"))
status, body = call("POST", "/stations", {**payload, "code": "ST-Z"}, token=staff)
check("工作人员不能新增驿站", status == 403 and body["code"] == 10003, body.get("message"))
status, body = call("POST", f"/stations/{test_id}/shelves", {"code": "T-02", "capacity": 5}, token=staff)
check("工作人员不能新增货架", status == 403, body.get("message"))

status, body = call("GET", "/stations", token=student)
check("学生可查看驿站列表", status == 200, body.get("message"))
status, body = call("GET", f"/stations/{test_id}/shelves", token=student)
check("学生不能查看货架明细", status == 403 and body["code"] == 10003, body.get("message"))
status, body = call("GET", "/stations")
check("未登录访问被拒绝", status == 401, body.get("message"))

print()
print(f"结果：{passed} 通过，{failed} 失败")
raise SystemExit(1 if failed else 0)
