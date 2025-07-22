from app.database.models import BillingPeriod


def get_billing_day(biiling_period: BillingPeriod, day: int):
    """
    Billing day only applies to subscriptions
    whose recurring term is month based -- e.g MONTHLY, ANNUAL, ..

    Args:
        biiling_period (BillingPeriod):
        day (int):
    """

    if biiling_period in [
        BillingPeriod.DAILY,
        BillingPeriod.WEEKLY,
        BillingPeriod.BIWEEKLY,
        BillingPeriod.THIRTY_DAYS,
        BillingPeriod.THIRTY_ONE_DAYS,
    ]:

        return None

    return day
