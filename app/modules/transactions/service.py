from app.models.models import Account, TransactionType


def apply_to_balance(account: Account, amount: float, ttype: TransactionType, reverse: bool = False) -> None:
    factor = -1.0 if reverse else 1.0
    if ttype == TransactionType.income:
        account.balance += amount * factor
    elif ttype == TransactionType.expense:
        account.balance -= amount * factor
    # transfer: não altera (tratado na rota de transferência)
