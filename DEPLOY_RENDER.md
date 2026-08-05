# 🚀 Guia de Deploy no Render

Seu dashboard Diligência Elite RJ agora está configurado para ser deployado no **Render** com um banco de dados **PostgreSQL** persistente!

## ✅ O que foi feito

1. **Integração com SQLAlchemy** - Convertemos o app de arquivos JSON para banco de dados PostgreSQL
2. **Modelos de dados** - Criamos modelos para Diligências, Processos e Histórico de Relatórios
3. **Configuração Render** - render.yaml já está configurado com banco de dados

## 📋 Pré-requisitos

- Conta no [render.com](https://render.com) (grátis)
- Git configurado
- Projeto já no GitHub

## 🎯 Passos para Deploy

### 1. Fazer commit das mudanças

```bash
git add .
git commit -m "Configurar banco de dados PostgreSQL e deploy no Render"
git push
```

### 2. Acessar Render.com

1. Acesse https://render.com
2. Faça login com sua conta GitHub
3. Clique em "New +"
4. Selecione "Web Service"

### 3. Conectar seu repositório

1. Selecione seu repositório GitHub
2. Configure:
   - **Name**: `diligencia-elite-rj`
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (ou Starter para melhor performance)

### 4. Configurar a URL do banco de dados

A variável `DATABASE_URL` é criada automaticamente pelo Render quando você adiciona um PostgreSQL.

Se estiver usando o render.yaml, o banco já está configurado!

### 5. Deploy

Clique em "Create Web Service" e o Render fará o deploy automaticamente.

## 🗄️ Banco de Dados

O PostgreSQL no Render:
- ✅ Persiste os dados permanentemente
- ✅ Não é apagado quando redeploya
- ✅ Está automaticamente configurado
- ✅ Gratuito com plano starter

## 📊 Características

### Dados Persistidos
- ✅ Diligências
- ✅ Processos
- ✅ Histórico de Relatórios
- ✅ Todos os campos operacionais

### Acesso

Após o deploy, seu app estará acessível em:
```
https://diligencia-elite-rj.onrender.com
```

## 🔧 Verificação Local (Opcional)

Para testar localmente com o banco de dados:

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar localmente (usará SQLite por padrão)
python -m flask run
```

## 🐛 Troubleshooting

### "DatabaseURL not found"
- Aguarde o PostgreSQL ser criado (pode levar 2-3 minutos)
- Redeploy a aplicação

### "Import error: No module named 'sqlalchemy'"
- Execute: `pip install -r requirements.txt`
- Faça novo commit e push

### Dados desapareceram
- Verifique se o PostgreSQL está rodando no Render
- Não deve acontecer, mas sempre faça backup!

## 📞 Suporte

Para mais informações:
- [Documentação Render](https://render.com/docs)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com)
- [GitHub Pages](https://docs.github.com/en/pages)

---

**🎉 Pronto!** Seu dashboard agora está 100% online com dados persistindo automaticamente!
