from typing import List, Literal, Tuple

from dateutil.relativedelta import relativedelta

from app.database.models import (
    PhaseType,
    Subscription,
    SubscriptionPhase,
    TrialTimeUnit,
)
from app.subscriptions.billing_day import get_billing_day


def create_phases(
    trial_time_unit: Literal[
        TrialTimeUnit.UNLIMITED,
        TrialTimeUnit.DAYS,
        TrialTimeUnit.WEEKS,
        TrialTimeUnit.MONTHS,
        TrialTimeUnit.YEARS,
    ],
    trial_time: int,
    subscription: Subscription,
) -> Tuple[List[SubscriptionPhase], int | None]:
    """Create subscription phases

    Args:
        trial_time_unit (TrialTimeUnit)
        trial_time (int)
        subscription (Subscription)
    """

    phases = []
    billing_day = None

    if trial_time_unit == TrialTimeUnit.UNLIMITED:
        initial_phase = SubscriptionPhase(
            phase=PhaseType.TRIAL,
            tenant_id=subscription.tenant_id,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
        )
        phases.append(initial_phase)

    elif trial_time_unit in (
        TrialTimeUnit.DAYS,
        TrialTimeUnit.WEEKS,
        TrialTimeUnit.MONTHS,
        TrialTimeUnit.YEARS,
    ):

        trial_time_unit_mapping = {
            TrialTimeUnit.DAYS: "days",
            TrialTimeUnit.WEEKS: "weeks",
            TrialTimeUnit.MONTHS: "months",
            TrialTimeUnit.YEARS: "years",
        }

        time_unit = trial_time_unit_mapping.get(trial_time_unit)

        end_date_trial_phase = subscription.start_date + relativedelta(
            **{time_unit: trial_time}
        )

        if subscription.end_date and subscription.end_date < end_date_trial_phase:
            end_date_trial_phase = subscription.end_date

        trial_phase = SubscriptionPhase(
            phase=PhaseType.TRIAL,
            tenant_id=subscription.tenant_id,
            start_date=subscription.start_date,
            end_date=end_date_trial_phase,
        )

        phases.append(trial_phase)

        start_date_final_phase = end_date_trial_phase + relativedelta(days=1)

        if (
            subscription.end_date
            and subscription.end_date > start_date_final_phase
            or not subscription.end_date
        ):

            final_phase = SubscriptionPhase(
                phase=PhaseType.EVERGREEN,
                tenant_id=subscription.tenant_id,
                start_date=start_date_final_phase,
                end_date=subscription.end_date,
            )

            phases.append(final_phase)

            billing_day = get_billing_day(
                subscription.billing_period, start_date_final_phase.day
            )

    else:

        initial_phase = SubscriptionPhase(
            phase=PhaseType.EVERGREEN,
            tenant_id=subscription.tenant_id,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
        )
        phases.append(initial_phase)

        billing_day = get_billing_day(
            subscription.billing_period, subscription.start_date.day
        )

    return phases, billing_day
