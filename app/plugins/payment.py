"""
Example plugin

Description of __setup__:

name (optional): Name to use to identify a payment method in the system, default value is the module name

specname: It should be used when there are several payment methods default value is "payment" .For
        example, if you define two payment methods , one to pay with Stripe and the other with BigCommerce

```python
# stripe_payment_plugin.py
# Plugin Stripe
__setup__ = {
    "name": "Payment with Stripe",
    "specname": "stripe_payment",
}
```

```python
# bc_payment_plugin.py
# Plugin BigCommerce
__setup__ = {
    "name": "Payment with BigCommerce",
    "specname": "bigcommerce_payment",
}
```

dependencies (optional): List of dependencies that the plugin uses
"""

import pluggy


__setup__ = {
    "name": "Default Payment",
    "description": "Default payment plugin",
    "dependencies": [],  # example: ["requests>=2.0"]
}


hookimpl = pluggy.HookimplMarker("bill-flow")


@hookimpl(specname=__setup__.get("specname"))
def payment(*args, **kwargs):
    print("inside example plugin")
    return "Hello"
