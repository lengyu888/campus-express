"""初始化演示数据：python -m app.seed"""
from datetime import datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.package import Package
from app.models.pickup_record import PickupRecord
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


def main():
    db = SessionLocal()
    try:
        users = seed_users(db)
        stations = seed_stations(db)
        packages = seed_packages(db)
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
    print("管理员 admin / Admin@123")
    print("工作人员 staff01 / Staff@123")
    print("学生 2023010101 / Student@123")


if __name__ == "__main__":
    main()
