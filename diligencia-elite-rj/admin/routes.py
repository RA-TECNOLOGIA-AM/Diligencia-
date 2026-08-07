from flask import request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from . import admin_bp
from auth.utils import require_auth, require_role, require_json, hash_password, audit_log
from models import db, User, Role, LoginLog, AuditLog


@admin_bp.route('/dashboard', methods=['GET'])
@require_auth
@require_role('admin')
def dashboard():
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_logins = LoginLog.query.filter(
        LoginLog.success == True,
        LoginLog.attempted_at >= today_start
    ).count()

    today_failed = LoginLog.query.filter(
        LoginLog.success == False,
        LoginLog.attempted_at >= today_start
    ).count()

    recent_activity = AuditLog.query.order_by(desc(AuditLog.created_at)).limit(10).all()

    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'today_logins': today_logins,
        'failed_logins': today_failed,
        'recent_activity': [log.to_dict() for log in recent_activity]
    }), 200


@admin_bp.route('/users', methods=['GET'])
@require_auth
@require_role('admin')
def list_users():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    if page < 1 or limit < 1 or limit > 100:
        return jsonify({'error': 'Parâmetros de paginação inválidos'}), 400

    query = User.query.order_by(desc(User.created_at))
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'users': [user.to_dict(include_email=True) for user in pagination.items]
    }), 200


@admin_bp.route('/users', methods=['POST'])
@require_auth
@require_role('admin')
@require_json('email', 'username', 'password', 'first_name', 'last_name')
def create_user():
    data = request.get_json()

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email já registrado'}), 409

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username já existe'}), 409

    role_name = data.get('role', 'user')
    role = Role.query.filter_by(name=role_name).first()

    if not role:
        return jsonify({'error': f'Role "{role_name}" não encontrada'}), 400

    user = User(
        email=data['email'],
        username=data['username'],
        password_hash=hash_password(data['password']),
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone=data.get('phone', ''),
        role_id=role.id,
        is_active=True
    )

    db.session.add(user)
    db.session.commit()

    audit_log('USER_CREATED_BY_ADMIN', resource=f'user:{user.id}', details={'email': user.email})

    return jsonify(user.to_dict(include_email=True)), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_auth
@require_role('admin')
def update_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = request.get_json()

    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'is_active' in data:
        user.is_active = data['is_active']

    if 'role' in data:
        role = Role.query.filter_by(name=data['role']).first()
        if not role:
            return jsonify({'error': f'Role "{data["role"]}" não encontrada'}), 400
        user.role_id = role.id

    db.session.commit()

    audit_log('USER_UPDATED_BY_ADMIN', resource=f'user:{user_id}')

    return jsonify(user.to_dict(include_email=True)), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_auth
@require_role('admin')
def delete_user(user_id):
    if user_id == g.user.id:
        return jsonify({'error': 'Você não pode deletar sua própria conta'}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    db.session.delete(user)
    db.session.commit()

    audit_log('USER_DELETED_BY_ADMIN', resource=f'user:{user_id}')

    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@admin_bp.route('/logs', methods=['GET'])
@require_auth
@require_role('admin')
def get_logs():
    log_type = request.args.get('type', 'audit', type=str)
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    days = request.args.get('days', 30, type=int)

    if page < 1 or limit < 1 or limit > 500:
        return jsonify({'error': 'Parâmetros de paginação inválidos'}), 400

    cutoff = datetime.utcnow() - timedelta(days=days)

    if log_type == 'login':
        query = LoginLog.query.filter(LoginLog.attempted_at >= cutoff).order_by(desc(LoginLog.attempted_at))
    elif log_type == 'audit':
        query = AuditLog.query.filter(AuditLog.created_at >= cutoff).order_by(desc(AuditLog.created_at))
    else:
        return jsonify({'error': 'Tipo de log inválido (login ou audit)'}), 400

    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    return jsonify({
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'logs': [log.to_dict() for log in pagination.items]
    }), 200


@admin_bp.route('/roles', methods=['GET'])
@require_auth
@require_role('admin')
def get_roles():
    roles = Role.query.all()
    return jsonify([role.to_dict() for role in roles]), 200


@admin_bp.route('/users/<int:user_id>/password-reset', methods=['POST'])
@require_auth
@require_role('admin')
@require_json('new_password')
def admin_reset_password(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    user.password_hash = hash_password(request.get_json()['new_password'])
    db.session.commit()

    audit_log('PASSWORD_RESET_BY_ADMIN', resource=f'user:{user_id}')

    return jsonify({'message': 'Senha redefinida com sucesso'}), 200
