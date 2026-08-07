import os
from flask import request, jsonify, g
from werkzeug.utils import secure_filename
from . import users_bp
from auth.utils import require_auth, require_json, verify_password, hash_password, audit_log
from models import db, User


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'avatars')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@users_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    user = g.user
    return jsonify(user.to_dict(include_email=True)), 200


@users_bp.route('/profile', methods=['PUT'])
@require_auth
@require_json('first_name', 'last_name')
def update_profile():
    user = g.user
    data = request.get_json()

    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.phone = data.get('phone', user.phone)

    if 'preferences' in data:
        prefs = data['preferences']
        user.preferences = {
            'theme': prefs.get('theme', user.preferences.get('theme', 'dark')),
            'language': prefs.get('language', user.preferences.get('language', 'pt'))
        }

    db.session.commit()

    audit_log('PROFILE_UPDATED', resource=f'user:{user.id}', details={
        'first_name': user.first_name,
        'last_name': user.last_name
    })

    return jsonify(user.to_dict(include_email=True)), 200


@users_bp.route('/profile/avatar', methods=['POST'])
@require_auth
def upload_avatar():
    user = g.user

    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Tipo de arquivo não permitido. Use PNG, JPG, JPEG ou GIF'}), 400

    import secrets
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{user.id}_{secrets.token_hex(8)}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)

    user.avatar_url = f'/static/avatars/{filename}'
    db.session.commit()

    audit_log('AVATAR_UPDATED', resource=f'user:{user.id}')

    return jsonify({'avatar_url': user.avatar_url}), 200


@users_bp.route('/profile/preferences', methods=['POST'])
@require_auth
@require_json('theme', 'language')
def update_preferences():
    user = g.user
    data = request.get_json()

    if data['theme'] not in ['light', 'dark']:
        return jsonify({'error': 'Tema inválido'}), 400

    if data['language'] not in ['pt', 'en']:
        return jsonify({'error': 'Idioma inválido'}), 400

    user.preferences = {
        'theme': data['theme'],
        'language': data['language']
    }
    db.session.commit()

    audit_log('PREFERENCES_UPDATED', resource=f'user:{user.id}', details=user.preferences)

    return jsonify(user.preferences), 200


@users_bp.route('/account', methods=['DELETE'])
@require_auth
@require_json('password')
def delete_account():
    user = g.user
    data = request.get_json()

    if not verify_password(data['password'], user.password_hash):
        return jsonify({'error': 'Senha incorreta'}), 401

    user_id = user.id
    db.session.delete(user)
    db.session.commit()

    audit_log('ACCOUNT_DELETED', resource=f'user:{user_id}')

    response = jsonify({'message': 'Conta deletada com sucesso'})
    response.delete_cookie('refresh_token')
    return response, 200
