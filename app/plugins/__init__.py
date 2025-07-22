import importlib
import os
import subprocess

import pluggy
from sqlmodel import Session, select

from app.database.deps import engine
from app.database.models import Plugin
from app.logging import log_operation

plugin_manager = pluggy.PluginManager("bill-flow")


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


def register_plugin(module_name: str, setup: dict):

    with Session(engine) as session:

        plugin_db = session.exec(
            select(Plugin).where(Plugin.module == module_name)
        ).first()

        if not plugin_db:
            plugin_db = Plugin(
                name=setup.get("name", module_name),
                module=module_name,
                specname=setup.get("specname"),
                description=setup.get("description"),
            )

            session.add(plugin_db)

            log_operation(
                operation="CREATE",
                model="Plugin",
                status="SUCCESS",
                detail=f"Plugin {module_name} loaded",
            )

        else:
            plugin_db.name = setup.get("name", module_name)
            plugin_db.specname = setup.get("specname")

            log_operation(
                operation="UPDATE",
                model="Plugin",
                status="SUCCESS",
                detail=f"Plugin {module_name} loaded",
            )

        session.commit()


IGNORE_FILES = ["__init__.py", "api.py"]


def setup_plugins():

    plugins_dir = os.path.dirname(__file__)

    for filename in os.listdir(plugins_dir):

        if filename.endswith(".py") and filename not in IGNORE_FILES:
            module_name = f"app.plugins.{filename[:-3]}"

            try:
                module = importlib.import_module(module_name)

                setup = getattr(module, "__setup__", {})

                plugin_deps = setup.get("dependencies")

                deps_installed = None

                if (
                    plugin_deps
                    and isinstance(plugin_deps, list)
                    and all(isinstance(d, str) for d in plugin_deps)
                ):

                    deps_installed = install_dependencies(plugin_deps, module_name)

                if deps_installed is False:
                    continue

                plugin_manager.register(module)

                register_plugin(module_name, setup)

            except pluggy.PluginValidationError as e:
                log_operation(
                    operation="READ",
                    model="Plugins",
                    status="FAILED",
                    detail=f"Error importing plugin {module_name}: {e}",
                    level="error",
                )
