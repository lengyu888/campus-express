# -*- coding: utf-8 -*-
"""阶段五接口冒烟测试（需后端运行在 127.0.0.1:8000）。

运行：python scripts/smoke_stage5.py
"""
import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"
passed = 0
failed = 0
stamp = str(int(time.time()))[-6:]


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
    return body.get("data", {}).get("access_token") if body.get("code") == 0 else None


def create_test_package(tracking):
    status, body = call("POST", "/packages", {
        "tracking_no": tracking, "station_id": 1, "recipient_phone": "13800000002",
        "courier_company": "顺丰速运", "weight": 1.0,
    }, token=staff)
    return body.get("data", {}) if status == 201 else {}


print("== 1. 登录准备 ==")
admin = login("admin", "Admin@123")
staff = login("staff01", "Staff@123")
student = login("2023010101", "Student@123")
check("三个角色登录成功", all([admin, staff, student]))

print("== 2. 异常件列表与权限 ==")
status, body = call("GET", "/exceptions", token=staff)
seed_items = body.get("data", {}).get("items", [])
check("异常列表返回演示数据", status == 200 and body["data"]["total"] >= 1, body.get("data", {}).get("total"))
check("异常记录含包裹与类型信息",
      bool(seed_items) and all(k in seed_items[0] for k in
                               ("tracking_no", "type_label", "status_label", "station_name")), True)

status, body = call("GET", "/exceptions/summary", token=staff)
check("异常统计接口可用", status == 200 and body["data"]["open"] >= 1, body.get("data"))

status, body = call("GET", "/exceptions", token=student)
check("学生不能查看异常列表", status == 403, body.get("message"))

status, body = call("POST", "/packages/1/exception", {"exception_type": "other"}, token=student)
check("学生不能登记异常", status == 403, body.get("message"))

print("== 3. 登记异常 ==")
pkg1 = create_test_package(f"TST5{stamp}01")
check("测试包裹入库成功", bool(pkg1.get("pickup_code")), pkg1)

status, body = call("POST", f"/packages/{pkg1['id']}/exception",
                    {"exception_type": "damaged", "remark": "外箱破损"}, token=staff)
check("登记异常成功", status == 200 and body["data"]["status"] == "exception", body.get("message"))

status, body = call("GET", "/exceptions?status=open", token=staff)
open_items = body["data"]["items"]
record1 = next((i for i in open_items if i["package_id"] == pkg1["id"]), None)
check("异常记录已生成", record1 is not None and record1["status"] == "open", open_items)
check("异常描述包含类型", record1 and "包装破损" in record1["description"], record1)

status, body = call("POST", f"/packages/{pkg1['id']}/exception",
                    {"exception_type": "other"}, token=staff)
check("重复登记异常被拒绝", status == 409 and body["code"] == 10005, body.get("message"))

print("== 4. 处理异常 ==")
status, body = call("PATCH", f"/exceptions/{record1['id']}",
                    {"status": "processing", "remark": "已联系收件人"}, token=staff)
check("异常转为处理中", status == 200 and body["data"]["status"] == "processing", body.get("message"))
check("记录处理人", body["data"].get("handler_name") == "驿站值班员", body["data"].get("handler_name"))

status, body = call("PATCH", f"/exceptions/{record1['id']}",
                    {"status": "resolved", "package_action": "restock", "remark": "收件人确认可取"},
                    token=staff)
check("异常解决并重新入库", status == 200 and body["data"]["status"] == "resolved", body.get("message"))

status, body = call("GET", f"/packages/{pkg1['id']}", token=staff)
check("包裹恢复为在库", status == 200 and body["data"]["status"] in ("in_stock", "overdue"),
      body["data"].get("status"))
check("包裹保留原货架", body["data"].get("shelf_code") is not None, body["data"].get("shelf_code"))

status, body = call("PATCH", f"/exceptions/{record1['id']}", {"status": "processing"}, token=staff)
check("已解决异常不能重复处理", status == 409, body.get("message"))

print("== 5. 异常退回 ==")
pkg2 = create_test_package(f"TST5{stamp}02")
status, body = call("GET", "/stations", token=admin)
before_used = next(s for s in body["data"]["items"] if s["code"] == "ST-A")["used_count"]

status, body = call("POST", f"/packages/{pkg2['id']}/exception",
                    {"exception_type": "lost", "remark": "包裹丢失"}, token=staff)
check("登记丢失类异常成功", status == 200, body.get("message"))
status, body = call("GET", "/exceptions?status=open", token=staff)
record2 = next(i for i in body["data"]["items"] if i["package_id"] == pkg2["id"])
status, body = call("PATCH", f"/exceptions/{record2['id']}",
                    {"status": "resolved", "package_action": "returned", "remark": "确认丢失，退回发件方"},
                    token=staff)
check("异常解决并退回", status == 200 and body["data"]["status"] == "resolved", body.get("message"))

status, body = call("GET", f"/packages/{pkg2['id']}", token=staff)
check("包裹状态变为已退回", body["data"]["status"] == "returned", body["data"].get("status"))
check("退回后释放格口", body["data"]["shelf_id"] is None, body["data"].get("shelf_id"))

status, body = call("GET", "/stations", token=admin)
after_used = next(s for s in body["data"]["items"] if s["code"] == "ST-A")["used_count"]
check("驿站占用数回落", after_used == before_used - 1, f"{before_used} -> {after_used}")

print("== 6. 操作日志 ==")
status, body = call("GET", "/logs?page=1&page_size=50", token=admin)
logs = body.get("data", {}).get("items", [])
check("管理员可查看操作日志", status == 200 and body["data"]["total"] > 0, body.get("data", {}).get("total"))
check("日志含模块与动作标签",
      bool(logs) and all(l.get("module_label") and l.get("action_label") for l in logs), True)
check("日志含操作人", any(l["user_name"] for l in logs), True)
check("日志含请求路径详情", any((l.get("detail") or {}).get("path") for l in logs), True)

status, body = call("GET", "/logs?module=packages", token=admin)
check("按模块筛选日志", status == 200 and all(l["module"] == "packages" for l in body["data"]["items"]),
      body.get("data", {}).get("total"))

status, body = call("GET", "/logs?module=auth&action=login", token=admin)
check("登录操作已记录", status == 200 and body["data"]["total"] >= 1, body.get("data", {}).get("total"))

status, body = call("GET", "/logs/summary", token=admin)
check("日志统计返回模块分布", status == 200 and len(body["data"].get("modules", [])) >= 2,
      body.get("data"))

status, body = call("GET", "/logs", token=staff)
check("工作人员不能查看日志", status == 403, body.get("message"))

print("== 7. 失败请求不写日志 ==")
status, body = call("GET", "/logs/summary", token=admin)
before_total = body["data"]["total"]
call("POST", "/packages", {
    "tracking_no": f"TST5{stamp}01", "station_id": 1, "recipient_phone": "13800000002",
    "courier_company": "顺丰速运",
}, token=staff)  # 重复运单，返回 409
time.sleep(0.4)
status, body = call("GET", "/logs/summary", token=admin)
check("失败请求不产生日志", body["data"]["total"] == before_total,
      f"{before_total} -> {body['data']['total']}")

print("== 8. 权限与未登录 ==")
status, body = call("GET", "/exceptions")
check("未登录访问异常被拒绝", status == 401, body.get("message"))
status, body = call("PATCH", "/exceptions/999999", {"status": "resolved"}, token=staff)
check("异常不存在返回 404", status == 404, body.get("message"))

print()
print(f"结果：{passed} 通过，{failed} 失败")
print(f"测试数据前缀：TST5{stamp}")
raise SystemExit(1 if failed else 0)
