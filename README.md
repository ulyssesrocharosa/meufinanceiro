# Meu Financeiro

Aplicação financeira pessoal em FastAPI, Jinja e SQLite.

## Desenvolvimento

1. Copie `.env.example` para `.env` e defina uma `SECRET_KEY` longa e uma senha de administrador com pelo menos 12 caracteres.
2. Execute `python scripts/migrate.py`.
3. Execute `python scripts/seed.py`.
4. Execute `uvicorn app.main:app --reload`.

O login inicial é definido por `ADMIN_EMAIL` e `ADMIN_PASSWORD`; não há credenciais padrão no código.

## Produção

O GitHub Actions executa testes, migrations e build Docker a cada push na `main`, além de publicar a imagem no GHCR.

No servidor, preencha `.env` com segredos reais e execute:

```sh
docker compose -f docker-compose.prod.yml up -d --build
```

O perfil de SQLite usa um único worker e uma única instância do scheduler. O volume `financas_data` contém o banco e deve fazer parte da rotina de backup.
