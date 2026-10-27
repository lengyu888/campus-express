"""初始化演示账号：python -m app.seed"""
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
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


def main():
    db = SessionLocal()
    created = []
    try:
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
    finally:
        db.close()

    if created:
        print(f"seed 完成，新增账号：{', '.join(created)}")
    else:
        print("seed 完成，演示账号已存在，无需重复创建")
    print("管理员 admin / Admin@123")
    print("工作人员 staff01 / Staff@123")
    print("学生 2023010101 / Student@123")


if __name__ == "__main__":
    main()
