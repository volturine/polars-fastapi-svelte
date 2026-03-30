from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from core.database import get_settings_db
from core.exceptions import EmailAlreadyExistsError, InvalidCredentialsError, ProviderUnlinkError
from main import app
from modules.auth.models import AuthProvider, UserSession
from modules.auth.service import (
    change_password,
    create_session,
    create_user,
    find_or_create_oauth_user,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    revoke_all_sessions,
    revoke_session,
    unlink_provider,
    update_profile,
    validate_password,
    validate_session,
    verify_password,
)


@pytest.fixture(autouse=True, scope='function')
def patch_auth_service_datetime(monkeypatch):
    class _DateTime:
        @staticmethod
        def now(_tz=None):
            return datetime.now()

    monkeypatch.setattr('modules.auth.service.datetime', _DateTime)


@pytest.fixture(scope='function')
def auth_engine():
    engine = create_engine(
        'sqlite:///:memory:',
        echo=False,
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(scope='function')
def auth_db_session(auth_engine):
    with Session(auth_engine) as session:
        yield session


@pytest.fixture(scope='function')
def auth_client(auth_db_session: Session):
    def override_get_settings_db():
        yield auth_db_session

    if hasattr(app.state, 'mcp_registry'):
        del app.state.mcp_registry
    app.dependency_overrides[get_settings_db] = override_get_settings_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


class TestPasswordHashing:
    def test_hash_and_verify_correct_password(self) -> None:
        password = 'strongpassword123'

        hashed = hash_password(password)

        assert hashed.startswith('pbkdf2_sha256$')
        assert verify_password(password, hashed) is True

    def test_hash_and_verify_wrong_password(self) -> None:
        hashed = hash_password('strongpassword123')

        assert verify_password('wrongpassword123', hashed) is False

    def test_verify_malformed_hash(self) -> None:
        assert verify_password('strongpassword123', 'badhash') is False
        assert verify_password('strongpassword123', 'pbkdf2_sha256$abc$00$11') is False
        assert verify_password('strongpassword123', 'pbkdf2_sha256$200000$0$11') is False

    def test_validate_password_valid(self) -> None:
        validate_password('strong123')

    def test_validate_password_too_short(self) -> None:
        with pytest.raises(ValueError, match='at least 8'):
            validate_password('short')


class TestUserService:
    def test_create_user_success(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')

        assert user.email == 'test@example.com'
        assert user.display_name == 'Test User'
        assert user.has_password is True

        provider = auth_db_session.exec(
            select(AuthProvider).where(AuthProvider.user_id == user.id, AuthProvider.provider == 'password')
        ).first()
        assert provider is not None
        assert provider.provider_subject == 'test@example.com'
        assert isinstance(provider.provider_metadata, dict)
        assert 'password_hash' in provider.provider_metadata

    def test_create_user_duplicate_email(self, auth_db_session: Session) -> None:
        create_user(auth_db_session, 'test@example.com', 'password123', 'User One')

        with pytest.raises(EmailAlreadyExistsError):
            create_user(auth_db_session, 'test@example.com', 'password123', 'User Two')

    def test_get_user_by_email(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')

        found = get_user_by_email(auth_db_session, 'TEST@EXAMPLE.COM')

        assert found is not None
        assert found.id == user.id

    def test_get_user_by_email_not_found(self, auth_db_session: Session) -> None:
        found = get_user_by_email(auth_db_session, 'missing@example.com')

        assert found is None

    def test_get_user_by_id(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')

        found = get_user_by_id(auth_db_session, user.id)

        assert found is not None
        assert found.email == 'test@example.com'

    def test_update_profile(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')

        updated = update_profile(
            auth_db_session,
            user_id=user.id,
            display_name='Updated Name',
            avatar_url=None,
            preferences=None,
        )

        assert updated.display_name == 'Updated Name'

    def test_change_password(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')

        change_password(auth_db_session, user.id, 'password123', 'newpassword123')

        provider = auth_db_session.exec(
            select(AuthProvider).where(AuthProvider.user_id == user.id, AuthProvider.provider == 'password')
        ).first()
        assert provider is not None
        assert isinstance(provider.provider_metadata, dict)
        hashed = provider.provider_metadata.get('password_hash')
        assert isinstance(hashed, str)
        assert verify_password('newpassword123', hashed) is True
        assert verify_password('password123', hashed) is False

    def test_change_password_wrong_current(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')

        with pytest.raises(InvalidCredentialsError):
            change_password(auth_db_session, user.id, 'wrongpassword', 'newpassword123')


class TestSessionService:
    def test_create_session(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')

        user_session = create_session(auth_db_session, user.id, 'pytest-agent', '127.0.0.1')

        assert user_session.user_id == user.id
        assert user_session.revoked is False
        assert user_session.expires_at > datetime.now()

    def test_validate_session_valid(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')
        user_session = create_session(auth_db_session, user.id, None, None)

        resolved = validate_session(auth_db_session, user_session.id)

        assert resolved is not None
        assert resolved.id == user.id
        assert resolved.last_login_at is not None

    def test_validate_session_expired(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')
        now = datetime.now()
        user_session = UserSession(
            user_id=user.id,
            device_info=None,
            ip_address=None,
            created_at=now - timedelta(days=3),
            expires_at=now - timedelta(minutes=1),
            revoked=False,
        )
        auth_db_session.add(user_session)
        auth_db_session.commit()
        auth_db_session.refresh(user_session)

        resolved = validate_session(auth_db_session, user_session.id)

        assert resolved is None
        refreshed = auth_db_session.get(UserSession, user_session.id)
        assert refreshed is not None
        assert refreshed.revoked is True

    def test_validate_session_revoked(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')
        now = datetime.now()
        user_session = UserSession(
            user_id=user.id,
            device_info=None,
            ip_address=None,
            created_at=now,
            expires_at=now + timedelta(days=1),
            revoked=True,
        )
        auth_db_session.add(user_session)
        auth_db_session.commit()
        auth_db_session.refresh(user_session)

        resolved = validate_session(auth_db_session, user_session.id)

        assert resolved is None

    def test_revoke_session(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')
        user_session = create_session(auth_db_session, user.id, None, None)

        revoke_session(auth_db_session, user_session.id)

        refreshed = auth_db_session.get(UserSession, user_session.id)
        assert refreshed is not None
        assert refreshed.revoked is True

    def test_revoke_all_sessions(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'test@example.com', 'password123', 'Test User')
        first = create_session(auth_db_session, user.id, None, None)
        second = create_session(auth_db_session, user.id, None, None)

        revoke_all_sessions(auth_db_session, user.id)

        refreshed_first = auth_db_session.get(UserSession, first.id)
        refreshed_second = auth_db_session.get(UserSession, second.id)
        assert refreshed_first is not None
        assert refreshed_second is not None
        assert refreshed_first.revoked is True
        assert refreshed_second.revoked is True


class TestOAuthService:
    def test_find_or_create_oauth_user_new(self, auth_db_session: Session) -> None:
        user = find_or_create_oauth_user(
            session=auth_db_session,
            provider='google',
            provider_subject='google-subject-1',
            email='oauth@example.com',
            display_name='OAuth User',
            avatar_url='https://example.com/avatar.png',
        )

        assert user.email == 'oauth@example.com'
        assert user.has_password is False
        provider = auth_db_session.exec(
            select(AuthProvider).where(AuthProvider.user_id == user.id, AuthProvider.provider == 'google')
        ).first()
        assert provider is not None

    def test_find_or_create_oauth_user_existing_provider(self, auth_db_session: Session) -> None:
        user = find_or_create_oauth_user(
            session=auth_db_session,
            provider='github',
            provider_subject='github-subject-1',
            email='oauth@example.com',
            display_name='OAuth User',
            avatar_url=None,
        )

        resolved = find_or_create_oauth_user(
            session=auth_db_session,
            provider='github',
            provider_subject='github-subject-1',
            email='oauth-changed@example.com',
            display_name='Changed Name',
            avatar_url='https://example.com/new-avatar.png',
        )

        assert resolved.id == user.id
        providers = auth_db_session.exec(select(AuthProvider).where(AuthProvider.user_id == user.id)).all()
        assert len(providers) == 1

    def test_find_or_create_oauth_user_existing_email(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'existing@example.com', 'password123', 'Existing User')

        resolved = find_or_create_oauth_user(
            session=auth_db_session,
            provider='google',
            provider_subject='google-subject-2',
            email='existing@example.com',
            display_name='OAuth Existing',
            avatar_url='https://example.com/avatar.png',
        )

        assert resolved.id == user.id
        providers = auth_db_session.exec(select(AuthProvider).where(AuthProvider.user_id == user.id)).all()
        names = {item.provider for item in providers}
        assert names == {'password', 'google'}

    def test_unlink_provider_success(self, auth_db_session: Session) -> None:
        user = create_user(auth_db_session, 'existing@example.com', 'password123', 'Existing User')
        find_or_create_oauth_user(
            session=auth_db_session,
            provider='google',
            provider_subject='google-subject-3',
            email='existing@example.com',
            display_name='OAuth Existing',
            avatar_url=None,
        )

        unlink_provider(auth_db_session, user.id, 'google')

        providers = auth_db_session.exec(select(AuthProvider).where(AuthProvider.user_id == user.id)).all()
        names = {item.provider for item in providers}
        assert names == {'password'}

    def test_unlink_provider_last(self, auth_db_session: Session) -> None:
        user = find_or_create_oauth_user(
            session=auth_db_session,
            provider='google',
            provider_subject='google-subject-4',
            email='oauth-last@example.com',
            display_name='OAuth Last',
            avatar_url=None,
        )

        with pytest.raises(ProviderUnlinkError):
            unlink_provider(auth_db_session, user.id, 'google')


class TestAuthRoutes:
    def test_register_success(self, auth_client: TestClient) -> None:
        response = auth_client.post(
            '/api/v1/auth/register',
            json={
                'email': 'register@example.com',
                'password': 'password123',
                'display_name': 'Register User',
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body['email'] == 'register@example.com'
        assert body['display_name'] == 'Register User'
        assert 'password' in body['providers']
        assert 'session_token' in response.cookies

    def test_register_duplicate_email(self, auth_client: TestClient) -> None:
        payload = {
            'email': 'duplicate@example.com',
            'password': 'password123',
            'display_name': 'User One',
        }
        first = auth_client.post('/api/v1/auth/register', json=payload)
        second = auth_client.post('/api/v1/auth/register', json=payload)

        assert first.status_code == 200
        assert second.status_code == 409

    def test_register_weak_password(self, auth_client: TestClient) -> None:
        response = auth_client.post(
            '/api/v1/auth/register',
            json={
                'email': 'weak@example.com',
                'password': 'short',
                'display_name': 'Weak User',
            },
        )

        assert response.status_code == 400

    def test_login_success(self, auth_client: TestClient) -> None:
        auth_client.post(
            '/api/v1/auth/register',
            json={
                'email': 'login@example.com',
                'password': 'password123',
                'display_name': 'Login User',
            },
        )

        response = auth_client.post('/api/v1/auth/login', json={'email': 'login@example.com', 'password': 'password123'})

        assert response.status_code == 200
        assert response.json()['email'] == 'login@example.com'
        assert 'session_token' in response.cookies

    def test_login_wrong_password(self, auth_client: TestClient) -> None:
        auth_client.post(
            '/api/v1/auth/register',
            json={
                'email': 'wrongpass@example.com',
                'password': 'password123',
                'display_name': 'Wrong Pass User',
            },
        )

        response = auth_client.post('/api/v1/auth/login', json={'email': 'wrongpass@example.com', 'password': 'wrongpassword'})

        assert response.status_code == 401

    def test_login_nonexistent_email(self, auth_client: TestClient) -> None:
        response = auth_client.post('/api/v1/auth/login', json={'email': 'missing@example.com', 'password': 'password123'})

        assert response.status_code == 401

    def test_me_authenticated(self, auth_client: TestClient) -> None:
        auth_client.post(
            '/api/v1/auth/register',
            json={
                'email': 'me@example.com',
                'password': 'password123',
                'display_name': 'Me User',
            },
        )

        response = auth_client.get('/api/v1/auth/me')

        assert response.status_code == 200
        assert response.json()['email'] == 'me@example.com'

    def test_me_unauthenticated(self, auth_client: TestClient) -> None:
        response = auth_client.get('/api/v1/auth/me')

        assert response.status_code == 401

    def test_logout(self, auth_client: TestClient) -> None:
        auth_client.post(
            '/api/v1/auth/register',
            json={
                'email': 'logout@example.com',
                'password': 'password123',
                'display_name': 'Logout User',
            },
        )

        response = auth_client.post('/api/v1/auth/logout')

        assert response.status_code == 200
        assert response.json()['success'] is True
        set_cookie = response.headers.get('set-cookie', '')
        assert 'session_token=' in set_cookie
        assert 'Max-Age=0' in set_cookie

    def test_update_profile_authenticated(self, auth_client: TestClient) -> None:
        auth_client.post(
            '/api/v1/auth/register',
            json={
                'email': 'profile@example.com',
                'password': 'password123',
                'display_name': 'Profile User',
            },
        )

        response = auth_client.put(
            '/api/v1/auth/profile',
            json={'display_name': 'Updated Profile User'},
        )

        assert response.status_code == 200
        assert response.json()['display_name'] == 'Updated Profile User'

    def test_change_password_authenticated(self, auth_client: TestClient) -> None:
        auth_client.post(
            '/api/v1/auth/register',
            json={
                'email': 'changepass@example.com',
                'password': 'password123',
                'display_name': 'Change Password User',
            },
        )

        response = auth_client.put(
            '/api/v1/auth/password',
            json={'current_password': 'password123', 'new_password': 'newpassword123'},
        )

        assert response.status_code == 200
        assert response.json()['success'] is True

        auth_client.post('/api/v1/auth/logout')
        login = auth_client.post('/api/v1/auth/login', json={'email': 'changepass@example.com', 'password': 'newpassword123'})
        assert login.status_code == 200
