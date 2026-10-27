# -*- coding: utf-8 -*-
"""阶段三接口冒烟测试（需后端运行在 127.0.0.1:8000）。

运行：python scripts/smoke_stage3.py
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


print("== 1. 登录准备 ==")
admin = login("admin", "Admin@123")
staff = login("staff01", "Staff@123")
student = login("2023010101", "Student@123")
check("三个角色登录成功", all([admin, staff, student]))

print("== 2. 演示数据与统计 ==")
status, body = call("GET", "/packages/summary", token=staff)
summary = body.get("data", {}) if status == 200 else {}
check("统计接口返回在库数", status == 200 and summary.get("in_stock", 0) >= 3, summary)
check("统计接口返回超期数", status == 200 and summary.get("overdue", 0) >= 1, summary)
check("统计接口返回异常数", status == 200 and summary.get("exception", 0) >= 1, summary)

status, body = call("GET", "/packages?page=1&page_size=50", token=admin)
data = body.get("data", {})
check("管理员可见全部演示包裹", status == 200 and data.get("total", 0) >= 7, data.get("total"))

status, body = call("GET", "/packages?page=1&page_size=50&status=overdue", token=admin)
overdue_items = body.get("data", {}).get("items", [])
check("超期筛选返回有效状态", status == 200 and all(i["status"] == "overdue" for i in overdue_items),
      [i["status"] for i in overdue_items])
check("超期包裹带超期天数", bool(overdue_items) and overdue_items[0]["overdue_days"] >= 1,
      overdue_items[0] if overdue_items else None)

status, body = call("GET", "/packages?page=1&page_size=50", token=student)
mine = body.get("data", {})
check("学生只看到本人包裹", status == 200 and mine.get("total", 0) == 3, mine.get("total"))
check("学生包裹手机号已脱敏", all("****" in i["recipient_phone"] for i in mine.get("items", [])),
      mine.get("items", [{}])[0].get("recipient_phone") if mine.get("items") else None)

status, body = call("GET", "/packages?keyword=JD9876543210", token=admin)
other_id = body["data"]["items"][0]["id"]
status, body = call("GET", f"/packages/{other_id}", token=student)
check("学生不能查看他人包裹详情", status == 403 and body["code"] == 10003, body.get("message"))

status, body = call("GET", "/packages/track/YT6655443322", token=student)
check("学生按运单号查询本人包裹", status == 200 and body["data"]["tracking_no"] == "YT6655443322",
      body.get("message"))
status, body = call("GET", "/packages/track/JD9876543210", token=student)
check("学生不能按运单号查他人包裹", status == 403, body.get("message"))

print("== 3. 入库登记 ==")
tracking = f"TST{stamp}01"
payload = {
    "tracking_no": tracking,
    "station_id": 1,
    "recipient_phone": "13800000002",
    "courier_company": "顺丰速运",
    "package_type": "normal",
    "weight": 1.35,
    "remark": "接口冒烟测试",
}
status, body = call("POST", "/packages", payload, token=staff)
pkg = body.get("data", {}) if status == 201 else {}
pkg_id = pkg.get("id")
code = pkg.get("pickup_code")
check("单件入库成功并生成 6 位取件码", status == 201 and len(code or "") == 6, body.get("message"))
check("入库自动匹配收件人", pkg.get("recipient_id") is not None, pkg.get("recipient_id"))
check("入库自动分配货架", bool(pkg.get("shelf_code")), pkg.get("shelf_code"))

status, body = call("POST", "/packages", payload, token=staff)
check("重复运单号被拒绝", status == 409 and body["code"] == 20001, body.get("message"))
check("重复入库返回原包裹 id", body.get("data", {}).get("package_id") == pkg_id, body.get("data"))

status, body = call("POST", "/packages", {**payload, "tracking_no": f"TST{stamp}99", "recipient_phone": "12345"},
                    token=staff)
check("手机号格式错误被拒绝", status == 422, body.get("message"))

status, body = call("POST", "/packages", {**payload, "tracking_no": f"TST{stamp}98", "recipient_phone": "13800000009"},
                    token=student)
check("学生不能执行入库", status == 403 and body["code"] == 10003, body.get("message"))

print("== 4. 取件码查询与核验失败分支 ==")
status, body = call("GET", f"/packages/by-code/{code}", token=staff)
check("按取件码查到在库包裹", status == 200 and body["data"]["tracking_no"] == tracking, body.get("message"))
status, body = call("GET", f"/packages/by-code/{code}", token=student)
check("学生不能使用取件码检索", status == 403, body.get("message"))

status, body = call("POST", f"/packages/{pkg_id}/pickup",
                    {"pickup_code": "000001", "phone_suffix": "0002"}, token=staff)
check("取件码错误被拒绝", status == 400 and body["code"] == 20002, body.get("message"))

status, body = call("POST", f"/packages/{pkg_id}/pickup",
                    {"pickup_code": code, "phone_suffix": "0001"}, token=staff)
check("手机号后四位不符被拒绝", status == 400 and body["code"] == 20003, body.get("message"))

status, body = call("GET", "/stations", token=admin)
before_used = next(s for s in body["data"]["items"] if s["code"] == "ST-A")["used_count"]

print("== 5. 取件出库 ==")
status, body = call("POST", f"/packages/{pkg_id}/pickup",
                    {"pickup_code": code, "phone_suffix": "0002"}, token=staff)
picked = body.get("data", {}).get("package", {}) if status == 200 else {}
check("取件码+手机号核验通过出库", status == 200 and picked.get("status") == "picked", body.get("message"))
check("出库后清空取件码与货架", picked.get("pickup_code") is None and picked.get("shelf_id") is None, picked)
check("生成取件记录", body.get("data", {}).get("record", {}).get("package_id") == pkg_id, body.get("data"))

status, body = call("GET", "/stations", token=admin)
after_used = next(s for s in body["data"]["items"] if s["code"] == "ST-A")["used_count"]
check("出库后格口释放", after_used == before_used - 1, f"{before_used} -> {after_used}")

status, body = call("POST", f"/packages/{pkg_id}/pickup",
                    {"pickup_code": code, "phone_suffix": "0002"}, token=staff)
check("重复出库被拒绝", status == 409 and body["code"] == 20004, body.get("message"))

status, body = call("GET", f"/packages/{pkg_id}", token=admin)
timeline = body["data"].get("timeline", [])
check("包裹详情返回流转时间线", status == 200 and len(timeline) >= 2, timeline)

status, body = call("GET", f"/pickup-records?keyword={tracking}", token=staff)
records = body.get("data", {}).get("items", [])
check("取件记录可检索", status == 200 and len(records) == 1, body.get("data", {}).get("total"))
check("记录含核验方式", bool(records) and records[0]["verify_type"] == "code_phone",
      records[0] if records else None)

status, body = call("GET", "/pickup-records?today_only=true", token=staff)
check("今日取件记录含本次出库", status == 200 and body["data"]["total"] >= 1, body["data"].get("total"))

print("== 6. 批量入库 ==")
batch = {
    "station_id": 1,
    "items": [
        {"tracking_no": f"TST{stamp}11", "recipient_phone": "13800000003", "courier_company": "京东物流"},
        {"tracking_no": f"TST{stamp}12", "recipient_phone": "13800000002", "courier_company": "圆通速递",
         "package_type": "fragile", "weight": 2.1},
        {"tracking_no": tracking, "recipient_phone": "13800000002"},
    ],
}
status, body = call("POST", "/packages/batch", batch, token=staff)
result = body.get("data", {})
check("批量入库返回逐条结果", status == 200 and result.get("total") == 3, body.get("message"))
check("批量入库成功 2 件", result.get("success") == 2, result)
check("重复运单号在批量中失败且不中断", result.get("failed") == 1, result.get("items"))
batch_ids = [i["package_id"] for i in result.get("items", []) if i.get("success")]
check("批量结果返回包裹与取件码", all(i.get("pickup_code") for i in result.get("items", []) if i.get("success")),
      result.get("items"))

print("== 7. 调架、退回与异常 ==")
status, body = call("GET", "/stations/1/shelves", token=admin)
shelves = body["data"]["items"]
target_shelf = next(s for s in shelves if s["code"] == "A-02")

status, body = call("POST", f"/packages/{batch_ids[0]}/shelf", {"shelf_id": target_shelf["id"]}, token=staff)
check("调整货架成功", status == 200 and body["data"]["shelf_code"] == "A-02", body.get("message"))

status, body = call("POST", f"/packages/{batch_ids[0]}/return", {"reason": "收件人拒收"}, token=staff)
check("登记退回成功", status == 200 and body["data"]["status"] == "returned", body.get("message"))
check("退回后释放取件码", body["data"]["pickup_code"] is None, body.get("data"))

status, body = call("POST", f"/packages/{batch_ids[1]}/exception",
                    {"exception_type": "damaged", "remark": "外包装破损"}, token=staff)
check("登记异常件成功", status == 200 and body["data"]["status"] == "exception", body.get("message"))

status, body = call("GET", "/stations/1/shelves", token=admin)
check("退回收回格口后占用数正确",
      status == 200 and all(s["used_count"] <= s["capacity"] for s in body["data"]["items"]),
      [(s["code"], s["used_count"]) for s in body["data"]["items"]])

print("== 8. 容量与驿站状态约束 ==")
status, body = call("POST", "/stations", {
    "code": f"ST-F{stamp[-3:]}", "name": "满载测试驿站", "address": "测试地址 2 号",
    "open_time": "09:00", "close_time": "18:00",
}, token=admin)
full_station = body.get("data", {}).get("id") if status == 201 else None
call("POST", f"/stations/{full_station}/shelves", {"code": "F-01", "capacity": 1}, token=admin)

status, body = call("POST", "/packages", {
    "tracking_no": f"TST{stamp}21", "station_id": full_station,
    "recipient_phone": "13800000002", "courier_company": "中通快递",
}, token=admin)
check("空驿站可入库", status == 201, body.get("message"))

status, body = call("POST", "/packages", {
    "tracking_no": f"TST{stamp}22", "station_id": full_station,
    "recipient_phone": "13800000002", "courier_company": "中通快递",
}, token=admin)
check("格口已满时拒绝入库", status == 409 and body["code"] == 20005, body.get("message"))

call("PATCH", f"/stations/{full_station}/status", {"status": 0}, token=admin)
status, body = call("POST", "/packages", {
    "tracking_no": f"TST{stamp}23", "station_id": full_station,
    "recipient_phone": "13800000002", "courier_company": "中通快递",
}, token=admin)
check("停用驿站拒绝入库", status == 409 and body["code"] == 10005, body.get("message"))

print("== 9. 权限与未登录 ==")
status, body = call("GET", "/packages/summary", token=student)
check("学生不能查看运营统计", status == 403, body.get("message"))
status, body = call("GET", "/pickup-records", token=student)
check("学生不能查看取件记录", status == 403, body.get("message"))
status, body = call("GET", "/packages")
check("未登录访问包裹列表被拒绝", status == 401, body.get("message"))

print()
print(f"结果：{passed} 通过，{failed} 失败")
print(f"测试数据前缀：TST{stamp}（请在测试后清理）")
raise SystemExit(1 if failed else 0)
