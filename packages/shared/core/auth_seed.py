import hashlib
import logging
import os
import uuid
from datetime import UTC, datetime

from sqlmodel import Session, select

from contracts.auth_models import AuthProvider, AuthProviderName, User, UserStatus
from core.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_USER_ID = uuid.uuid5(uuid.NAMESPACE_URL, 'data-forge-default-user').hex
_DEFAULT_USER_MARKER = 'env_default_user'
_PASSWORD_PROVIDER = AuthProviderName.PASSWORD
_PBKDF2_ALG = 'sha256'
_PBKDF2_ITERATIONS = 200_000


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _normalize_name(value: str, email: str) -> str:
    name = value.strip()
    if name:
        return name
    return email.split('@', 1)[0]


def _provider_metadata(password: str) -> dict[str, str]:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(_PBKDF2_ALG, password.encode('utf-8'), salt, _PBKDF2_ITERATIONS)
    hashed = f'pbkdf2_{_PBKDF2_ALG}${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}'
    return {'managed_by': _DEFAULT_USER_MARKER, 'password_hash': hashed}


def _user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def ensure_default_user(session: Session) -> User:
    email = _normalize_email(settings.default_user_email)
    name = _normalize_name(settings.default_user_name, email)
    now = _utcnow()
    user = session.get(User, _DEFAULT_USER_ID)
    if user is None:
        owner = _user_by_email(session, email)
        user_email = email if owner is None else f'{_DEFAULT_USER_ID}@default.local'
        if owner is not None:
            logger.warning('Default user email %s is already in use; using fallback email %s', email, user_email)
        user = User(
            id=_DEFAULT_USER_ID,
            email=user_email,
            display_name=name,
            status=UserStatus.ACTIVE,
            email_verified=True,
            has_password=True,
            preferences={},
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        session.add(
            AuthProvider(
                id=uuid.uuid4().hex,
                user_id=user.id,
                provider=_PASSWORD_PROVIDER,
                provider_subject=user.email,
                provider_metadata=_provider_metadata(settings.default_user_password),
                created_at=now,
            )
        )
        session.commit()
        return user
    user.display_name = name
    user.status = UserStatus.ACTIVE
    user.email_verified = True
    user.has_password = True
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
