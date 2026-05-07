from datetime import date

from dateutil.relativedelta import relativedelta

from app.models.models import RecurringFrequency


def calc_next_occurrence(current: date, frequency: RecurringFrequency) -> date:
    if frequency == RecurringFrequency.daily:
        return current + relativedelta(days=1)
    elif frequency == RecurringFrequency.weekly:
        return current + relativedelta(weeks=1)
    elif frequency == RecurringFrequency.monthly:
        return current + relativedelta(months=1)
    elif frequency == RecurringFrequency.quarterly:
        return current + relativedelta(months=3)
    elif frequency == RecurringFrequency.yearly:
        return current + relativedelta(years=1)
    return current
