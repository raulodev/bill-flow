"""
- pip install bill-flow
Example payment plugin
"""

from decimal import Decimal
from typing import List

from bill_flow import bill_flow


@bill_flow.payment(name="Default payment", description="Example")
def default(
    invoice_id: int,
    total_amount: Decimal,
    invoice_items: List[dict],
    account: dict,
    tenant: dict,
):

    print(invoice_id)
    print(total_amount)
    print(invoice_items)
    print(account)
    print(tenant)

    return total_amount
