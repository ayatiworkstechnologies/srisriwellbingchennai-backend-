from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AdminUser
from ..legacy import is_active_flag
from ..security import decode_access_token

security = HTTPBearer()


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> AdminUser:
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    admin = db.query(AdminUser).filter(AdminUser.email == payload.get("sub")).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin user not found")
    if not is_active_flag(admin.is_active):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    return admin


def require_roles(*allowed_roles: str):
    def dependency(current_admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
        if current_admin.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this action")
        return current_admin

    return dependency


def get_current_super_admin(
    current_admin: AdminUser = Depends(require_roles("super_admin")),
) -> AdminUser:
    return current_admin
