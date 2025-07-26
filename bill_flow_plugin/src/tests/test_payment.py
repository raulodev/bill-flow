from bill_flow import bill_flow
import sys


@bill_flow.payment(name="Test Payment")
def payment():
    return "payment"


@bill_flow.payment(name="Test Payment 2", custom_name="custom_name")
def payment2():
    return "payment custom name"


def test_register_plugin(plugin_manager):

    plugin_manager.register(sys.modules[__name__])

    results = plugin_manager.hook.payment()

    assert results == ["payment"]


def test_register_plugin_with_custom_name(plugin_manager):

    plugin_manager.register(sys.modules[__name__])

    results = plugin_manager.hook.custom_name()

    assert results == ["payment custom name"]


def test_get_metadatas(plugin_manager):

    plugin_manager.register(sys.modules[__name__])

    hookcallers = plugin_manager.get_hookcallers(sys.modules[__name__])

    for hookcaller in hookcallers:

        if hookcaller.name == "payment":
            meta = hookcaller.get_hookimpls()[0].function.meta

            assert meta["name"] == "Test Payment"
            assert meta["description"] is None
            assert meta["dependencies"] == []
            assert meta["custom_name"] is None

        elif hookcaller.name == "custom_name":
            meta = hookcaller.get_hookimpls()[0].function.meta

            assert meta["name"] == "Test Payment 2"
            assert meta["description"] is None
            assert meta["dependencies"] == []
            assert meta["custom_name"] == "custom_name"


def test_get_plugins():

    module = sys.modules[__name__]

    assert len(module.bill_flow.get_plugins("payment")) == 2
