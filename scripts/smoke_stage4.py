# -*- coding: utf-8 -*-
"""阶段四接口冒烟测试（需后端运行在 127.0.0.1:8000）。

运行：python scripts/smoke_stage4.py
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
other = login("2023010102", "Student@123")
check("四个账号登录成功", all([admin, staff, student, other]))

print("== 2. 寄件列表与统计 ==")
status, body = call("GET", "/shipments?page=1&page_size=50", token=student)
data = body.get("data", {})
check("学生只看到本人寄件", status == 200 and data.get("total") == 3, data.get("total"))
check("寄件列表返回状态标签", all(i.get("status_label") for i in data.get("items", [])), True)

status, body = call("GET", "/shipments?page=1&page_size=50", token=admin)
check("管理员看到全部寄件", status == 200 and body["data"]["total"] >= 5, body["data"].get("total"))

status, body = call("GET", "/shipments/summary", token=student)
summary = body.get("data", {})
check("寄件统计按寄件人过滤", status == 200 and summary.get("total") == 3, summary)
check("统计包含各状态数量", all(k in summary for k in
                              ("pending", "accepted", "shipped", "completed", "cancelled")), summary)

status, body = call("GET", "/shipments", token=other)
check("另一学生看不到他人订单", status == 200 and body["data"]["total"] == 2, body["data"].get("total"))

print("== 3. 下单与运费估算 ==")
payload = {
    "station_id": 1,
    "receiver_name": "测试收件人",
    "receiver_phone": "13900007777",
    "receiver_address": "江苏省南京市栖霞区仙林大道 163 号",
    "item_name": "测试物品",
    "weight": 2.5,
    "remark": "冒烟测试",
}
status, body = call("POST", "/shipments", payload, token=student)
order = body.get("data", {})
order_id = order.get("id")
check("学生创建寄件订单成功", status == 201 and order_id, body.get("message"))
check("订单号格式为 S+日期+序号", str(order.get("order_no", "")).startswith("S") and
      len(str(order.get("order_no"))) == 15, order.get("order_no"))
check("运费按首重+续重计算（2.5kg→12 元）", order.get("freight") == 12.0, order.get("freight"))
check("下单生成首条轨迹", len(order.get("tracks", [])) == 1, order.get("tracks"))
check("订单初始状态为待揽收", order.get("status") == "pending", order.get("status"))

status, body = call("POST", "/shipments", payload, token=staff)
check("工作人员不能创建寄件", status == 403, body.get("message"))

status, body = call("POST", "/shipments", {**payload, "weight": 0.05}, token=student)
check("重量小于 0.1kg 被拒绝", status == 422, body.get("message"))

status, body = call("POST", "/shipments", {**payload, "receiver_phone": "12345"}, token=student)
check("收件人手机号格式校验", status == 422, body.get("message"))

status, body = call("GET", f"/shipments/{order_id}", token=other)
check("他人不能查看订单详情", status == 403 and body["code"] == 10003, body.get("message"))

print("== 4. 揽收、发出与完成 ==")
status, body = call("POST", f"/shipments/{order_id}/accept", {"weight": 3.2, "courier_company": "顺丰速运"},
                    token=staff)
accepted = body.get("data", {}) if status == 200 else {}
check("驿站揽收成功", status == 200 and accepted.get("status") == "accepted", body.get("message"))
check("揽收按实重重算运费（3.2kg→14 元）", accepted.get("freight") == 14.0, accepted.get("freight"))
check("揽收写入轨迹", len(accepted.get("tracks", [])) == 2, len(accepted.get("tracks", [])))

status, body = call("POST", f"/shipments/{order_id}/accept", {"weight": 3.2}, token=staff)
check("重复揽收被拒绝", status == 409 and body["code"] == 30001, body.get("message"))

status, body = call("POST", f"/shipments/{order_id}/ship", token=staff)
check("登记发出成功", status == 200 and body["data"]["status"] == "shipped", body.get("message"))

status, body = call("POST", f"/shipments/{order_id}/complete", token=staff)
check("确认完成成功", status == 200 and body["data"]["status"] == "completed", body.get("message"))

status, body = call("POST", f"/shipments/{order_id}/complete", token=staff)
check("重复完成被拒绝", status == 409 and body["code"] == 30001, body.get("message"))

status, body = call("GET", f"/shipments/{order_id}/tracks", token=student)
check("轨迹节点完整（4 条）", status == 200 and len(body["data"]) == 4, len(body.get("data", [])))
check("轨迹含操作人", all(t.get("operator_name") for t in body["data"][1:]), body.get("data"))

status, body = call("POST", f"/shipments/{order_id}/cancel", token=student)
check("已完成订单不能取消", status == 409 and body["code"] == 30001, body.get("message"))

status, body = call("POST", f"/shipments/{order_id}/ship", token=student)
check("学生不能登记发出", status == 403, body.get("message"))

print("== 5. 取消订单 ==")
status, body = call("POST", "/shipments", {**payload, "item_name": "待取消物品"}, token=student)
cancel_id = body.get("data", {}).get("id")
status, body = call("POST", f"/shipments/{cancel_id}/cancel", token=student)
check("待揽收订单可取消", status == 200 and body["data"]["status"] == "cancelled", body.get("message"))
status, body = call("POST", f"/shipments/{cancel_id}/cancel", token=student)
check("已取消订单不能重复取消", status == 409, body.get("message"))

print("== 6. 通知中心 ==")
status, body = call("GET", "/notifications/unread-count", token=student)
check("未读数量接口可用", status == 200 and body["data"]["unread"] >= 3, body.get("data"))
unread_before = body["data"]["unread"]

status, body = call("GET", "/notifications?page=1&page_size=20", token=student)
items = body.get("data", {}).get("items", [])
check("通知列表返回数据", status == 200 and len(items) >= 3, len(items))
check("通知包含类型标签", all(i.get("type_label") for i in items), True)
first_id = items[0]["id"]

status, body = call("PATCH", f"/notifications/{first_id}/read", token=student)
check("标记单条已读", status == 200 and body["data"]["is_read"] == 1, body.get("message"))
status, body = call("GET", "/notifications/unread-count", token=student)
check("未读数减一", body["data"]["unread"] == unread_before - 1, body.get("data"))

status, body = call("GET", "/notifications?type=shipment", token=student)
check("按类型筛选通知", status == 200 and all(i["type"] == "shipment" for i in body["data"]["items"]),
      body.get("data", {}).get("total"))

status, body = call("POST", "/notifications/read-all", token=student)
check("全部标记已读", status == 200, body.get("message"))
status, body = call("GET", "/notifications/unread-count", token=student)
check("全部已读后未读为 0", body["data"]["unread"] == 0, body.get("data"))

status, body = call("GET", "/notifications", token=admin)
check("管理员通知与本人隔离", status == 200 and body["data"]["total"] == 0, body.get("data", {}).get("total"))

print("== 7. 公告 ==")
status, body = call("GET", "/announcements", token=student)
check("学生看到已发布公告", status == 200 and body["data"]["total"] >= 2, body.get("data", {}).get("total"))

status, body = call("POST", "/announcements", {"title": "测试公告", "content": "测试内容"}, token=admin)
ann_id = body.get("data", {}).get("id") if status == 201 else None
check("管理员发布公告", status == 201 and ann_id, body.get("message"))

status, body = call("POST", "/announcements", {"title": "越权公告", "content": "测试内容"}, token=student)
check("学生不能发布公告", status == 403, body.get("message"))

status, body = call("GET", "/announcements", token=student)
check("新公告出现在学生列表", status == 200 and any(a["id"] == ann_id for a in body["data"]["items"]), True)

status, body = call("PUT", f"/announcements/{ann_id}", {"title": "测试公告（改）", "content": "更新内容"}, token=admin)
check("修改公告成功", status == 200 and body["data"]["title"] == "测试公告（改）", body.get("message"))

status, body = call("DELETE", f"/announcements/{ann_id}", token=admin)
check("下架公告成功", status == 200 and body["data"]["status"] == 0, body.get("message"))

status, body = call("GET", "/announcements", token=student)
check("下架后学生列表不再显示", all(a["id"] != ann_id for a in body["data"]["items"]), True)

status, body = call("GET", "/announcements?include_offline=true", token=admin)
check("管理员可查看已下架公告", status == 200 and any(a["id"] == ann_id for a in body["data"]["items"]), True)

print("== 8. 统计报表 ==")
status, body = call("GET", "/stats/overview", token=staff)
ov = body.get("data", {})
check("总览接口返回包裹指标", status == 200 and ov.get("packages_total", 0) >= 7, ov)
check("总览包含寄件待揽收", "shipments_pending" in ov and ov["shipments_pending"] >= 1, ov.get("shipments_pending"))
check("总览返回占用率", 0 <= ov.get("occupancy", -1) <= 1, ov.get("occupancy"))

status, body = call("GET", "/stats/packages/trend?days=7", token=staff)
trend = body.get("data", {})
check("趋势返回 7 天数据", status == 200 and len(trend.get("items", [])) == 7, len(trend.get("items", [])))
check("趋势含入库与出库字段", all("inbound" in i and "picked" in i for i in trend.get("items", [])), True)

status, body = call("GET", "/stats/stations/workload", token=staff)
work = body.get("data", {}).get("items", [])
check("驿站工作量返回全部驿站", status == 200 and len(work) >= 2, len(work))
check("工作量含占用与在库", all({"in_stock", "overdue", "capacity", "used"} <= set(w) for w in work), True)

status, body = call("GET", "/stats/overdue", token=staff)
od = body.get("data", {})
check("超期分析返回列表", status == 200 and od.get("overdue", 0) >= 1, od.get("overdue"))
check("超期分布总数一致", sum(b["count"] for b in od.get("buckets", [])) == od.get("overdue"), od.get("buckets"))

status, body = call("GET", "/stats/overview", token=student)
check("学生不能看统计报表", status == 403, body.get("message"))
status, body = call("GET", "/stats/overview")
check("未登录访问统计被拒绝", status == 401, body.get("message"))

print("== 9. 入库/出库通知联动 ==")
tracking = f"TST4{stamp}01"
status, body = call("POST", "/packages", {
    "tracking_no": tracking, "station_id": 1, "recipient_phone": "13800000002",
    "courier_company": "顺丰速运", "weight": 1.0,
}, token=staff)
pkg = body.get("data", {})
code = pkg.get("pickup_code")
check("入库成功", status == 201 and code, body.get("message"))

status, body = call("GET", "/notifications?unread_only=true", token=student)
titles = [n["title"] for n in body["data"]["items"]]
check("入库生成到站通知", "包裹已到站" in titles, titles)

status, body = call("POST", f"/packages/{pkg['id']}/pickup",
                    {"pickup_code": code, "phone_suffix": "0002"}, token=staff)
check("出库成功", status == 200, body.get("message"))
status, body = call("GET", "/notifications?unread_only=true", token=student)
titles = [n["title"] for n in body["data"]["items"]]
check("出库生成取件成功通知", "取件成功" in titles, titles)

print()
print(f"结果：{passed} 通过，{failed} 失败")
print(f"测试数据：TST4{stamp} / 订单 id {order_id}")
raise SystemExit(1 if failed else 0)
