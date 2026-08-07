from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Diligencia(db.Model):
    __tablename__ = 'diligencias'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, default='Nova diligência')
    process_number = db.Column(db.String(100), unique=True, nullable=False)
    responsavel = db.Column(db.String(255), default='')
    region = db.Column(db.String(100), default='Não informado')
    municipio = db.Column(db.String(255), default='')
    comarca = db.Column(db.String(255), default='')
    lat = db.Column(db.Float, default=-22.9068)
    lng = db.Column(db.Float, default=-43.1729)
    status = db.Column(db.String(50), default='Pendente')
    resumo = db.Column(db.Text, default='')
    processos = db.Column(db.Integer, default=1)
    valor_alvara = db.Column(db.Float)
    valor_total = db.Column(db.Float)
    valor_causa = db.Column(db.Float)
    roteiro_estrategico = db.Column(db.Text, default='')
    modalidade_diligencia = db.Column(db.String(255), default='Não informado')
    distancia_roteiro = db.Column(db.Float)
    preco_gasolina = db.Column(db.Float)
    preco_aluguel_carro = db.Column(db.Float)
    modus_operandi = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'process_number': self.process_number,
            'responsavel': self.responsavel,
            'region': self.region,
            'municipio': self.municipio,
            'comarca': self.comarca,
            'lat': self.lat,
            'lng': self.lng,
            'status': self.status,
            'resumo': self.resumo,
            'processos': self.processos,
            'valor_alvara': self.valor_alvara,
            'valor_total': self.valor_total,
            'valor_causa': self.valor_causa,
            'roteiro_estrategico': self.roteiro_estrategico,
            'modalidade_diligencia': self.modalidade_diligencia,
            'distancia_roteiro': self.distancia_roteiro,
            'preco_gasolina': self.preco_gasolina,
            'preco_aluguel_carro': self.preco_aluguel_carro,
            'modus_operandi': self.modus_operandi,
        }


class Processo(db.Model):
    __tablename__ = 'processos'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(50), default='Pendente')
    region = db.Column(db.String(100), default='Metropolitana')
    municipio = db.Column(db.String(255), default='')
    comarca = db.Column(db.String(255), default='')
    responsavel = db.Column(db.String(255), default='')
    urgencia = db.Column(db.String(50), default='Pendente')
    resumo = db.Column(db.Text, default='')
    valor_alvara = db.Column(db.Float)
    valor_total = db.Column(db.Float)
    valor_causa = db.Column(db.Float)
    roteiro_estrategico = db.Column(db.Text, default='')
    modalidade_diligencia = db.Column(db.String(255), default='Não informado')
    distancia_roteiro = db.Column(db.Float)
    preco_gasolina = db.Column(db.Float)
    preco_aluguel_carro = db.Column(db.Float)
    modus_operandi = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'status': self.status,
            'region': self.region,
            'municipio': self.municipio,
            'comarca': self.comarca,
            'responsavel': self.responsavel,
            'urgencia': self.urgencia,
            'resumo': self.resumo,
            'valor_alvara': self.valor_alvara,
            'valor_total': self.valor_total,
            'valor_causa': self.valor_causa,
            'roteiro_estrategico': self.roteiro_estrategico,
            'modalidade_diligencia': self.modalidade_diligencia,
            'distancia_roteiro': self.distancia_roteiro,
            'preco_gasolina': self.preco_gasolina,
            'preco_aluguel_carro': self.preco_aluguel_carro,
            'modus_operandi': self.modus_operandi,
        }


class ReportHistory(db.Model):
    __tablename__ = 'report_history'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    report_data = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'report_data': self.report_data,
        }


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), default='')
    permissions = db.relationship('Permission', secondary='role_permissions', backref='roles')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': [p.to_dict() for p in self.permissions],
        }


class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
        }


role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)
)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), default='')
    last_name = db.Column(db.String(100), default='')
    phone = db.Column(db.String(20), default='')
    avatar_url = db.Column(db.String(255), default='')
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False, default=1)
    role = db.relationship('Role', backref='users')
    preferences = db.Column(db.JSON, default={'theme': 'dark', 'language': 'pt'})
    is_active = db.Column(db.Boolean, default=True)
    password_reset_token = db.Column(db.String(255), default='')
    password_reset_expires = db.Column(db.DateTime, default=None)
    last_login = db.Column(db.DateTime, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'avatar_url': self.avatar_url,
            'role': self.role.name if self.role else 'user',
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_email:
            data['email'] = self.email
            data['preferences'] = self.preferences
        return data


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    user = db.relationship('User', backref='sessions')
    token_hash = db.Column(db.String(255), nullable=False, index=True)
    refresh_token_hash = db.Column(db.String(255), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'revoked': self.revoked,
        }


class LoginLog(db.Model):
    __tablename__ = 'login_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    user = db.relationship('User', backref='login_logs')
    email = db.Column(db.String(255), default='')
    ip_address = db.Column(db.String(45), default='')
    user_agent = db.Column(db.String(512), default='')
    success = db.Column(db.Boolean, default=False)
    failure_reason = db.Column(db.String(255), default='')
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'ip_address': self.ip_address,
            'success': self.success,
            'failure_reason': self.failure_reason,
            'attempted_at': self.attempted_at.isoformat() if self.attempted_at else None,
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    user = db.relationship('User', backref='audit_logs')
    action = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(255), default='')
    details = db.Column(db.JSON, default={})
    ip_address = db.Column(db.String(45), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource': self.resource,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
