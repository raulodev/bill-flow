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

IGNORE_FILES = ["__init__.py", "__pycache__"]


def install_plugins_dependencies(dependencies: list[str], module_name: str):
    """Install dependencies for a plugin."""
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
    """Register a plugin in the database."""

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
    """Check if the file should be skipped based on its name."""
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
    """Setup plugins by importing them and processing their functions."""

    plugins_dir = os.path.dirname(__file__).replace("app/plugins", "plugins")

    for filename in os.listdir(plugins_dir):

        if should_skip_file(filename):
            log_operation(
                operation="READ",
                model="Plugin",
                status="SKIPPED",
                detail=f"Skipping file {filename}",
            )
            continue

        module_name = f"plugins.{filename[:-3]}".replace("/", ".")

        try:
            module = importlib.import_module(module_name)

            if not hasattr(module, "bill_flow"):
                log_operation(
                    operation="READ",
                    model="Plugin",
                    status="FAILED",
                    detail=f"Plugin {module_name} does not have a 'bill_flow' attribute.",
                    level="warning",
                )
                continue

            process_plugin_module(module, install_plugin_deps, save_in_db)

        except (pluggy.PluginValidationError, ValueError) as e:
            log_operation(
                operation="READ",
                model="Plugins",
                status="FAILED",
                detail=f"Error importing plugin {module_name}: {e}",
                level="warning",
            )
