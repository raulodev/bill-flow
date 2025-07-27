import pytest
import pluggy


@pytest.fixture()
def plugin_manager():
    return pluggy.PluginManager("bill-flow")
