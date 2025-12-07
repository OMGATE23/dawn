# tools/__init__.py
import pkgutil
import importlib
import inspect
from typing import List
from .base import BaseTool

available_tools: List[BaseTool] = []

for loader, module_name, is_pkg in pkgutil.iter_modules(__path__):

    if module_name == 'base':
        continue

    module = importlib.import_module(f'.{module_name}', __package__)

    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:

            if getattr(obj, 'active', True):
                available_tools.append(obj)
