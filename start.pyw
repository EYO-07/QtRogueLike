# start.pyw

# built-in
import os, sys, re, ast
import importlib.util

restricted_modules = {
    'os', 'sys', 'subprocess', 'shutil', 'socket', 'pathlib',
    'multiprocessing', 'threading', 'ctypes', 'inspect', 'platform',
    'builtins', 'importlib', 'tempfile', 'resource', 'psutil'
}
restricted_builtins = {
    'eval', 'exec', 'compile', '__import__', 'globals', 'locals',
    'vars', 'open', 'input', 'dir', 'delattr', 'setattr', 'getattr'
}
alias_map = {}

def add_alias(alias, root):
    if alias.asname:
        alias_map[alias.asname] = root
    else:
        alias_map[alias.name] = root
def is_node_import_restricted(node):
    if isinstance(node, ast.Import):
        for alias in node.names:
            root = alias.name.split('.')[0]
            if root in restricted_modules:
                return True
            add_alias(alias, root)
    elif isinstance(node, ast.ImportFrom):
        if node.module:
            root = node.module.split('.')[0]
            if root in restricted_modules:
                return True
            for alias in node.names:
                add_alias(alias, root)
    return False
def is_node_call_restricted(node):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in restricted_builtins:
                return True
    return False
def is_node_attr_restricted(node):
    if isinstance(node, ast.Attribute):
        # Drill down the attribute chain to get the root name
        current = node
        while isinstance(current, ast.Attribute):
            current = current.value
        if isinstance(current, ast.Name):
            root_name = current.id
            real_name = alias_map.get(root_name, root_name)
            if real_name in restricted_modules:
                return True
    return False
def is_node_dynamic_import(node):
    if isinstance(node, ast.Call):
        # Check for getattr(__import__('os'), ...)
        if isinstance(node.func, ast.Name) and node.func.id == 'getattr':
            if len(node.args) >= 1:
                arg = node.args[0]
                if (isinstance(arg, ast.Call) and
                    isinstance(arg.func, ast.Name) and
                    arg.func.id == '__import__' and
                    len(arg.args) >= 1):

                    # Check if importing a restricted module
                    import_arg = arg.args[0]
                    if isinstance(import_arg, ast.Str):
                        if import_arg.s.split('.')[0] in restricted_modules:
                            return True
    return False
def is_node_string_injection_with_dynamic_import(node):
    """
    Detects restricted calls containing dynamic imports of restricted modules in their string arguments.
    """
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in restricted_builtins:
            if node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Str):
                    payload = arg.s
                    for mod in restricted_modules:
                        if f"__import__('{mod}')" in payload or f'__import__("{mod}")' in payload:
                            return True
    return False

def is_module_safe(path):
    """
    Check if a Python module is safe by detecting restricted imports and built-in calls.

    :param path: Path to the Python source file.
    :return: True if safe, False otherwise.
    """
    alias_map = {}
    source = None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        if not source: return False
        # & node : tree || Check for Restricted Imports | Check for Restricted Built-ins 
        tree = ast.parse(source, filename=path)
        for node in ast.walk(tree):
            # Check for Restricted Imports
            if is_node_import_restricted(node): 
                print("... this module isn't safe, restricted modules encountered")
                return False
            if is_node_call_restricted(node): 
                print("... this module isn't safe, restricted calls encountered")
                return False
            if is_node_attr_restricted(node):
                print("... this module isn't safe, restricted attribute access encountered")
                return False
            if is_node_dynamic_import(node):
                print("... this module isn't safe, dynamic import of restricted module detected")
                return False
            if is_node_string_injection_with_dynamic_import(node):
                print("... this module isn't safe, string injection with dynamic import detected")
                return False    
        print("... mod basic safety check - ok")
        return True 
    except (SyntaxError, FileNotFoundError, OSError) as e:
        print(f"Error parsing module: {e}")
        return False
    
def import_module_from_path(path, module_name=None):
    """
    Dynamically imports a Python module from a given file path.

    :param path: Full path to the .py file.
    :param module_name: Optional name to assign to the module. Defaults to the filename without extension.
    :return: The imported module object.
    """
    if not os.path.exists(path): raise FileNotFoundError(f"No such file: {path}")
    if module_name is None: module_name = os.path.splitext(os.path.basename(path))[0]
    if not is_module_safe(path): return None
    # -- 
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# project
from game import Game

# third-party
from PyQt5.QtWidgets import QApplication

# Set working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
mod_dir = "./mods"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    game_instance = Game()
    mods_filenames = [ os.path.join(mod_dir, f) for f in os.listdir(mod_dir) if re.search( "\\.py", f ) ]
    for f in mods_filenames:
        print("Loading Mod: ", f)
        mod = import_module_from_path(f)
        if mod: 
            if mod.Entry:
                mod.Entry(game_instance)
    game_instance.show()
    sys.exit(app.exec_())

# --- END 






























