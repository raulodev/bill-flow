import importlib
import os
import subprocess
from typing import List

import pluggy
from sqlmodel import Session, select

from app.database.deps import engine
from app.database.models import Plugin
from app.logging import log_operation

plugin_manager = pluggy.PluginManager("bill-flow")

IGNORE_FILES = ["__init__.py", "api.py", "setup.py"]


def install_plugins_dependencies(dependencies: list[str], module_name: str):
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


def register_plugin_in_database(module_name: str, function_name: str, meta: dict):

    with Session(engine) as session:

        path = f"{module_name}.{function_name}"

        plugin_db = session.exec(select(Plugin).where(Plugin.path == path)).first()

        if not plugin_db:

            plugin_db = Plugin(
                name=meta.get("name"),
                path=path,
                hook_caller=meta.get("custom_name") or function_name,
                description=meta.get("description"),
            )

            session.add(plugin_db)

            log_operation(
                operation="CREATE",
                model="Plugin",
                status="SUCCESS",
                detail=f"Plugin {path} loaded",
            )

        else:
            plugin_db.name = meta.get("name")
            plugin_db.hook_caller = meta.get("custom_name") or function_name
            plugin_db.description = meta.get("description")

            log_operation(
                operation="UPDATE",
                model="Plugin",
                status="SUCCESS",
                detail=f"Plugin {path} loaded",
            )

        session.commit()


def should_skip_file(filename: str) -> bool:
    return not filename.endswith(".py") or filename in IGNORE_FILES


def process_plugin_module(module, install_plugin_deps: bool = True, save_in_db=True):

    plugin_manager.register(module)

    plugins: List[dict] = module.bill_flow.get_all_plugins()

    for functions in plugins.values():

        for function in functions:

            if install_plugin_deps:

                deps_installed = None

                plugin_deps = function.get("meta", {}).get("dependencies")

                if (
                    plugin_deps
                    and isinstance(plugin_deps, list)
                    and all(isinstance(d, str) for d in plugin_deps)
                ):

                    deps_installed = install_plugins_dependencies(
                        plugin_deps, module.__name__
                    )

                if deps_installed is False:
                    continue

            if save_in_db:
                register_plugin_in_database(
                    module.__name__,
                    function.get("func").__name__,
                    function.get("meta", {}),
                )


def setup_plugins(install_plugin_deps=True, save_in_db=True):

    plugins_dir = os.path.dirname(__file__)

    for filename in os.listdir(plugins_dir):

        if should_skip_file(filename):
            continue

        module_name = f"app.plugins.{filename[:-3]}"

        try:
            module = importlib.import_module(module_name)

            if not hasattr(module, "bill_flow"):
                continue

            process_plugin_module(module, install_plugin_deps, save_in_db)

        except pluggy.PluginValidationError as e:
            log_operation(
                operation="READ",
                model="Plugins",
                status="FAILED",
                detail=f"Error importing plugin {module_name}: {e}",
                level="error",
            )
