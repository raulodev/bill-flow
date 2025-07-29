from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from functools import wraps
from typing import Callable, List, Literal

import pluggy

hookimpl = pluggy.HookimplMarker("bill-flow")


class BillFlow:
    """
    BillFlow is a plugin manager for registering and managing payment-related plugins
    using the pluggy framework. It provides a decorator for registering payment plugins
    with metadata such as name, description, dependencies, and custom names. The class
    allows retrieval of registered plugins by type and access to all registered plugins.

    Methods:
        payment: Decorator to register a payment plugin with metadata.
        get_plugins: Retrieve all plugins registered under a specific type.
        get_all_plugins: Retrieve all registered plugins.
    """

    def __init__(self):
        self._registered_plugins = {}

    def payment(
        self,
        *,
        name: str,
        description: str = None,
        dependencies: list = None,
        custom_name: str = None,
    ):
        """
        Decorator to register a payment plugin with metadata.

        Args:
            name (str): The name of the payment plugin.
            description (str, optional): A description of the plugin.
            dependencies (list, optional): List of dependencies required by the plugin example: ["requests>=2.0"].
            custom_name (str, optional): Custom name for the plugin hook.

        Returns:
            Callable: A decorator that registers the function as a payment plugin.
        """

        dependencies = dependencies or []

        def decorator(func: Callable):

            func.meta = {
                "name": name,
                "description": description,
                "dependencies": dependencies,
                "custom_name": custom_name,
            }

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            self._register("payment", func, func.meta)

            return hookimpl(function=wrapper, specname=custom_name)

        return decorator

    def _register(self, hookname: str, func: Callable, meta: dict):
        if hookname not in self._registered_plugins:
            self._registered_plugins[hookname] = []
        self._registered_plugins[hookname].append({"func": func, "meta": meta})

    def get_plugins(self, name: Literal["payment"]):
        """
        Retrieve all plugins registered under a specific type.

        Args:
            name (Literal["payment"]): The type of plugins to retrieve.

        Returns:
            list: A list of registered plugins for the specified type.
        """
        return self._registered_plugins.get(name, [])

    def get_all_plugins(self):
        """
        Retrieve all registered plugins.

        Returns:
            dict: A dictionary containing all registered plugins grouped by type.
        """
        return self._registered_plugins


bill_flow = BillFlow()


@dataclass
class CustomFieldData:
    """Dataclass to represent custom fields"""

    name: str
    value: str


@dataclass
class ProductData:
    """Dataclass to represent products"""

    id: int
    name: str
    price: Decimal
    custom_fields: List[CustomFieldData]


@dataclass
class SubscriptionData:
    """Dataclass to represent subscriptions"""

    id: int
    custom_fields: List[CustomFieldData]


@dataclass
class InvoiceItemData:
    """Dataclass to represent invoice items"""

    id: int
    quantity: int
    amount: Decimal
    product: ProductData
    subscription: SubscriptionData


@dataclass
class AccountData:
    """Dataclass to represent accounts"""

    id: int
    tenant_id: int
    external_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    timezone: str
    credit: Decimal
    custom_fields: List[CustomFieldData]


@dataclass
class TenantData:
    """Dataclass to represent tenants"""

    id: int
    name: str
    external_id: str
    api_key: str
    custom_fields: List[CustomFieldData]


@dataclass
class InvoiceData:
    """Dataclass to represent invoices"""

    id: int
    created: datetime


@dataclass
class PaidItem:
    """Use to indicate a partial payment, for example, "
    "of all the items on the invoice, only this one was paid."""

    id: int
    amount: Decimal


class PaymentResult:
    """Use to indicate the result of a payment"""

    amount: Decimal
    message: str
    paid_items: List[PaidItem] = []
