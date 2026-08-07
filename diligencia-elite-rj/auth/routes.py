from flask import request, jsonify, g
from datetime import datetime, timedelta
from . import auth_bp
from .utils import (
    hash_password, verify_password, generate_jwt, verify_jwt, generate_refresh_token,
    hash_token, generate_reset_token, get_client_ip, get_user_agent,
    validate_email_format, validate_password_strength, rate_limit_check, reset_rate_limit,
    require_auth, require_json, audit_log, require_role
)
from models import db, User, Session, LoginLog, Role


@auth_bp.route('/register', methods=['POST'])
@require_json('name', 'surname', 'email', 'username', 'password', 'confirm_password')
def register():
    data = request.get_json()

    if not validate_email_format(data['email']):
        return jsonify({'error': 'Email inválido'}), 400

    if data['password'] != data['confirm_password']:
        return jsonify({'error': 'Senhas não correspondem'}), 400

    is_valid, message = validate_password_strength(data['password'])
    if not is_valid:
        return jsonify({'error': message}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email já registrado'}), 409

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Nome de usuário já existe'}), 409

    default_role = Role.query.filter_by(name='user').first()
    if not default_role:
        return jsonify({'error': 'Role padrão não encontrada'}), 500

    user = User(
        email=data['email'],
        username=data['username'],
        password_hash=hash_password(data['password']),
        first_name=data['name'],
        last_name=data['surname'],
        phone=data.get('phone', ''),
        role_id=default_role.id,
        is_active=True
    )

    db.session.add(user)
    db.session.commit()

    audit_log('USER_REGISTERED', resource=f'user:{user.id}', details={'email': user.email})

    return jsonify({
        'message': 'Cadastro realizado com sucesso',
        'user_id': user.id,
        'email': user.email
    }), 201


@auth_bp.route('/login', methods=['POST'])
@require_json('email', 'password')
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    can_attempt, rate_limit_message = rate_limit_check(email)
    if not can_attempt:
        return jsonify({'error': rate_limit_message}), 429

    user = User.query.filter_by(email=email).first()

    if not user or not verify_password(password, user.password_hash):
        log = LoginLog(
            email=email,
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
            success=False,
            failure_reason='invalid_credentials'
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({'error': 'Email ou senha incorretos'}), 401

    if not user.is_active:
        log = LoginLog(
            user_id=user.id,
            email=email,
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
            success=False,
            failure_reason='user_inactive'
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({'error': 'Usuário inativo'}), 403

    access_token = generate_jwt(user.id)
    refresh_token = generate_refresh_token()

    session = Session(
        user_id=user.id,
        token_hash=hash_token(access_token),
        refresh_token_hash=hash_token(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False
    )

    user.last_login = datetime.utcnow()
    db.session.add(session)
    db.session.commit()

    reset_rate_limit(email)

    login_log = LoginLog(
        user_id=user.id,
        email=email,
        ip_address=get_client_ip(),
        user_agent=get_user_agent(),
        success=True
    )
    db.session.add(login_log)
    db.session.commit()

    audit_log('USER_LOGIN', resource=f'user:{user.id}')

    response = jsonify({
        'access_token': access_token,
        'user': user.to_dict(include_email=True)
    })
    response.set_cookie(
        'refresh_token',
        refresh_token,
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        secure=True,
        samesite='Lax'
    )
    return response, 200


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    user = g.user
    Session.query.filter_by(user_id=user.id).update({'revoked': True})
    db.session.commit()

    audit_log('USER_LOGOUT', resource=f'user:{user.id}')

    response = jsonify({'message': 'Logout realizado com sucesso'})
    response.delete_cookie('refresh_token')
    return response, 200


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    refresh_token = request.cookies.get('refresh_token')

    if not refresh_token:
        return jsonify({'error': 'Refresh token não encontrado'}), 401

    from datetime import datetime
    session = Session.query.filter(
        Session.refresh_token_hash == hash_token(refresh_token),
        Session.revoked == False,
        Session.expires_at > datetime.utcnow()
    ).first()

    if not session:
        return jsonify({'error': 'Refresh token inválido ou expirado'}), 401

    user = User.query.get(session.user_id)
    if not user or not user.is_active:
        return jsonify({'error': 'Usuário não encontrado ou inativo'}), 401

    access_token = generate_jwt(user.id)

    session.token_hash = hash_token(access_token)
    db.session.commit()

    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/forgot-password', methods=['POST'])
@require_json('email')
def forgot_password():
    data = request.get_json()
    email = data['email']

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'message': 'Se o email existe, um link de recuperação foi enviado'}), 200

    reset_token = generate_reset_token()
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()

    audit_log('PASSWORD_RESET_REQUESTED', resource=f'user:{user.id}')

    return jsonify({
        'message': 'Link de recuperação enviado para o email',
        'reset_token': reset_token
    }), 200


@auth_bp.route('/reset-password', methods=['POST'])
@require_json('token', 'new_password', 'confirm_password')
def reset_password():
    data = request.get_json()

    if data['new_password'] != data['confirm_password']:
        return jsonify({'error': 'Senhas não correspondem'}), 400

    is_valid, message = validate_password_strength(data['new_password'])
    if not is_valid:
        return jsonify({'error': message}), 400

    user = User.query.filter_by(password_reset_token=data['token']).first()

    if not user or not user.password_reset_expires or user.password_reset_expires < datetime.utcnow():
        return jsonify({'error': 'Token inválido ou expirado'}), 400

    user.password_hash = hash_password(data['new_password'])
    user.password_reset_token = ''
    user.password_reset_expires = None
    db.session.commit()

    audit_log('PASSWORD_RESET', resource=f'user:{user.id}')

    return jsonify({'message': 'Senha redefinida com sucesso'}), 200


@auth_bp.route('/change-password', methods=['POST'])
@require_auth
@require_json('current_password', 'new_password', 'confirm_password')
def change_password():
    user = g.user
    data = request.get_json()

    if not verify_password(data['current_password'], user.password_hash):
        return jsonify({'error': 'Senha atual incorreta'}), 401

    if data['new_password'] != data['confirm_password']:
        return jsonify({'error': 'Senhas não correspondem'}), 400

    is_valid, message = validate_password_strength(data['new_password'])
    if not is_valid:
        return jsonify({'error': message}), 400

    user.password_hash = hash_password(data['new_password'])
    Session.query.filter_by(user_id=user.id).update({'revoked': True})
    db.session.commit()

    audit_log('PASSWORD_CHANGED', resource=f'user:{user.id}')

    response = jsonify({'message': 'Senha alterada com sucesso. Faça login novamente.'})
    response.delete_cookie('refresh_token')
    return response, 200
