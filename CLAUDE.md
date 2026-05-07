# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Instalar dependências
pip install -r requirements.txt

# Variáveis de ambiente mínimas para dev local
cp .env.example .env  # ou criar .env manualmente (ver seção abaixo)

# Criar tabelas + admin + categorias do sistema
python scripts/seed.py

# Popular dados fictícios de demonstração (6 meses)
python scripts/seed_demo.py

# Apagar apenas dados financeiros (mantém usuários e categorias do sistema)
python scripts/clear_db.py

# Rodar servidor de desenvolvimento
uvicorn app.main:app --reload --port 8000

# Rodar todos os testes
pytest tests/ -v

# Rodar um teste específico
pytest tests/test_auth.py::test_login_success -v
```

## Variáveis de ambiente (`.env`)

```
SECRET_KEY=qualquer-string-longa
DATABASE_URL=sqlite:///./data/financas.db
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=senha123
EVOLUTION_API_URL=      # opcional — WhatsApp via Evolution API
EVOLUTION_API_KEY=
EVOLUTION_INSTANCE=
```

## Arquitetura

Aplicação **server-side rendered** com FastAPI + Jinja2. Não há API REST separada nem frontend SPA — cada rota retorna HTML direto ou `RedirectResponse`.

```
app/
├── main.py              ← monta o app, registra todos os routers, inicia o scheduler
├── core/
│   ├── auth.py          ← get_current_user (Depends), AuthRedirect exception
│   ├── config.py        ← Settings via pydantic-settings (lê .env)
│   ├── database.py      ← engine SQLite, SessionLocal, Base, get_db
│   ├── scheduler.py     ← APScheduler: roda a cada hora, filtra por horário do usuário
│   └── security.py      ← hash_password, verify_password (bcrypt)
├── models/models.py     ← todos os 14 modelos SQLAlchemy em um único arquivo
├── modules/             ← um subpacote por recurso (router.py + service.py quando há lógica)
│   └── {recurso}/router.py
└── templates/           ← Jinja2, um diretório por módulo
    └── base.html        ← layout principal com sidebar, topbar e flash messages
scripts/
├── seed.py              ← create_all + admin + categorias do sistema + _migrate()
├── seed_demo.py         ← dados fictícios vinculados ao ADMIN_EMAIL
└── clear_db.py          ← apaga dados financeiros com dupla confirmação
```

## Padrões críticos

**Autenticação:** toda rota protegida usa `user: User = Depends(get_current_user)`. Esse helper lê `request.session["user_id"]` e levanta `AuthRedirect` (capturado como exception handler global) se não autenticado — nunca retorna 401.

**Isolamento por usuário:** toda query ao banco **deve** filtrar por `user_id`. O cascade `onDelete: CASCADE` garante que deletar um usuário limpa todos os seus dados.

**Categorias:** `is_system=True` são globais (criadas pelo seed, sem `user_id`). Queries de categorias usam `(Category.user_id == user.id) | (Category.is_system == True)`. Nunca deletar categorias do sistema.

**Contexto de template:** cada router tem um helper `_ctx(request, user, db)` que retorna `{request, user, unread_count}` — sempre passe com `**_ctx(...)` para que o `base.html` funcione (badge de notificações, nome do usuário).

**Flash messages:** via query params — `RedirectResponse("/rota?success=Mensagem")` ou `?error=Mensagem`. O `base.html` já renderiza automaticamente.

**Saldo de contas:** toda transação com `status=completed` chama `apply_to_balance()` do `transactions/service.py`. Ao editar ou deletar, reverter o efeito anterior antes de aplicar o novo.

## Banco de dados

Usa SQLite (arquivo em `/app/data/financas.db` no container, `./data/` em dev). Não há Alembic migrations ativas — novas colunas são adicionadas via `_migrate()` em `scripts/seed.py` usando `ALTER TABLE ... ADD COLUMN` envolvido em try/except. Ao adicionar colunas ao modelo, adicionar o `ALTER` correspondente em `_migrate()`.

## Scheduler (notificações automáticas)

Roda a cada hora no minuto 0. Cada job compara `datetime.now().hour` com `user.profile.notif_bill_hour` (padrão 8) e `notif_budget_hour` (padrão 9). Se bater, cria `Notification` no banco e envia WhatsApp se `profile.whatsapp_enabled=True`. O TZ do container é `America/Sao_Paulo`.

## Deploy

O `entrypoint.sh` roda `seed.py` (cria tabelas + migra colunas) antes de subir o uvicorn. A imagem é publicada em `ghcr.io/ulyssesrocharosa/financeiropython` via GitHub Actions:
- Push em `main` → publica `:latest` + `:<sha>`
- Push de tag `vX.Y` → publica `:vX.Y`

Para criar uma release: `git tag v1.0 && git push origin v1.0`

## Testes

SQLite in-memory com `StaticPool` (compartilhado entre threads). O `conftest.py` cria as tabelas antes de cada teste e dropa depois. Para criar um usuário de teste, usar o helper `create_test_user(db)` definido em `tests/test_auth.py`.
