import importlib
import os
import subprocess

import pluggy

from app.logging import log_operation

hookspec = pluggy.HookspecMarker("bill-flow")
hookimpl = pluggy.HookimplMarker("bill-flow")


@hookimpl
def setup_project(config, args):
    """This hook is used to process the initial config
    and possibly input arguments.
    """
    if args:
        config.process_args(args)

    return config


class MySpec:
    """A hook specification namespace."""

    @hookspec
    def payment(self, args) -> str:
        """Make a payment"""


def install_dependencies(dependencies: list[str], module_name: str):
    try:
        subprocess.check_call(["pip", "install", *dependencies])
        log_operation(
            operation="INSTALL DEPS",
            model="Plugins",
            status="SUCCESS",
            detail=f"Dependencies installed for plugin {module_name}",
        )

        return True
    except subprocess.CalledProcessError as e:
        log_operation(
            operation="INSTALL",
            model="Plugins",
            status="FAILED",
            detail=f"Error installing dependencies for plugin {module_name}: {e}",
            level="error",
        )

        return False


def setup_plugins():

    pm = pluggy.PluginManager("bill-flow")
    pm.add_hookspecs(MySpec)

    plugins_dir = os.path.dirname(__file__)

    for filename in os.listdir(plugins_dir):

        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"app.plugins.{filename[:-3]}"

            try:
                module = importlib.import_module(module_name)

                deps = getattr(module, "__dependencies__", None)

                deps_installed = None

                if isinstance(deps, list) and all(isinstance(d, str) for d in deps):
                    deps_installed = install_dependencies(deps, module_name)

                if deps_installed is False:
                    continue

                pm.register(module)

                log_operation(
                    operation="READ",
                    model="Plugins",
                    status="SUCCESS",
                    detail=f"Plugin {module_name} loaded",
                    level="info",
                )

            except pluggy.PluginValidationError as e:
                log_operation(
                    operation="READ",
                    model="Plugins",
                    status="FAILED",
                    detail=f"Error importing plugin {module_name}: {e}",
                    level="error",
                )

    return pm
