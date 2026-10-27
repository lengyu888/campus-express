"""初始化演示数据：python -m app.seed"""
from datetime import time

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
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


def main():
    db = SessionLocal()
    try:
        users = seed_users(db)
        stations = seed_stations(db)
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
    print("管理员 admin / Admin@123")
    print("工作人员 staff01 / Staff@123")
    print("学生 2023010101 / Student@123")


if __name__ == "__main__":
    main()
