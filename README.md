# Minhas Finanças (FastAPI)

Aplicação financeira pessoal em FastAPI, Jinja e SQLite.

## Execução local

1. Copie `.env.example` para `.env` e defina uma `SECRET_KEY` longa e uma senha de administrador com pelo menos 12 caracteres.
2. Execute `python scripts/migrate.py`.
3. Execute `python scripts/seed.py`.
4. Execute `uvicorn app.main:app --reload`.

O login inicial é definido por `ADMIN_EMAIL` e `ADMIN_PASSWORD`; não há credenciais padrão no código.

## Banco de dados

SQLite é o perfil suportado para um usuário local. Use somente um worker e mantenha `RUN_SCHEDULER=true` em uma única instância. O arquivo `data/financas.db` deve entrar na rotina de backup.

Para múltiplos usuários, múltiplas réplicas ou acesso público com escrita concorrente, configure PostgreSQL em `DATABASE_URL`, desative o scheduler nas réplicas web e execute-o em uma única instância dedicada.

## Operação

O contêiner executa migrations e o seed idempotente antes de subir. Instalações SQLite anteriores são reconhecidas e recebem a coluna de deduplicação sem apagar dados. A rota `GET /healthz` valida a conexão com o banco.

## Build de produção

O workflow do GitHub Actions executa testes, migrations e `docker build` a cada push na `main`. GitHub valida a imagem; a aplicação contínua deve ser executada no servidor.

No servidor, copie `.env.example` para `.env`, preencha os segredos de produção e execute:

```sh
docker compose -f docker-compose.prod.yml up -d --build
```

Esse perfil mantém somente o banco SQLite no volume `financas_data`, inicia um único worker e executa o scheduler na mesma instância. Faça backup periódico desse volume.
