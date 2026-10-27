def mask_phone(phone: str) -> str:
    if len(phone) == 11:
        return f"{phone[:3]}****{phone[-4:]}"
    return phone


def serialize_user(user, mask: bool = True) -> dict:
    return {
        "id": user.id,
        "student_no": user.student_no,
        "name": user.name,
        "phone": mask_phone(user.phone) if mask else user.phone,
        "role": user.role,
        "college": user.college,
        "status": user.status,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
