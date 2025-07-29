"""
- pip install bill-flow
Example payment plugin
"""

from decimal import Decimal
from typing import List

from bill_flow import AccountData, InvoiceData, InvoiceItemData, TenantData, bill_flow


@bill_flow.payment(name="Default payment", description="Example")
def default(
    total_amount: Decimal,
    invoice: InvoiceData,
    invoice_items: List[InvoiceItemData],
    account: AccountData,
    tenant: TenantData,
) -> dict:

    print(invoice)
    print(total_amount)
    print(invoice_items)
    print(account)
    print(tenant)

    return {"amount": total_amount, "message": "ok"}
