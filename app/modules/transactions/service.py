from decimal import Decimal

from app.models.models import Account, TransactionType


def apply_to_balance(account: Account, amount: Decimal, ttype: TransactionType, reverse: bool = False) -> None:
    factor = Decimal("-1") if reverse else Decimal("1")
    if ttype == TransactionType.income:
        account.balance += amount * factor
    elif ttype == TransactionType.expense:
        account.balance -= amount * factor
    # transfer: não altera (tratado na rota de transferência)
