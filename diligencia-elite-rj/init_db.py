#!/usr/bin/env python3
import os
import sys

from app import app, db
from models import Role, Permission, User
from auth.utils import hash_password

def init_database():
    with app.app_context():
        print("Criando tabelas do banco de dados...")
        db.create_all()
        print("✓ Tabelas criadas")

        print("\nCriando permissões...")
        permissions_data = [
            ('view_diligencias', 'Ver diligências'),
            ('create_diligencia', 'Criar diligência'),
            ('edit_diligencia', 'Editar diligência'),
            ('delete_diligencia', 'Deletar diligência'),
            ('view_processos', 'Ver processos'),
            ('create_processo', 'Criar processo'),
            ('edit_processo', 'Editar processo'),
            ('delete_processo', 'Deletar processo'),
            ('view_reports', 'Ver relatórios'),
            ('export_reports', 'Exportar relatórios'),
            ('manage_users', 'Gerenciar usuários'),
            ('view_logs', 'Ver logs de auditoria'),
            ('manage_roles', 'Gerenciar roles'),
        ]

        permissions = {}
        for perm_name, perm_desc in permissions_data:
            perm = Permission.query.filter_by(name=perm_name).first()
            if not perm:
                perm = Permission(name=perm_name, description=perm_desc)
                db.session.add(perm)
            permissions[perm_name] = perm
        db.session.commit()
        print(f"✓ {len(permissions)} permissões criadas")

        print("\nCriando roles...")
        roles_data = {
            'admin': {
                'description': 'Administrador do sistema',
                'permissions': list(permissions.keys())
            },
            'supervisor': {
                'description': 'Supervisor de diligências',
                'permissions': [
                    'view_diligencias', 'create_diligencia', 'edit_diligencia', 'delete_diligencia',
                    'view_processos', 'create_processo', 'edit_processo', 'delete_processo',
                    'view_reports', 'export_reports'
                ]
            },
            'user': {
                'description': 'Usuário comum',
                'permissions': [
                    'view_diligencias', 'create_diligencia',
                    'view_processos', 'create_processo',
                    'view_reports'
                ]
            },
            'visitor': {
                'description': 'Visitante (apenas leitura)',
                'permissions': ['view_diligencias', 'view_processos', 'view_reports']
            }
        }

        for role_name, role_data in roles_data.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(
                    name=role_name,
                    description=role_data['description']
                )
                for perm_name in role_data['permissions']:
                    if perm_name in permissions:
                        role.permissions.append(permissions[perm_name])
                db.session.add(role)

        db.session.commit()
        print("✓ Roles criadas com permissões")

        print("\nCriando usuário administrador padrão...")
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@diligencia-elite.com.br')
        admin_password = os.getenv('ADMIN_PASSWORD', 'AdminPassword123!')

        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin_role = Role.query.filter_by(name='admin').first()
            admin = User(
                email=admin_email,
                username='admin',
                password_hash=hash_password(admin_password),
                first_name='Admin',
                last_name='User',
                role_id=admin_role.id,
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print(f"✓ Usuário administrador criado: {admin_email}")
        else:
            print(f"! Usuário administrador já existe: {admin_email}")

        print("\n✓ Banco de dados inicializado com sucesso!")
        print(f"\nPara fazer login, use:")
        print(f"  Email: {admin_email}")
        print(f"  Senha: {admin_password}")

if __name__ == '__main__':
    init_database()
