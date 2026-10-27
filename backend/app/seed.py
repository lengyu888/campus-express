"""初始化演示数据：python -m app.seed"""
from datetime import datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.announcement import Announcement
from app.models.notification import Notification
from app.models.package import Package
from app.models.pickup_record import PickupRecord
from app.models.shipment import ShipmentOrder, ShipmentTrack
from app.models.shelf import Shelf
from app.models.station import Station
from app.models.user import User

ACCOUNTS = [
    {
        "student_no": "admin",
        "name": "系统管理员",
        "phone": "13800000000",
        "password": "Admin@123",
        "role": "admin",
        "college": "信息中心",
    },
    {
        "student_no": "staff01",
        "name": "驿站值班员",
        "phone": "13800000001",
        "password": "Staff@123",
        "role": "staff",
        "college": "校园驿站",
    },
    {
        "student_no": "2023010101",
        "name": "张同学",
        "phone": "13800000002",
        "password": "Student@123",
        "role": "student",
        "college": "计算机学院",
    },
    {
        "student_no": "2023010102",
        "name": "李同学",
        "phone": "13800000003",
        "password": "Student@123",
        "role": "student",
        "college": "软件学院",
    },
]

STATIONS = [
    {
        "code": "ST-A",
        "name": "东区驿站",
        "address": "东区学生公寓 3 号楼一层",
        "phone": "13800001001",
        "open_time": time(8, 0),
        "close_time": time(21, 0),
        "manager_no": "staff01",
        "shelves": [
            {"code": "A-01", "zone": "A 区", "capacity": 30},
            {"code": "A-02", "zone": "A 区", "capacity": 30},
            {"code": "A-03", "zone": "B 区", "capacity": 24},
        ],
    },
    {
        "code": "ST-B",
        "name": "西区驿站",
        "address": "西区食堂南侧",
        "phone": "13800001002",
        "open_time": time(8, 30),
        "close_time": time(20, 30),
        "manager_no": None,
        "shelves": [
            {"code": "B-01", "zone": "A 区", "capacity": 20},
            {"code": "B-02", "zone": "A 区", "capacity": 20},
        ],
    },
]


DEMO_PACKAGES = [
    # station, shelf, tracking, phone, name, company, type, weight, code, days_ago, status
    ("ST-A", "A-01", "SF1234567890", "13800000002", "张同学", "顺丰速运", "normal", "1.20", "830215", 1, "in_stock"),
    ("ST-A", "A-01", "JD9876543210", "13800000003", "李同学", "京东物流", "fragile", "2.50", "417026", 5, "in_stock"),
    ("ST-A", "A-01", "YT6655443322", "13800000002", "张同学", "圆通速递", "normal", "0.80", "662318", 0, "in_stock"),
    ("ST-A", "A-01", "ZT7788990011", "13900001111", "王同学", "中通快递", "doc", "0.10", "205944", 1, "in_stock"),
    ("ST-A", "A-02", "STO1122334455", "13800000003", "李同学", "申通快递", "large", "6.30", None, 6, "picked"),
    ("ST-B", "B-01", "YD5566778899", "13800000002", "张同学", "韵达快递", "normal", "1.60", "318820", 2, "exception"),
    ("ST-B", "B-01", "EMS0099887766", "13800000003", "李同学", "EMS", "normal", "0.95", None, 4, "returned"),
]


def seed_users(db) -> list[str]:
    created = []
    for item in ACCOUNTS:
        exists = db.execute(
            select(User).where(User.phone == item["phone"])
        ).scalar_one_or_none()
        if exists:
            continue
        db.add(
            User(
                student_no=item["student_no"],
                name=item["name"],
                phone=item["phone"],
                password_hash=hash_password(item["password"]),
                role=item["role"],
                college=item["college"],
                status=1,
            )
        )
        created.append(item["student_no"])
    db.commit()
    return created


def seed_stations(db) -> list[str]:
    created = []
    for item in STATIONS:
        station = db.execute(
            select(Station).where(Station.code == item["code"])
        ).scalar_one_or_none()
        if station is None:
            manager = None
            if item["manager_no"]:
                manager = db.execute(
                    select(User).where(User.student_no == item["manager_no"])
                ).scalar_one_or_none()
            station = Station(
                code=item["code"],
                name=item["name"],
                address=item["address"],
                phone=item["phone"],
                open_time=item["open_time"],
                close_time=item["close_time"],
                capacity=0,
                manager_id=manager.id if manager else None,
                status=1,
            )
            db.add(station)
            db.flush()
            created.append(item["code"])

        for sh in item["shelves"]:
            exists = db.execute(
                select(Shelf).where(
                    Shelf.station_id == station.id, Shelf.code == sh["code"]
                )
            ).scalar_one_or_none()
            if exists:
                continue
            db.add(
                Shelf(
                    station_id=station.id,
                    code=sh["code"],
                    zone=sh["zone"],
                    capacity=sh["capacity"],
                    used_count=0,
                    status=1,
                )
            )
            db.flush()

        total = sum(
            s.capacity for s in db.execute(
                select(Shelf).where(Shelf.station_id == station.id)
            ).scalars().all()
        )
        station.capacity = total

    db.commit()
    return created


def seed_packages(db) -> int:
    """演示包裹。仅在 packages 为空时灌入，并按在库包裹重算货架占用。"""
    if db.scalar(select(func.count()).select_from(Package)):
        return 0

    operator = db.execute(
        select(User).where(User.student_no == "staff01")
    ).scalar_one_or_none()
    if operator is None:
        return 0

    now = datetime.now()
    created = 0
    for (station_code, shelf_code, tracking, phone, name, company,
         ptype, weight, code, days_ago, status) in DEMO_PACKAGES:
        station = db.execute(
            select(Station).where(Station.code == station_code)
        ).scalar_one_or_none()
        if station is None:
            continue
        shelf = db.execute(
            select(Shelf).where(Shelf.station_id == station.id, Shelf.code == shelf_code)
        ).scalar_one_or_none()

        recipient = db.execute(
            select(User).where(User.phone == phone)
        ).scalar_one_or_none()
        stored_at = now - timedelta(days=days_ago, hours=3)
        pkg = Package(
            tracking_no=tracking,
            station_id=station.id,
            shelf_id=shelf.id if shelf and status in ("in_stock", "overdue") else None,
            recipient_id=recipient.id if recipient else None,
            recipient_name=name,
            recipient_phone=phone,
            courier_company=company,
            package_type=ptype,
            weight=Decimal(weight),
            status="in_stock" if status in ("in_stock", "overdue") else status,
            pickup_code=code,
            code_expire_at=stored_at + timedelta(days=7) if code else None,
            stored_at=stored_at,
            overdue_days=max(0, days_ago - 3) if days_ago > 3 else 0,
            remark="登记异常：包装破损：待联系收件人" if status == "exception" else None,
            created_by=operator.id,
        )
        if status == "picked":
            pkg.picked_at = now - timedelta(days=2)
            pkg.pickup_code = None
            pkg.code_expire_at = None
        elif status == "returned":
            pkg.remark = "超期未取，已退回发件方"
        elif status == "exception":
            pkg.shelf_id = shelf.id if shelf else None

        db.add(pkg)
        db.flush()

        if status == "picked":
            db.add(
                PickupRecord(
                    package_id=pkg.id,
                    operator_id=operator.id,
                    pickup_code="513907",
                    phone_suffix=phone[-4:],
                    verify_type="code_phone",
                    picked_at=pkg.picked_at,
                )
            )
        created += 1

    db.flush()
    for shelf in db.execute(select(Shelf)).scalars().all():
        used = db.scalar(
            select(func.count()).select_from(Package).where(
                Package.shelf_id == shelf.id,
                Package.status.in_(("in_stock", "overdue", "exception")),
            )
        ) or 0
        shelf.used_count = int(used)

    db.commit()
    return created


DEMO_SHIPMENTS = [
    {
        "order_no": "S20261026100001", "sender": "13800000002", "station": "ST-A",
        "receiver_name": "王小明", "receiver_phone": "13900002222",
        "receiver_address": "北京市海淀区学院路 15 号 3 号楼 402",
        "item_name": "考研资料", "weight": "2.00", "freight": "10.00",
        "status": "pending", "courier": "顺丰速运", "days_ago": 0,
    },
    {
        "order_no": "S20261026100002", "sender": "13800000003", "station": "ST-A",
        "receiver_name": "赵敏", "receiver_phone": "13900003333",
        "receiver_address": "上海市杨浦区四平路 1239 号 6 号楼",
        "item_name": "平板电脑", "weight": "1.50", "freight": "10.00",
        "status": "accepted", "courier": "京东物流", "days_ago": 1,
    },
    {
        "order_no": "S20261026100003", "sender": "13800000002", "station": "ST-B",
        "receiver_name": "陈晨", "receiver_phone": "13900004444",
        "receiver_address": "广东省广州市天河区五山路 381 号",
        "item_name": "换季衣物", "weight": "3.20", "freight": "14.00",
        "status": "shipped", "courier": "圆通速递", "days_ago": 2,
    },
    {
        "order_no": "S20261026100004", "sender": "13800000003", "station": "ST-A",
        "receiver_name": "刘洋", "receiver_phone": "13900005555",
        "receiver_address": "四川省成都市武侯区一环路南一段 24 号",
        "item_name": "实习证明", "weight": "0.50", "freight": "8.00",
        "status": "completed", "courier": "EMS", "days_ago": 4,
    },
    {
        "order_no": "S20261026100005", "sender": "13800000002", "station": "ST-A",
        "receiver_name": "周舟", "receiver_phone": "13900006666",
        "receiver_address": "浙江省杭州市西湖区余杭塘路 866 号",
        "item_name": "耳机", "weight": "0.30", "freight": "8.00",
        "status": "cancelled", "courier": None, "days_ago": 3,
    },
]

DEMO_ANNOUNCEMENTS = [
    {
        "title": "东区驿站营业时间调整通知",
        "content": "自本周起，东区驿站营业时间调整为 08:00—21:00，周末照常开放。"
                   "取件高峰为 12:00—13:30 与 17:30—19:00，建议错峰取件。",
    },
    {
        "title": "超期包裹提醒",
        "content": "包裹入库满 3 天将标记为超期，满 7 天未取将退回发件方。"
                   "请及时查看「我的包裹」中的取件码，避免包裹被退回。",
    },
]


def seed_shipments(db) -> int:
    if db.scalar(select(func.count()).select_from(ShipmentOrder)):
        return 0

    operator = db.execute(
        select(User).where(User.student_no == "staff01")
    ).scalar_one_or_none()
    created = 0
    now = datetime.now()

    for item in DEMO_SHIPMENTS:
        sender = db.execute(
            select(User).where(User.phone == item["sender"])
        ).scalar_one_or_none()
        station = db.execute(
            select(Station).where(Station.code == item["station"])
        ).scalar_one_or_none()
        if sender is None or station is None:
            continue

        created_at = now - timedelta(days=item["days_ago"], hours=2)
        order = ShipmentOrder(
            order_no=item["order_no"],
            sender_id=sender.id,
            station_id=station.id,
            receiver_name=item["receiver_name"],
            receiver_phone=item["receiver_phone"],
            receiver_address=item["receiver_address"],
            courier_company=item["courier"],
            item_name=item["item_name"],
            weight=Decimal(item["weight"]),
            freight=Decimal(item["freight"]),
            status=item["status"],
            created_at=created_at,
            updated_at=created_at,
        )
        db.add(order)
        db.flush()

        nodes = [("订单已创建", "pending", f"预估运费 ¥{item['freight']}", created_at)]
        if item["status"] != "cancelled":
            nodes.append(
                ("驿站已揽收", "accepted",
                 f"实重 {item['weight']} kg，运费 ¥{item['freight']}", created_at + timedelta(hours=3))
            )
        if item["status"] in ("shipped", "completed"):
            nodes.append(
                ("包裹已发出", "shipped", f"{item['courier']} 已收件", created_at + timedelta(hours=20))
            )
        if item["status"] == "completed":
            nodes.append(
                ("已签收", "completed", "收件人已签收，订单完成", created_at + timedelta(days=2))
            )
        if item["status"] == "cancelled":
            nodes.append(
                ("订单已取消", "cancelled", "寄件人取消订单", created_at + timedelta(hours=1))
            )

        for node, status, desc, at in nodes:
            db.add(
                ShipmentTrack(
                    order_id=order.id,
                    node=node,
                    status=status,
                    description=desc,
                    operator_id=operator.id if status != "pending" else sender.id,
                    occurred_at=at,
                )
            )
        created += 1

    db.commit()
    return created


def seed_announcements(db) -> int:
    if db.scalar(select(func.count()).select_from(Announcement)):
        return 0
    admin = db.execute(select(User).where(User.student_no == "admin")).scalar_one_or_none()
    if admin is None:
        return 0

    now = datetime.now()
    for index, item in enumerate(DEMO_ANNOUNCEMENTS):
        db.add(
            Announcement(
                title=item["title"],
                content=item["content"],
                publisher_id=admin.id,
                status=1,
                publish_at=now - timedelta(days=index),
            )
        )
    db.commit()
    return len(DEMO_ANNOUNCEMENTS)


def seed_notifications(db) -> int:
    student = db.execute(
        select(User).where(User.phone == "13800000002")
    ).scalar_one_or_none()
    other = db.execute(
        select(User).where(User.phone == "13800000003")
    ).scalar_one_or_none()
    if student is None:
        return 0

    staff = db.execute(
        select(User).where(User.student_no == "staff01")
    ).scalar_one_or_none()

    now = datetime.now()
    rows = [
        (student.id, "pickup", "包裹已到站",
         "东区驿站已收到您的顺丰速运包裹 SF1234567890，取件码 830215，请 7 天内领取。", now - timedelta(hours=2)),
        (student.id, "overdue", "包裹超期提醒",
         "包裹 YD5566778899 已入库 2 天，请尽快到西区驿站领取。", now - timedelta(hours=9)),
        (student.id, "system", "东区驿站营业时间调整",
         "自本周起，东区驿站营业时间调整为 08:00—21:00，周末照常开放。", now - timedelta(days=1)),
    ]
    if other is not None:
        rows.append(
            (other.id, "shipment", "包裹已揽收",
             "订单 S20261026100002 已在东区驿站揽收，实重 1.5 kg，运费 ¥10.00。",
             now - timedelta(days=1))
        )
    if staff is not None:
        rows.extend([
            (staff.id, "shipment", "新的寄件订单待揽收",
             "有学生提交了寄件订单，请到「寄件处理」完成揽收与称重。", now - timedelta(minutes=40)),
            (staff.id, "overdue", "超期包裹待处理",
             "东区驿站有包裹入库超过 3 天仍未取件，请及时通知收件人。", now - timedelta(hours=5)),
        ])

    created = 0
    for user_id, type_, title, content, at in rows:
        exists = db.scalar(
            select(Notification.id).where(
                Notification.user_id == user_id, Notification.title == title
            )
        )
        if exists:
            continue
        db.add(
            Notification(
                user_id=user_id, type=type_, title=title, content=content,
                channel="inapp", is_read=0, sent_at=at, created_at=at,
            )
        )
        created += 1
    db.commit()
    return created


def main():
    db = SessionLocal()
    try:
        users = seed_users(db)
        stations = seed_stations(db)
        packages = seed_packages(db)
        shipments = seed_shipments(db)
        announcements = seed_announcements(db)
        notifications = seed_notifications(db)
    finally:
        db.close()

    if users:
        print(f"seed 完成，新增账号：{', '.join(users)}")
    else:
        print("seed 完成，演示账号已存在")
    if stations:
        print(f"seed 完成，新增驿站：{', '.join(stations)}")
    else:
        print("seed 完成，驿站数据已存在")
    if packages:
        print(f"seed 完成，新增演示包裹 {packages} 件")
    else:
        print("seed 完成，包裹数据已存在")
    if shipments:
        print(f"seed 完成，新增演示寄件订单 {shipments} 单")
    else:
        print("seed 完成，寄件订单已存在")
    if announcements:
        print(f"seed 完成，新增公告 {announcements} 条")
    else:
        print("seed 完成，公告已存在")
    if notifications:
        print(f"seed 完成，新增站内通知 {notifications} 条")
    else:
        print("seed 完成，通知已存在")
    print("管理员 admin / Admin@123")
    print("工作人员 staff01 / Staff@123")
    print("学生 2023010101 / Student@123")


if __name__ == "__main__":
    main()
