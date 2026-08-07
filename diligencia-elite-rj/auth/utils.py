import os
import secrets
import hashlib
import jwt
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from email_validator import validate_email, EmailNotValidError

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    USE_ARGON2 = True
except ImportError:
    USE_ARGON2 = False
    import bcrypt

from models import db, User, Session, AuditLog, LoginLog


JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRY = 15
REFRESH_TOKEN_EXPIRY = 7


def hash_password(password: str) -> str:
    if USE_ARGON2:
        ph = PasswordHasher()
        return ph.hash(password)
    else:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    if USE_ARGON2:
        ph = PasswordHasher()
        try:
            ph.verify(password_hash, password)
            return True
        except VerifyMismatchError:
            return False
    else:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_jwt(user_id: int, expiry_minutes: int = ACCESS_TOKEN_EXPIRY) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(minutes=expiry_minutes),
        'iat': datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def get_client_ip() -> str:
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'


def get_user_agent() -> str:
    return request.headers.get('User-Agent', '')[:512]


def validate_email_format(email: str) -> bool:
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, 'Senha deve ter pelo menos 8 caracteres'
    if not any(c.isupper() for c in password):
        return False, 'Senha deve conter pelo menos uma letra maiúscula'
    if not any(c.islower() for c in password):
        return False, 'Senha deve conter pelo menos uma letra minúscula'
    if not any(c.isdigit() for c in password):
        return False, 'Senha deve conter pelo menos um número'
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False, 'Senha deve conter pelo menos um caractere especial'
    return True, 'Senha válida'


def rate_limit_check(email: str, max_attempts: int = 5, window_minutes: int = 15) -> tuple[bool, str]:
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    recent_failures = LoginLog.query.filter(
        LoginLog.email == email,
        LoginLog.success == False,
        LoginLog.attempted_at >= cutoff
    ).count()

    if recent_failures >= max_attempts:
        return False, f'Muitas tentativas de login. Tente novamente em {window_minutes} minutos.'

    return True, ''


def reset_rate_limit(email: str):
    cutoff = datetime.utcnow() - timedelta(minutes=1)
    LoginLog.query.filter(
        LoginLog.email == email,
        LoginLog.success == False,
        LoginLog.attempted_at >= cutoff
    ).delete()
    db.session.commit()


def audit_log(action: str, resource: str = '', details: dict = None, user_id: int = None):
    if details is None:
        details = {}

    log = AuditLog(
        user_id=user_id or (g.user.id if hasattr(g, 'user') and g.user else None),
        action=action,
        resource=resource,
        details=details,
        ip_address=get_client_ip()
    )
    db.session.add(log)
    db.session.commit()


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing authorization token'}), 401

        token = auth_header.replace('Bearer ', '', 1)

        try:
            payload = verify_jwt(token)
            user = User.query.get(payload['user_id'])

            if not user or not user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401

            g.user = user
        except ValueError as e:
            return jsonify({'error': str(e)}), 401

        return f(*args, **kwargs)

    return decorated_function


def require_role(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'user') or not g.user:
                return jsonify({'error': 'Authentication required'}), 401

            if g.user.role.name not in allowed_roles:
                audit_log('UNAUTHORIZED_ACCESS', resource=request.path, details={'reason': 'insufficient_role'})
                return jsonify({'error': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_json(*required_fields):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400

            data = request.get_json() or {}

            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            return f(*args, **kwargs)

        return decorated_function

    return decorator
