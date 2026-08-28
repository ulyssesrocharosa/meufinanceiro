"""
Seed de dados fictícios para demonstração.
Popula: contas, transações (6 meses), recorrentes, orçamentos, metas, dívidas, investimentos, tags, notificações.
Rodar: python scripts/seed_demo.py
"""
import sys, os, random
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.models import (
    Base, User, Account, Category, Transaction, Tag, RecurringBill,
    Budget, Goal, Debt, Investment, Notification,
    AccountType, CategoryType, TransactionType, TransactionStatus,
    RecurringFrequency, BudgetPeriod, GoalPriority,
    DebtType, DebtStatus, InvestmentType, RiskLevel, NotificationType,
)

TODAY = date(2026, 5, 7)
START = TODAY - relativedelta(months=6)  # nov/2025


def months_range():
    months = []
    d = date(START.year, START.month, 1)
    while d <= TODAY:
        months.append(d)
        d += relativedelta(months=1)
    return months


def rand_date(month_start: date) -> date:
    end = min(month_start + relativedelta(months=1) - timedelta(days=1), TODAY)
    delta = (end - month_start).days
    return month_start + timedelta(days=random.randint(0, delta))


def seed_demo():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter_by(email="admin@minhasfinancas.com").first()
        if not admin:
            print("ERRO: rode scripts/seed.py primeiro para criar o admin.")
            return
        uid = admin.id

        # ── Limpar dados demo anteriores (SQL direto evita problemas ORM) ─────
        db.execute(text("DELETE FROM transaction_tags"))
        db.execute(text(f"DELETE FROM notifications WHERE user_id = {uid}"))
        db.execute(text(f"DELETE FROM investments WHERE user_id = {uid}"))
        db.execute(text(f"DELETE FROM debts WHERE user_id = {uid}"))
        db.execute(text(f"DELETE FROM goals WHERE user_id = {uid}"))
        db.execute(text(f"DELETE FROM budgets WHERE user_id = {uid}"))
        db.execute(text(f"DELETE FROM transactions WHERE user_id = {uid}"))
        db.execute(text(f"DELETE FROM recurring_bills WHERE user_id = {uid}"))
        db.execute(text(f"DELETE FROM tags WHERE user_id = {uid}"))
        db.execute(text(f"DELETE FROM accounts WHERE user_id = {uid}"))
        db.commit()
        print("Dados anteriores removidos.")

        # ── Contas ────────────────────────────────────────────────────────────
        contas = [
            Account(user_id=uid, name="Nubank Conta", type=AccountType.checking,
                    balance=4820.50, institution="Nubank", color="#8B5CF6"),
            Account(user_id=uid, name="Caixa Poupança", type=AccountType.savings,
                    balance=12300.00, institution="Caixa Economica", color="#10B981"),
            Account(user_id=uid, name="Nubank Roxinho", type=AccountType.credit,
                    balance=-2150.80, institution="Nubank", color="#EF4444"),
            Account(user_id=uid, name="XP Investimentos", type=AccountType.investment,
                    balance=35000.00, institution="XP Investimentos", color="#F59E0B"),
            Account(user_id=uid, name="Carteira (dinheiro)", type=AccountType.cash,
                    balance=350.00, color="#6B7280"),
        ]
        for a in contas:
            db.add(a)
        db.commit()
        acc_corrente, acc_poupanca, acc_credito, acc_invest, acc_carteira = contas
        print("Contas criadas.")

        # ── Tags ──────────────────────────────────────────────────────────────
        tags_objs = [
            Tag(user_id=uid, name="Essencial", color="#EF4444"),
            Tag(user_id=uid, name="Lazer",     color="#8B5CF6"),
            Tag(user_id=uid, name="Trabalho",  color="#3B82F6"),
            Tag(user_id=uid, name="Saude",     color="#10B981"),
            Tag(user_id=uid, name="Educacao",  color="#F59E0B"),
        ]
        for t in tags_objs:
            db.add(t)
        db.commit()
        tag_essencial, tag_lazer, tag_trabalho, tag_saude, tag_educacao = tags_objs
        print("Tags criadas.")

        # ── Categorias do sistema ─────────────────────────────────────────────
        cats = {c.name: c for c in db.query(Category).filter_by(is_system=True).all()}

        # ── Recorrentes ───────────────────────────────────────────────────────
        recorrentes_def = [
            ("Netflix",              149.90, cats.get("Assinaturas"), 5),
            ("Spotify",               21.90, cats.get("Assinaturas"), 10),
            ("Academia Smart Fit",    99.90, cats.get("Saude"),       15),
            ("Aluguel",             1800.00, cats.get("Moradia"),      5),
            ("Internet Vivo",        129.99, cats.get("Servicos"),     8),
            ("Plano de Saude",       380.00, cats.get("Saude"),        1),
            ("Conta de Luz",         210.00, cats.get("Moradia"),     12),
            ("Agua e Esgoto",         85.00, cats.get("Moradia"),     20),
            ("IPTU (parcela)",        243.00, cats.get("Moradia"),    10),
            ("Escola (mensalidade)", 650.00, cats.get("Educacao"),     5),
        ]
        rb_aluguel = None
        for name, amount, cat, day in recorrentes_def:
            next_occ = date(TODAY.year, TODAY.month, day)
            if next_occ < TODAY:
                next_occ += relativedelta(months=1)
            rb = RecurringBill(
                user_id=uid,
                category_id=cat.id if cat else None,
                name=name, amount=amount,
                frequency=RecurringFrequency.monthly,
                start_date=START, next_occurrence=next_occ,
                is_active=True, days_before_reminder=3,
            )
            db.add(rb)
            if name == "Aluguel":
                rb_aluguel = rb
        db.commit()
        print(f"Recorrentes criados: {len(recorrentes_def)}")

        # ── Transações ────────────────────────────────────────────────────────
        # Coletamos (tx, [tag_ids]) para inserir transaction_tags ao final
        tx_tag_links: list[tuple] = []  # (tx_obj, [tag_id, ...])
        tx_list: list[Transaction] = []

        def add_tx(amount, tx_type, desc, cat, acc, dt,
                   status=TransactionStatus.completed, payment=None,
                   tag_ids=None, rb=None):
            t = Transaction(
                user_id=uid, account_id=acc.id,
                category_id=cat.id if cat else None,
                recurring_bill_id=rb.id if rb else None,
                amount=round(amount, 2), type=tx_type,
                description=desc, date=dt, status=status,
                payment_method=payment,
            )
            db.add(t)
            tx_list.append(t)
            if tag_ids:
                tx_tag_links.append((t, tag_ids))

        for month_start in months_range():
            m, y = month_start.month, month_start.year

            # Salário
            sd = min(date(y, m, 5), TODAY)
            add_tx(8500.00, TransactionType.income, "Salario mensal — Empresa Tech Ltda",
                   cats.get("Salario"), acc_corrente, sd,
                   payment="transferencia", tag_ids=[tag_trabalho.id])

            # Freelance trimestral
            if m in (1, 4, 7, 10):
                add_tx(random.uniform(800, 1500), TransactionType.income,
                       "Freelance — Projeto web",
                       cats.get("Freelance"), acc_corrente, rand_date(month_start),
                       payment="pix", tag_ids=[tag_trabalho.id])

            if m == 1:
                add_tx(1200.00, TransactionType.income, "13 salario (segunda parcela)",
                       cats.get("Salario"), acc_corrente, date(y, 1, 10),
                       payment="transferencia")

            # Moradia
            add_tx(1800.00, TransactionType.expense, "Aluguel",
                   cats.get("Moradia"), acc_corrente, rand_date(month_start),
                   payment="transferencia", tag_ids=[tag_essencial.id],
                   rb=rb_aluguel)
            add_tx(random.uniform(180, 260), TransactionType.expense, "Conta de luz — Enel",
                   cats.get("Moradia"), acc_corrente, rand_date(month_start),
                   payment="debito automatico", tag_ids=[tag_essencial.id])
            add_tx(random.uniform(70, 100), TransactionType.expense, "Agua e esgoto — Sabesp",
                   cats.get("Moradia"), acc_corrente, rand_date(month_start),
                   payment="debito automatico", tag_ids=[tag_essencial.id])
            add_tx(129.99, TransactionType.expense, "Internet fibra — Vivo",
                   cats.get("Servicos"), acc_corrente, rand_date(month_start),
                   payment="debito automatico", tag_ids=[tag_essencial.id])

            # Alimentação
            mercados = ["Supermercado Extra", "Carrefour", "Pao de Acucar", "Atacadao"]
            for i in range(4):
                add_tx(random.uniform(180, 350), TransactionType.expense,
                       random.choice(mercados), cats.get("Alimentacao"),
                       acc_corrente,
                       month_start + timedelta(days=i * 7 + random.randint(0, 3)),
                       payment=random.choice(["debito", "credito", "pix"]),
                       tag_ids=[tag_essencial.id])

            deliveries = ["iFood — Pizza", "iFood — Japones", "Restaurante da esquina",
                          "McDonald's", "Outback", "Bob's", "Subway", "iFood — Hamburguer"]
            for _ in range(random.randint(6, 12)):
                add_tx(random.uniform(25, 95), TransactionType.expense,
                       random.choice(deliveries), cats.get("Alimentacao"),
                       acc_credito, rand_date(month_start),
                       payment="credito", tag_ids=[tag_lazer.id])

            # Transporte
            add_tx(random.uniform(180, 240), TransactionType.expense,
                   "Combustivel — Posto Shell", cats.get("Transporte"),
                   acc_corrente, rand_date(month_start),
                   payment="debito", tag_ids=[tag_essencial.id])
            add_tx(random.uniform(50, 120), TransactionType.expense,
                   random.choice(["Uber", "99 Pop", "Estacionamento Shopping"]),
                   cats.get("Transporte"), acc_credito, rand_date(month_start),
                   payment="credito")
            if m % 3 == 0:
                add_tx(random.uniform(200, 350), TransactionType.expense,
                       "Manutencao carro — oficina", cats.get("Transporte"),
                       acc_corrente, rand_date(month_start), payment="pix")

            # Saúde
            add_tx(380.00, TransactionType.expense, "Plano de saude — Amil",
                   cats.get("Saude"), acc_corrente, rand_date(month_start),
                   payment="debito automatico", tag_ids=[tag_saude.id, tag_essencial.id])
            add_tx(99.90, TransactionType.expense, "Academia Smart Fit",
                   cats.get("Saude"), acc_corrente, rand_date(month_start),
                   payment="debito automatico", tag_ids=[tag_saude.id])
            if random.random() > 0.6:
                consultas = ["Consulta medica — clinico geral", "Dentista — manutencao",
                             "Farmacia — remedios", "Exames laboratoriais",
                             "Consulta dermatologista"]
                add_tx(random.uniform(80, 350), TransactionType.expense,
                       random.choice(consultas), cats.get("Saude"),
                       acc_credito, rand_date(month_start),
                       payment="credito", tag_ids=[tag_saude.id])

            # Educação
            add_tx(650.00, TransactionType.expense, "Escola — mensalidade filha",
                   cats.get("Educacao"), acc_corrente, rand_date(month_start),
                   payment="transferencia", tag_ids=[tag_educacao.id, tag_essencial.id])
            if random.random() > 0.5:
                cursos = ["Udemy — curso Python", "Alura — assinatura",
                          "Livro tecnico — Amazon", "Curso ingles — Duolingo Plus"]
                add_tx(random.uniform(29, 99), TransactionType.expense,
                       random.choice(cursos), cats.get("Educacao"),
                       acc_credito, rand_date(month_start),
                       payment="credito", tag_ids=[tag_educacao.id])

            # Lazer
            if random.random() > 0.4:
                eventos = ["Cinema — familia", "Show ao vivo", "Teatro municipal",
                           "Parque de diversoes", "Boliche", "Bar com amigos"]
                add_tx(random.uniform(60, 280), TransactionType.expense,
                       random.choice(eventos), cats.get("Lazer"),
                       acc_credito, rand_date(month_start),
                       payment="credito", tag_ids=[tag_lazer.id])
            if random.random() > 0.6:
                refeicoes = ["Restaurante fino — jantar especial",
                             "Hamburgeria artesanal", "Churrasco",
                             "Vinho — adega online"]
                add_tx(random.uniform(150, 600), TransactionType.expense,
                       random.choice(refeicoes), cats.get("Lazer"),
                       acc_credito, rand_date(month_start),
                       payment="credito", tag_ids=[tag_lazer.id])

            # Assinaturas
            add_tx(149.90, TransactionType.expense, "Netflix — plano familia",
                   cats.get("Assinaturas"), acc_credito, rand_date(month_start),
                   payment="credito")
            add_tx(21.90, TransactionType.expense, "Spotify Premium",
                   cats.get("Assinaturas"), acc_credito, rand_date(month_start),
                   payment="credito")
            if random.random() > 0.5:
                streaming = ["Disney+ — mensal", "HBO Max", "Amazon Prime"]
                add_tx(random.choice([45.90, 37.90, 29.90]), TransactionType.expense,
                       random.choice(streaming), cats.get("Assinaturas"),
                       acc_credito, rand_date(month_start), payment="credito")

            # Vestuário
            if random.random() > 0.6:
                roupas = ["Zara — roupas", "Renner — calcas", "C&A — camisas",
                          "Adidas — tenis running", "Hering — basicos"]
                add_tx(random.uniform(80, 450), TransactionType.expense,
                       random.choice(roupas), cats.get("Vestuario"),
                       acc_credito, rand_date(month_start), payment="credito")

            # Serviços
            if random.random() > 0.7:
                servicos = ["Cabelereiro", "Manicure", "Lavagem do carro",
                            "Faxineira mensal", "Conserto celular"]
                add_tx(random.uniform(50, 200), TransactionType.expense,
                       random.choice(servicos), cats.get("Servicos"),
                       acc_carteira, rand_date(month_start), payment="dinheiro")

            # Transferência poupança
            add_tx(500.00, TransactionType.transfer, "Transferencia para poupanca",
                   cats.get("Transferencia"), acc_corrente, rand_date(month_start),
                   payment="transferencia")

        db.commit()
        print(f"Transacoes criadas: {len(tx_list)}")

        # ── Inserir links transaction_tags (SQL direto, sem ORM) ──────────────
        tt_rows = 0
        seen = set()
        for tx_obj, tag_ids in tx_tag_links:
            for tid in tag_ids:
                key = (tx_obj.id, tid)
                if key not in seen:
                    db.execute(text(
                        f"INSERT OR IGNORE INTO transaction_tags (transaction_id, tag_id) VALUES ({tx_obj.id}, {tid})"
                    ))
                    seen.add(key)
                    tt_rows += 1
        db.commit()
        print(f"Links de tags criados: {tt_rows}")

        # ── Orçamentos (mês atual) ────────────────────────────────────────────
        mes_ini = date(TODAY.year, TODAY.month, 1)
        prox_mes = mes_ini + relativedelta(months=1) - timedelta(days=1)
        budgets_def = [
            ("Alimentacao", 1800.00), ("Transporte",  400.00),
            ("Saude",        600.00), ("Lazer",        500.00),
            ("Educacao",     800.00), ("Vestuario",    300.00),
            ("Assinaturas",  250.00), ("Servicos",     200.00),
            ("Moradia",     2300.00),
        ]
        for cat_name, amount in budgets_def:
            cat = cats.get(cat_name)
            if cat:
                db.add(Budget(user_id=uid, category_id=cat.id, amount=amount,
                              period=BudgetPeriod.monthly,
                              start_date=mes_ini, end_date=prox_mes))
        db.commit()
        print(f"Orcamentos criados: {len(budgets_def)}")

        # ── Metas ─────────────────────────────────────────────────────────────
        metas = [
            ("Reserva de emergencia", 30000.00, 18500.00, date(2026, 12, 31),
             GoalPriority.high, acc_poupanca),
            ("Viagem para Europa",    20000.00,  4200.00, date(2027, 6, 30),
             GoalPriority.medium, acc_poupanca),
            ("Trocar de carro",       55000.00,  8000.00, date(2028, 3, 1),
             GoalPriority.medium, acc_invest),
            ("MacBook Pro",           14000.00,  5500.00, date(2026, 9, 1),
             GoalPriority.low, acc_poupanca),
            ("Entrada apartamento",   80000.00, 12000.00, date(2029, 1, 1),
             GoalPriority.high, acc_invest),
        ]
        for name, target, current, tdate, priority, acc in metas:
            db.add(Goal(user_id=uid, account_id=acc.id, name=name,
                        target_amount=target, current_amount=current,
                        target_date=tdate, priority=priority))
        db.commit()
        print(f"Metas criadas: {len(metas)}")

        # ── Dívidas ───────────────────────────────────────────────────────────
        dividas = [
            ("Cartao Nubank — fatura",     2150.80, 2150.80, 12.5,
             DebtType.credit_card, date(2026, 5, 15), DebtStatus.active),
            ("Financiamento notebook",     3600.00, 2400.00, 1.99,
             DebtType.loan, date(2026, 11, 10), DebtStatus.active),
            ("Emprestimo pessoal — banco", 8000.00, 5200.00, 2.5,
             DebtType.personal, date(2027, 4, 1), DebtStatus.active),
            ("Cartao Itau — quitado",      1800.00,    0.00, 0.0,
             DebtType.credit_card, date(2026, 2, 10), DebtStatus.paid),
        ]
        for name, original, current, rate, dtype, due, status in dividas:
            db.add(Debt(user_id=uid, name=name, original_amount=original,
                        current_amount=current, interest_rate=rate,
                        type=dtype, due_date=due, status=status))
        db.commit()
        print(f"Dividas criadas: {len(dividas)}")

        # ── Investimentos ─────────────────────────────────────────────────────
        investimentos = [
            ("Tesouro Selic 2027",    15000.00, 16240.00, date(2024, 3, 15),
             InvestmentType.bond,        RiskLevel.low),
            ("CDB Inter 110% CDI",    10000.00, 10850.00, date(2024, 8, 1),
             InvestmentType.bond,        RiskLevel.low),
            ("MXRF11 — FII",           3000.00,  3180.00, date(2025, 1, 10),
             InvestmentType.real_estate, RiskLevel.medium),
            ("ITSA4 — Acoes",          2500.00,  2780.00, date(2024, 11, 5),
             InvestmentType.stock,       RiskLevel.medium),
            ("PETR4 — Acoes",          1500.00,  1320.00, date(2025, 3, 20),
             InvestmentType.stock,       RiskLevel.high),
            ("Bitcoin ETF — HASH11",    800.00,   940.00, date(2025, 2, 14),
             InvestmentType.crypto,      RiskLevel.high),
            ("Fundo Multimercado — XP", 2000.00,  2150.00, date(2024, 6, 1),
             InvestmentType.fund,        RiskLevel.medium),
        ]
        for name, amount, current_val, pdate, itype, risk in investimentos:
            db.add(Investment(user_id=uid, account_id=acc_invest.id, name=name,
                              type=itype, amount=amount, current_value=current_val,
                              purchase_date=pdate, risk_level=risk))
        db.commit()
        print(f"Investimentos criados: {len(investimentos)}")

        # ── Notificações ──────────────────────────────────────────────────────
        notifs = [
            (NotificationType.bill_reminder, "Vencimento proximo",
             "Aluguel de R$ 1.800,00 vence em 3 dias.", False),
            (NotificationType.budget_alert, "Orcamento de Alimentacao",
             "Voce ja usou 78% do orcamento de Alimentacao este mes.", False),
            (NotificationType.goal_update, "Meta: Reserva de emergencia",
             "Sua reserva de emergencia esta em 61,7% — continue assim!", True),
            (NotificationType.system, "Bem-vindo!",
             "Seus dados demo foram carregados com sucesso.", True),
            (NotificationType.transaction, "Nova transacao",
             "Salario de R$ 8.500,00 recebido em Nubank Conta.", True),
            (NotificationType.budget_alert, "Orcamento de Lazer",
             "Atencao: voce ultrapassou o orcamento de Lazer em R$ 48,00.", False),
        ]
        for ntype, title, msg, is_read in notifs:
            db.add(Notification(user_id=uid, type=ntype, title=title,
                                message=msg, is_read=is_read))
        db.commit()
        print(f"Notificacoes criadas: {len(notifs)}")

        print("\nSeed de demonstracao concluido com sucesso!")
        print(f"  Periodo coberto: {START} ate {TODAY}")
        print(f"  Total de transacoes: {len(tx_list)}")

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo()
