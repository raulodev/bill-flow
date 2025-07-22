from datetime import datetime

from dateutil.relativedelta import relativedelta

from app.database.models import (
    BillingPeriod,
    PhaseType,
    State,
    Subscription,
    TrialTimeUnit,
)
from app.subscriptions.phases import create_phases


def test_create_unlimited_trial_phase():

    start_date = datetime.now().date()

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.UNLIMITED, None, subs)

    assert billing_day is None

    assert len(phases) == 1

    assert phases[0].phase == PhaseType.TRIAL
    assert phases[0].start_date == subs.start_date
    assert phases[0].end_date == subs.end_date


def test_create_evergreen_phase():

    start_date = datetime.now().date()

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
    )

    phases, billing_day = create_phases(None, None, subs)

    assert len(phases) == 1

    assert billing_day == start_date.day

    assert phases[0].phase == PhaseType.EVERGREEN
    assert phases[0].start_date == subs.start_date
    assert phases[0].end_date == subs.end_date


def test_create_phase_with_days_trial_time():

    start_date = datetime.now().date()
    trial_days = 9

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.DAYS, trial_days, subs)

    assert len(phases) == 2

    trial_phase = phases[0]
    final_phase = phases[1]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == start_date + relativedelta(days=trial_days)

    assert final_phase.phase == PhaseType.EVERGREEN
    assert final_phase.start_date == start_date + relativedelta(days=trial_days + 1)
    assert final_phase.end_date is None

    assert billing_day == final_phase.start_date.day


def test_create_phase_with_days_trial_time_and_end_date():

    start_date = datetime.now().date()
    end_date = start_date + relativedelta(days=5)
    trial_days = 1

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.SCHEDULED_CANCELLATION,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
        end_date=end_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.DAYS, trial_days, subs)

    assert len(phases) == 2

    trial_phase = phases[0]
    final_phase = phases[1]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == start_date + relativedelta(days=trial_days)

    assert final_phase.phase == PhaseType.EVERGREEN
    assert final_phase.start_date == start_date + relativedelta(days=trial_days + 1)
    assert final_phase.end_date == end_date

    assert billing_day == final_phase.start_date.day


def test_create_phase_with_days_trial_time_and_end_date_v2():

    start_date = datetime.now().date()
    end_date = start_date + relativedelta(days=1)
    trial_days = 2

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.SCHEDULED_CANCELLATION,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
        end_date=end_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.DAYS, trial_days, subs)

    assert len(phases) == 1

    assert billing_day is None

    trial_phase = phases[0]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == end_date


def test_create_phase_with_weeks_trial_time():

    start_date = datetime.now().date()
    trial_weeks = 2
    end_date = start_date + relativedelta(weeks=trial_weeks)

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.WEEKS, trial_weeks, subs)

    assert len(phases) == 2

    trial_phase = phases[0]
    final_phase = phases[1]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == end_date

    assert final_phase.phase == PhaseType.EVERGREEN
    assert final_phase.start_date == end_date + relativedelta(days=1)
    assert final_phase.end_date is None

    assert billing_day == final_phase.start_date.day


def test_create_phase_with_weeks_trial_time_and_end_date():

    start_date = datetime.now().date()
    end_date = start_date + relativedelta(weeks=3)
    trial_weeks = 1

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.SCHEDULED_CANCELLATION,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
        end_date=end_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.WEEKS, trial_weeks, subs)

    assert len(phases) == 2

    trial_phase = phases[0]
    final_phase = phases[1]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == start_date + relativedelta(weeks=trial_weeks)

    final_phase_start_date = (
        start_date + relativedelta(weeks=trial_weeks) + relativedelta(days=1)
    )

    assert final_phase.phase == PhaseType.EVERGREEN
    assert final_phase.start_date == final_phase_start_date
    assert final_phase.end_date == end_date

    assert billing_day == final_phase_start_date.day


def test_create_phase_with_weeks_trial_time_and_end_date_v2():

    start_date = datetime.now().date()
    end_date = start_date + relativedelta(weeks=1)
    trial_weeks = 2

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.SCHEDULED_CANCELLATION,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
        end_date=end_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.WEEKS, trial_weeks, subs)

    assert len(phases) == 1

    assert billing_day is None

    trial_phase = phases[0]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == end_date


def test_create_phase_with_months_trial_time():

    start_date = datetime.now().date()
    trial_months = 2
    end_date = start_date + relativedelta(months=trial_months)

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.MONTHS, trial_months, subs)

    assert len(phases) == 2

    trial_phase = phases[0]
    final_phase = phases[1]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == end_date

    assert final_phase.phase == PhaseType.EVERGREEN
    assert final_phase.start_date == end_date + relativedelta(days=1)
    assert final_phase.end_date is None

    assert billing_day == final_phase.start_date.day


def test_create_phase_with_months_trial_time_and_end_date():

    start_date = datetime.now().date()
    end_date = start_date + relativedelta(months=3)
    trial_months = 1

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.SCHEDULED_CANCELLATION,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
        end_date=end_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.MONTHS, trial_months, subs)

    assert len(phases) == 2

    trial_phase = phases[0]
    final_phase = phases[1]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == start_date + relativedelta(months=trial_months)

    final_phase_start_date = (
        start_date + relativedelta(months=trial_months) + relativedelta(days=1)
    )

    assert final_phase.phase == PhaseType.EVERGREEN
    assert final_phase.start_date == final_phase_start_date
    assert final_phase.end_date == end_date

    assert billing_day == final_phase_start_date.day


def test_create_phase_with_months_trial_time_and_end_date_v2():

    start_date = datetime.now().date()
    end_date = start_date + relativedelta(months=1)
    trial_months = 2

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.SCHEDULED_CANCELLATION,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
        end_date=end_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.MONTHS, trial_months, subs)

    assert len(phases) == 1

    assert billing_day is None

    trial_phase = phases[0]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == end_date


def test_create_phase_with_years_trial_time():

    start_date = datetime.now().date()
    trial_years = 2
    end_date = start_date + relativedelta(years=trial_years)

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.ACTIVE,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.YEARS, trial_years, subs)

    assert len(phases) == 2

    trial_phase = phases[0]
    final_phase = phases[1]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == end_date

    assert final_phase.phase == PhaseType.EVERGREEN
    assert final_phase.start_date == end_date + relativedelta(days=1)
    assert final_phase.end_date is None

    assert billing_day == final_phase.start_date.day


def test_create_phase_with_years_trial_time_and_end_date():

    start_date = datetime.now().date()
    end_date = start_date + relativedelta(years=3)
    trial_years = 1

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.SCHEDULED_CANCELLATION,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
        end_date=end_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.YEARS, trial_years, subs)

    assert len(phases) == 2

    trial_phase = phases[0]
    final_phase = phases[1]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == start_date + relativedelta(years=trial_years)

    final_phase_start_date = (
        start_date + relativedelta(years=trial_years) + relativedelta(days=1)
    )

    assert final_phase.phase == PhaseType.EVERGREEN
    assert final_phase.start_date == final_phase_start_date
    assert final_phase.end_date == end_date

    assert billing_day == final_phase_start_date.day


def test_create_phase_with_years_trial_time_and_end_date_v2():

    start_date = datetime.now().date()
    end_date = start_date + relativedelta(years=1)
    trial_years = 2

    subs = Subscription(
        billing_period=BillingPeriod.BIANNUAL,
        account_id=1,
        state=State.SCHEDULED_CANCELLATION,
        external_id="external_id_abcd",
        tenant_id=1,
        start_date=start_date,
        end_date=end_date,
    )

    phases, billing_day = create_phases(TrialTimeUnit.YEARS, trial_years, subs)

    assert len(phases) == 1

    assert billing_day is None

    trial_phase = phases[0]

    assert trial_phase.phase == PhaseType.TRIAL
    assert trial_phase.start_date == start_date
    assert trial_phase.end_date == end_date
