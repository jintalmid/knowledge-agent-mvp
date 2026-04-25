from pydantic import BaseModel


class CurrentUser(BaseModel):
    owner_user_id: str = "demo_user"
    department_id: str = "demo_department"
    security_level: str = "normal"


def get_current_user() -> CurrentUser:
    return CurrentUser()
