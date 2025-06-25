from app.subscriptions.billing_day import billing_day
from app.database.models import BillingPeriod


def test_billing_day():

    bd1 = billing_day(BillingPeriod.MONTHLY, 5)
    bd2 = billing_day(BillingPeriod.QUARTERLY, 5)
    bd3 = billing_day(BillingPeriod.BIANNUAL, 5)
    bd4 = billing_day(BillingPeriod.ANNUAL, 5)
    bd5 = billing_day(BillingPeriod.SESQUIENNIAL, 5)
    bd6 = billing_day(BillingPeriod.BIENNIAL, 5)
    bd7 = billing_day(BillingPeriod.TRIENNIAL, 5)

    assert all([bd1, bd2, bd3, bd4, bd5, bd6, bd7]) is True


def test_billing_day_none():

    bd1 = billing_day(BillingPeriod.DAILY, 5)
    bd2 = billing_day(BillingPeriod.WEEKLY, 5)
    bd3 = billing_day(BillingPeriod.BIWEEKLY, 5)
    bd4 = billing_day(BillingPeriod.THIRTY_DAYS, 5)
    bd5 = billing_day(BillingPeriod.THIRTY_ONE_DAYS, 5)

    assert all([bd1, bd2, bd3, bd4, bd5]) is False
