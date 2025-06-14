"""Example plugin"""

import pluggy

__dependencies__ = ["requests>=2.0"]


hookimpl = pluggy.HookimplMarker("bill-flow")


@hookimpl
def payment(args):
    print("inside plugin 1")
    return "args"
