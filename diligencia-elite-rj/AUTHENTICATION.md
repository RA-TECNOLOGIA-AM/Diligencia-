# Sistema de Autenticação - Diligência Elite RJ

## Visão Geral

Sistema de autenticação completo, production-ready para a plataforma Diligência Elite RJ com:

- ✅ Login/Signup com validação completa
- ✅ JWT + Refresh Tokens
- ✅ Hashing seguro (Argon2 com fallback para bcrypt)
- ✅ Rate limiting (anti-brute force)
- ✅ Session management
- ✅ RBAC (Role-Based Access Control)
- ✅ Audit logging
- ✅ Password recovery
- ✅ User profile management
- ✅ Admin panel

---

## Configuração Inicial

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

**Variáveis críticas:**
- `DATABASE_URL`: PostgreSQL em produção, SQLite em desenvolvimento
- `JWT_SECRET`: Chave secreta para assinar JWTs (mude em produção!)
- `ADMIN_EMAIL` / `ADMIN_PASSWORD`: Credenciais do primeiro admin

### 3. Inicializar Banco de Dados

```bash
python init_db.py
```

Isso irá:
- Criar todas as tabelas do banco
- Criar as 4 roles padrão (admin, supervisor, user, visitor)
- Criar usuário administrador

### 4. Executar Aplicação

```bash
python -m flask run
# ou
gunicorn app:app
```

Acesse:
- Dashboard: http://localhost:5000/
- Login: http://localhost:5000/login
- Signup: http://localhost:5000/signup

---

## Arquitetura de Autenticação

### Fluxo de Login

```
[Usuário] 
   ↓
[POST /auth/login] com email + senha
   ↓
[Validação] (rate limit, credenciais, ativo)
   ↓
[Geração] JWT (15min) + Refresh Token (7 dias)
   ↓
[Resposta] access_token em JSON + refresh_token em HttpOnly cookie
   ↓
[Cliente] Armazena token em memória, usa em Authorization header
   ↓
[Rotas protegidas] Verificam JWT via middleware @require_auth
```

### Estrutura de Token

**Access Token (JWT - 15 minutos):**
```json
{
  "user_id": 1,
  "exp": 1234567890,
  "iat": 1234567800
}
```

**Refresh Token (HttpOnly cookie - 7 dias):**
- Armazenado em cookie seguro (HttpOnly, Secure, SameSite=Lax)
- Hash SHA-256 armazenado no banco
- Permite renovar access token sem re-fazer login

---

## API de Autenticação

### Registro

```bash
POST /auth/register
Content-Type: application/json

{
  "name": "João",
  "surname": "Silva",
  "email": "joao@example.com",
  "username": "joao123",
  "phone": "(21) 99999-9999",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!",
  "accept_terms": true
}

Response: 201
{
  "message": "Cadastro realizado com sucesso",
  "user_id": 2,
  "email": "joao@example.com"
}
```

### Login

```bash
POST /auth/login
Content-Type: application/json

{
  "email": "joao@example.com",
  "password": "SecurePass123!",
  "remember_me": true
}

Response: 200
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "email": "joao@example.com",
    "first_name": "João",
    "last_name": "Silva",
    "role": "user"
  }
}

Set-Cookie: refresh_token=secure_token_here; HttpOnly; Secure; SameSite=Lax; Max-Age=604800
```

### Logout

```bash
POST /auth/logout
Authorization: Bearer <access_token>

Response: 200
{
  "message": "Logout realizado com sucesso"
}
```

### Refresh Token

```bash
POST /auth/refresh
Cookie: refresh_token=token_here

Response: 200
{
  "access_token": "new_token_here"
}
```

### Recuperar Senha

```bash
POST /auth/forgot-password
Content-Type: application/json

{
  "email": "joao@example.com"
}

Response: 200
{
  "message": "Link de recuperação enviado para o email",
  "reset_token": "secure_reset_token"
}
```

### Redefinir Senha

```bash
POST /auth/reset-password
Content-Type: application/json

{
  "token": "reset_token_from_email",
  "new_password": "NewPassword123!",
  "confirm_password": "NewPassword123!"
}

Response: 200
{
  "message": "Senha redefinida com sucesso"
}
```

---

## API de Usuário

### Obter Perfil

```bash
GET /api/users/profile
Authorization: Bearer <access_token>

Response: 200
{
  "id": 2,
  "email": "joao@example.com",
  "username": "joao123",
  "first_name": "João",
  "last_name": "Silva",
  "phone": "(21) 99999-9999",
  "avatar_url": "/static/avatars/user_2_abc123.jpg",
  "role": "user",
  "preferences": {
    "theme": "dark",
    "language": "pt"
  }
}
```

### Atualizar Perfil

```bash
PUT /api/users/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "João Paulo",
  "last_name": "Silva Santos",
  "phone": "(21) 98888-8888",
  "preferences": {
    "theme": "light",
    "language": "pt"
  }
}

Response: 200
{ ...updated user... }
```

### Upload de Avatar

```bash
POST /api/users/profile/avatar
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

[arquivo de imagem]

Response: 200
{
  "avatar_url": "/static/avatars/user_2_xyz789.png"
}
```

### Alterar Senha

```bash
POST /auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword123!",
  "confirm_password": "NewPassword123!"
}

Response: 200
{
  "message": "Senha alterada com sucesso. Faça login novamente."
}
```

### Deletar Conta

```bash
DELETE /api/users/account
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "password": "CurrentPassword123!"
}

Response: 200
{
  "message": "Conta deletada com sucesso"
}
```

---

## API de Admin

### Dashboard Admin

```bash
GET /admin/dashboard
Authorization: Bearer <admin_token>

Response: 200
{
  "total_users": 15,
  "active_users": 13,
  "today_logins": 8,
  "failed_logins": 2,
  "recent_activity": [...]
}
```

### Listar Usuários

```bash
GET /admin/users?page=1&limit=20
Authorization: Bearer <admin_token>

Response: 200
{
  "total": 15,
  "pages": 1,
  "current_page": 1,
  "users": [...]
}
```

### Criar Usuário (Admin)

```bash
POST /admin/users
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "email": "novo@example.com",
  "username": "novo_user",
  "password": "SecurePass123!",
  "first_name": "Novo",
  "last_name": "Usuário",
  "phone": "(21) 99999-9999",
  "role": "supervisor"
}

Response: 201
{ ...created user... }
```

### Atualizar Usuário (Admin)

```bash
PUT /admin/users/2
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "first_name": "João Paulo",
  "last_name": "Silva",
  "role": "user",
  "is_active": true
}

Response: 200
{ ...updated user... }
```

### Deletar Usuário (Admin)

```bash
DELETE /admin/users/2
Authorization: Bearer <admin_token>

Response: 200
{
  "message": "Usuário deletado com sucesso"
}
```

### Redefinir Senha (Admin)

```bash
POST /admin/users/2/password-reset
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "new_password": "NewPassword123!"
}

Response: 200
{
  "message": "Senha redefinida com sucesso"
}
```

### Obter Logs

```bash
GET /admin/logs?type=login&page=1&limit=50&days=30
Authorization: Bearer <admin_token>

Response: 200
{
  "total": 150,
  "pages": 3,
  "current_page": 1,
  "logs": [
    {
      "id": 1,
      "email": "joao@example.com",
      "ip_address": "192.168.1.1",
      "success": true,
      "attempted_at": "2026-08-07T10:30:00"
    },
    ...
  ]
}
```

---

## Segurança

### Proteção Implementada

✅ **Hashing**: Argon2 (default) / bcrypt (fallback)
- Tempo de hashing: ~100ms (resis a brute-force)
- Salt incluído automaticamente

✅ **Tokens JWT**
- Assinados com HS256
- Expiry curto (15 min) para access token
- Refresh token em HttpOnly cookie (7 dias)

✅ **Rate Limiting**
- Máx 5 tentativas de login em 15 minutos
- Por email (não IP, para suportar proxies)
- Lockout automático com resposta 429

✅ **CSRF Protection**
- Validação de Content-Type JSON
- Cookies SameSite=Lax

✅ **XSS Prevention**
- No dados sensíveis em localStorage
- Token em HttpOnly cookie (não acessível via JS)
- Input sanitizado

✅ **SQL Injection Prevention**
- SQLAlchemy parameterized queries
- Sem string concatenation em queries

✅ **Audit Logging**
- Todos auth events registrados (login, logout, password changes)
- IP e user agent capturados
- Admin pode acessar logs completos

### Vulnerabilidades Prevenidas

- ❌ Plain text passwords: Argon2 hashing
- ❌ Session hijacking: Tokens armazenados com hash
- ❌ Credential stuffing: Rate limiting + lockout
- ❌ Expired tokens usados: Verificação de exp
- ❌ User enumeration: Mensagens genéricas ("Email ou senha incorretos")
- ❌ CSRF attacks: Validação de content-type
- ❌ Privilege escalation: Role validation em middleware

---

## Estrutura de Banco de Dados

### Tabelas Principais

**users**
```
id (PK)
email (unique, indexed)
username (unique)
password_hash
first_name, last_name
phone
avatar_url
role_id (FK)
preferences (JSON) - theme, language
is_active
password_reset_token
password_reset_expires
last_login
created_at, updated_at
```

**roles**
```
id (PK)
name (unique) - admin, supervisor, user, visitor
description
created_at
```

**permissions**
```
id (PK)
name (unique)
description
created_at
```

**role_permissions** (M2M)
```
role_id (FK)
permission_id (FK)
```

**sessions**
```
id (PK)
user_id (FK, indexed)
token_hash (indexed)
refresh_token_hash (indexed)
expires_at
created_at
revoked (bool)
```

**login_logs**
```
id (PK)
user_id (FK, nullable)
email
ip_address
user_agent
success (bool)
failure_reason
attempted_at (indexed)
```

**audit_logs**
```
id (PK)
user_id (FK)
action
resource
details (JSON)
ip_address
created_at (indexed)
```

---

## Roles e Permissions

### Roles Padrão

| Role | Descrição | Permissões |
|------|-----------|-----------|
| **admin** | Gerenciador do sistema | Todas as 13 permissões |
| **supervisor** | Supervisor de diligências | Criar, editar, deletar diligências/processos, exportar relatórios |
| **user** | Usuário comum | Ver/criar diligências/processos, ver relatórios |
| **visitor** | Visitante | Apenas leitura (view) |

### Permissões Disponíveis

```
view_diligencias, create_diligencia, edit_diligencia, delete_diligencia
view_processos, create_processo, edit_processo, delete_processo
view_reports, export_reports
manage_users, view_logs, manage_roles
```

### Usar Roles em Rotas

```python
# Proteger rota com autenticação
@app.route('/api/diligencias', methods=['GET'])
@require_auth
def get_diligencias():
    user = g.user
    # user.role.name == 'admin', 'supervisor', 'user', etc
    return jsonify({...})

# Proteger rota com role específico
@app.route('/admin/users', methods=['GET'])
@require_auth
@require_role('admin')
def list_users():
    return jsonify({...})

# Proteger com múltiplos roles
@app.route('/api/processos/<id>', methods=['DELETE'])
@require_auth
@require_role('admin', 'supervisor')
def delete_processo(id):
    return jsonify({...})
```

---

## Frontend

### Serviço de Autenticação (`auth.js`)

O arquivo `/static/js/auth.js` fornece uma classe `AuthService`:

```javascript
// Verificar autenticação
if (auth.isAuthenticated()) {
    const user = auth.getUser();
    console.log(user.first_name);
}

// Login
const result = await auth.login('email@example.com', 'password', true);

// Logout
await auth.logout();

// Perfil
const profile = await auth.getProfile();

// Requisições autenticadas
const response = await auth.makeAuthenticatedRequest('/api/diligencias');

// Verificar role
if (auth.hasRole('admin')) { ... }
if (auth.hasAnyRole('admin', 'supervisor')) { ... }
```

### Headers de Autenticação

Todo request para API protegida deve incluir:

```
Authorization: Bearer <access_token>
```

O `auth.js` adiciona automaticamente quando usa `auth.makeAuthenticatedRequest()`.

### Session Timeout

- Inatividade de 30 minutos = sessão expirada
- Atividade rastreada por: mouse, keyboard, scroll, touch
- Token refresh automático cada 12 minutos

---

## Deployment no Render

### Configurar Variáveis de Ambiente no Render

1. Dashboard Render → Seu serviço → Settings → Environment
2. Adicione:

```
DATABASE_URL=postgresql://...
JWT_SECRET=sua-chave-supersecrta-aqui-min-32-chars
ADMIN_EMAIL=admin@...
ADMIN_PASSWORD=...
FLASK_ENV=production
```

### Build Command

```bash
pip install -r requirements.txt && python init_db.py
```

### Start Command

```bash
gunicorn app:app
```

### First Deploy

1. Commit e push para git
2. Render detecta `Procfile` e faz deploy
3. Executa `init_db.py` que cria usuário admin
4. Acesse https://seu-app.onrender.com/login

---

## Troubleshooting

### "Database not initialized"
→ Execute: `python init_db.py`

### "Invalid token"
→ Verifique JWT_SECRET é consistente
→ Token pode ter expirado (15 min)
→ Refresh token usando POST /auth/refresh

### "Too many login attempts"
→ Rate limiting ativo
→ Aguarde 15 minutos ou mude email/IP

### "Module 'auth' not found"
→ Certifique que está executando da pasta `diligencia-elite-rj/`
→ Ou: `export PYTHONPATH=$PWD`

### Argon2 não instalado
→ Bcrypt funciona como fallback
→ Para instalar Argon2: `pip install argon2-cffi`

---

## Melhorias Futuras (Post-MVP)

- [ ] Email verification on signup
- [ ] Two-factor authentication (2FA)
- [ ] OAuth2 (Google, GitHub)
- [ ] SSO para instituições
- [ ] API key generation
- [ ] WebAuthn/biometric support
- [ ] Session management UI
- [ ] Custom permissions UI
- [ ] LDAP/Active Directory integration
- [ ] Audit log retention policies

---

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs: `tail -f app.log`
2. Consulte a documentação de cada módulo em `/auth`, `/users`, `/admin`
3. Verifique models.py para schema do banco

---

**Última atualização:** 2026-08-07
**Versão:** 1.0.0
**Status:** Production-Ready
