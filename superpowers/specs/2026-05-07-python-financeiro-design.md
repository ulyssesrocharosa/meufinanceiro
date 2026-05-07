# Design: Minhas Finanças — Python Edition

**Data:** 2026-05-07  
**Pasta alvo:** `financeiropython/` dentro do repositório existente  
**Premissa:** projeto totalmente independente do Node.js/React atual — não toca nenhum arquivo existente.

---

## Decisões fundamentais

| Decisão | Escolha |
|---|---|
| Backend | FastAPI + Python 3.12 |
| Templates | Jinja2 + Tailwind CDN + Chart.js CDN |
| Banco | SQLite3 via SQLAlchemy 2.x + Alembic |
| Auth | Session cookie (Starlette SessionMiddleware) |
| WhatsApp | Evolution API |
| Scheduler | APScheduler (embutido no processo FastAPI) |
| Deploy | Docker Swarm + Traefik (VPS com Portainer) |
| Módulos removidos | Família |

---

## Seção 1: Estrutura do projeto

```
financeiropython/
├── app/
│   ├── main.py                  # FastAPI app, registra routers, monta static
│   ├── core/
│   │   ├── config.py            # Settings via pydantic-settings (.env)
│   │   ├── database.py          # Engine SQLite + SessionLocal + Base
│   │   ├── auth.py              # get_current_user, require_admin (dependencies)
│   │   └── scheduler.py         # APScheduler: jobs de recorrentes + WhatsApp
│   ├── models/
│   │   └── models.py            # Todos os modelos SQLAlchemy (~300 linhas)
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── router.py        # GET /login, POST /login, GET /logout
│   │   │   └── templates/       # login.html
│   │   ├── dashboard/
│   │   │   ├── router.py        # GET /
│   │   │   └── templates/       # dashboard.html
│   │   ├── transactions/
│   │   │   ├── router.py        # CRUD + filtros
│   │   │   ├── service.py       # lógica de negócio
│   │   │   └── templates/       # list.html, form.html
│   │   ├── accounts/
│   │   ├── categories/
│   │   ├── recurring/
│   │   ├── budgets/
│   │   ├── goals/
│   │   ├── debts/
│   │   ├── investments/
│   │   ├── reports/
│   │   ├── notifications/
│   │   ├── whatsapp/
│   │   │   └── service.py       # cliente Evolution API
│   │   └── admin/
│   │       ├── router.py        # CRUD de usuários
│   │       └── templates/       # admin.html
│   └── templates/
│       ├── base.html            # layout: sidebar + navbar + flash messages
│       └── shared/              # macros: card.html, table.html, modal.html, badge.html
├── static/
│   └── app.js                   # JS mínimo (toggle sidebar, confirm delete)
├── data/
│   └── financas.db              # arquivo SQLite (volume Docker)
├── alembic/
│   ├── env.py
│   └── versions/
├── scripts/
│   └── seed.py                  # popula admin + categorias do sistema
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml           # dev local
└── docker-stack.yml             # Swarm + Traefik (produção)
```

**Fluxo de request:**
```
Browser → Traefik (prod) → Uvicorn → FastAPI router → service → SQLAlchemy → SQLite → Jinja2 → HTML
```

---

## Seção 2: Modelos de dados (SQLite)

12 tabelas. IDs inteiros auto-increment. Sem campos JSON opacos.

### users
```
id, email, name, password_hash, role (admin|user), is_active, created_at, last_login
```

### profiles
```
id, user_id FK, currency (default BRL), timezone (default America/Sao_Paulo),
theme (light|dark), whatsapp_phone, whatsapp_enabled
```

### accounts
```
id, user_id FK, name, type (checking|savings|credit|investment|cash|other),
balance (REAL), currency, institution, account_number, is_active, color, created_at
```

### categories
```
id, user_id FK nullable, parent_id FK nullable, name, type (income|expense|transfer),
icon, color, order_index, is_system, created_at
```
> `user_id = NULL` → categoria do sistema (compartilhada, não deletável)

### transactions
```
id, user_id FK, account_id FK, category_id FK nullable, recurring_bill_id FK nullable,
amount (REAL), type (income|expense|transfer), description, date, status (pending|completed|cancelled),
payment_method, is_reconciled, created_at, updated_at
```

### tags + transaction_tags
```
tags: id, user_id FK, name, color
transaction_tags: transaction_id FK, tag_id FK  (PK composta)
```

### recurring_bills
```
id, user_id FK, category_id FK nullable, name, amount (REAL), frequency (daily|weekly|monthly|quarterly|yearly),
start_date, end_date nullable, next_occurrence, is_active, days_before_reminder (default 3), created_at
```

### budgets
```
id, user_id FK, category_id FK, amount (REAL), period (weekly|monthly|quarterly|yearly),
start_date, end_date, created_at
```
> `spent` calculado via query (SUM de transactions no período), não armazenado

### goals
```
id, user_id FK, account_id FK nullable, name, target_amount (REAL), current_amount (REAL),
target_date, priority (low|medium|high), created_at, updated_at
```

### debts
```
id, user_id FK, name, original_amount (REAL), current_amount (REAL),
interest_rate (REAL default 0), type (credit_card|loan|mortgage|personal|other),
due_date nullable, status (active|paid|defaulted), created_at
```

### investments
```
id, user_id FK, account_id FK, name, type (stock|bond|fund|crypto|real_estate|other),
amount (REAL), current_value (REAL nullable), purchase_date, risk_level (low|medium|high),
created_at, updated_at
```

### notifications
```
id, user_id FK, type (bill_reminder|budget_alert|goal_update|system|transaction),
title, message, is_read, scheduled_for nullable, created_at
```

---

## Seção 3: Auth + Admin

### Fluxo de autenticação
- `SessionMiddleware` do Starlette com `SECRET_KEY` do `.env`
- Login: `POST /auth/login` → valida email+senha com bcrypt → grava `session["user_id"]` → redirect `/`
- Logout: `GET /auth/logout` → limpa session → redirect `/auth/login`
- Dependency `get_current_user`: lê `session["user_id"]` → busca user no banco → retorna User ou redirect 302
- Dependency `require_admin`: chama `get_current_user` + verifica `user.role == "admin"`
- Todas as rotas protegidas usam `Depends(get_current_user)`
- Rotas admin usam `Depends(require_admin)`

### Painel Admin (só para role=admin)
- `GET /admin` → lista usuários
- `POST /admin/users` → criar usuário
- `POST /admin/users/{id}/toggle` → ativar/desativar usuário
- `POST /admin/users/{id}/reset-password` → resetar senha
- Seed inicial: cria usuário admin com email+senha do `.env` + categorias do sistema

---

## Seção 4: WhatsApp + Scheduler

### Evolution API (service.py)
```python
# whatsapp/service.py
async def send_message(phone: str, message: str) -> bool:
    # POST {EVOLUTION_API_URL}/message/sendText/{INSTANCE}
    # headers: apikey: {EVOLUTION_API_KEY}
    # body: { "number": phone, "text": message }
```

Variáveis `.env`:
```
EVOLUTION_API_URL=https://evolution.seudominio.com
EVOLUTION_API_KEY=sua_chave
EVOLUTION_INSTANCE=nome_da_instancia
```

### APScheduler (scheduler.py)
Jobs registrados no startup do FastAPI:

| Job | Frequência | Lógica |
|---|---|---|
| `check_bill_reminders` | Diário 08:00 | Busca recurring_bills com `next_occurrence <= hoje + days_before_reminder` → envia WhatsApp ao usuário se `whatsapp_enabled` |
| `check_budget_alerts` | Diário 09:00 | Calcula % gasto por orçamento ativo → se > 80%, envia alerta |
| `check_goal_updates` | Semanal (segunda 08:30) | Resume progresso de metas com prazo nos próximos 30 dias |
| `update_next_occurrence` | Diário 00:05 | Atualiza `next_occurrence` das recorrentes executadas |

---

## Seção 5: Deploy (Docker Swarm + Traefik)

### Dockerfile
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-stack.yml (Swarm + Traefik)
```yaml
services:
  financeiropython:
    image: ${REGISTRY}/financeiropython:${TAG}
    volumes:
      - financas_data:/app/data
    environment:
      - DATABASE_URL=sqlite:////app/data/financas.db
      - SECRET_KEY=${SECRET_KEY}
      - EVOLUTION_API_URL=${EVOLUTION_API_URL}
      - EVOLUTION_API_KEY=${EVOLUTION_API_KEY}
      - EVOLUTION_INSTANCE=${EVOLUTION_INSTANCE}
      - ADMIN_EMAIL=${ADMIN_EMAIL}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
    deploy:
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.financas.rule=Host(`financas.seudominio.com`)"
        - "traefik.http.routers.financas.entrypoints=websecure"
        - "traefik.http.routers.financas.tls.certresolver=letsencrypt"
        - "traefik.http.services.financas.loadbalancer.server.port=8000"

volumes:
  financas_data:
```

### docker-compose.yml (dev local)
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app          # hot reload
      - ./data:/app/data
    env_file: .env
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Dashboard (visual)

Componentes usando Tailwind CDN + Chart.js CDN:
- Cards de KPIs: saldo total, receitas do mês, despesas do mês, saldo líquido
- Gráfico de linha: evolução do saldo (últimos 6 meses) — Chart.js
- Gráfico de pizza: gastos por categoria do mês — Chart.js
- Tabela: últimas 10 transações
- Alertas: contas vencendo em breve, orçamentos próximos do limite
- Sidebar: navegação por módulo, ícones Lucide via CDN

---

## Dependências principais (requirements.txt)

```
fastapi==0.115.x
uvicorn[standard]==0.29.x
sqlalchemy==2.0.x
alembic==1.13.x
jinja2==3.1.x
python-multipart==0.0.x    # forms HTML
itsdangerous==2.2.x        # sessions
passlib[bcrypt]==1.7.x     # hashing de senha
httpx==0.27.x              # cliente HTTP p/ Evolution API
apscheduler==3.10.x        # jobs agendados
pydantic-settings==2.x     # config via .env
python-dotenv==1.0.x
```
