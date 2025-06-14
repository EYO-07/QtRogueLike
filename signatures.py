import ast,os

def extract_function_signatures(filename, output_filename):
    """
    Extracts all function and class signatures from a single Python file and writes
    them in a simplified form to an output file.

    This function uses the `ast` module to parse the source file and extract:
    - Class definitions
    - Function definitions, including arguments with default values and annotations

    It formats each signature in a readable, single-line form without body contents.

    Example Output:
        def my_function(arg1: int, arg2='default'): ...
        class MyClass:
            def method(self, value): ...

    Args:
        filename (str): The path to the source `.py` file.
        output_filename (str): The path to the output text file where the signatures will be written.

    Raises:
        SyntaxError: If the input file contains invalid Python code.

    Note:
        Only top-level and nested classes/functions are processed — inner functions inside other
        functions are not handled.
    """
    with open(filename, 'r') as f:
        source = f.read()

    tree = ast.parse(source)
    output_lines = []

    def format_args(args_obj):
        args = []
        defaults = [ast.unparse(d) for d in args_obj.defaults]
        total_defaults = len(defaults)
        positional = args_obj.args

        for i, arg in enumerate(positional):
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            if i >= len(positional) - total_defaults:
                default_value = defaults[i - (len(positional) - total_defaults)]
                arg_str += f"={default_value}"
            args.append(arg_str)

        if args_obj.vararg:
            args.append(f"*{args_obj.vararg.arg}")
        if args_obj.kwonlyargs:
            for i, arg in enumerate(args_obj.kwonlyargs):
                arg_str = arg.arg
                if arg.annotation:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                if i < len(args_obj.kw_defaults) and args_obj.kw_defaults[i]:
                    arg_str += f"={ast.unparse(args_obj.kw_defaults[i])}"
                args.append(arg_str)
        if args_obj.kwarg:
            args.append(f"**{args_obj.kwarg.arg}")

        return ", ".join(args)
    
    def visit_node(node, indent=0):
        prefix = " " * indent

        if isinstance(node, ast.FunctionDef):
            args_str = format_args(node.args)
            output_lines.append(f"{prefix}def {node.name}({args_str}): ...")

        elif isinstance(node, ast.ClassDef):
            output_lines.append(f"{prefix}class {node.name}:")
            for child in node.body:
                visit_node(child, indent + 4)

        elif isinstance(node, ast.Assign):
            # Handle multiple assignments (e.g. A = B = 5)
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    value = ast.unparse(node.value) if hasattr(ast, 'unparse') else "..."
                    output_lines.append(f"{prefix}{target.id} = {value}")

        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id.isupper():
                target = node.target.id
                value = ast.unparse(node.value) if node.value else "..."
                output_lines.append(f"{prefix}{target} = {value}")


    for node in tree.body:
        visit_node(node)

    with open(output_filename, 'w') as f:
        for line in output_lines:
            f.write(line + "\n")
            
def extract_function_signatures_from_list(filename_list, output_filename):
    """
    Extracts function and class signatures from a list of Python source files and writes
    the results into a single output file. Each section is prefixed with the source file name.

    Similar to `extract_function_signatures`, but handles multiple files. The output includes
    a heading for each file and displays:
    - Class definitions
    - Function definitions (including nested in classes)
    - Argument names, annotations, and default values

    Example Output:
        # --- From file: file1.py ---
        def foo(a: int = 10, b): ...
        class Bar:
            def baz(self): ...

        # --- From file: file2.py ---
        def another(): ...

    Args:
        filename_list (list[str]): A list of Python source file paths to parse.
        output_filename (str): The path to the output text file for the extracted signatures.

    Notes:
        - Uses the `ast.unparse()` method (Python 3.9+) to convert AST nodes back to code.
        - Files that fail to parse will include a comment in the output noting the failure.
    """
    output_lines = []
    line_sum = 0
    def format_args(args_obj):
        args = []
        defaults = [ast.unparse(d) for d in args_obj.defaults]
        total_defaults = len(defaults)
        positional = args_obj.args

        for i, arg in enumerate(positional):
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            if i >= len(positional) - total_defaults:
                default_value = defaults[i - (len(positional) - total_defaults)]
                arg_str += f"={default_value}"
            args.append(arg_str)

        if args_obj.vararg:
            args.append(f"*{args_obj.vararg.arg}")
        if args_obj.kwonlyargs:
            for i, arg in enumerate(args_obj.kwonlyargs):
                arg_str = arg.arg
                if arg.annotation:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                if i < len(args_obj.kw_defaults) and args_obj.kw_defaults[i]:
                    arg_str += f"={ast.unparse(args_obj.kw_defaults[i])}"
                args.append(arg_str)
        if args_obj.kwarg:
            args.append(f"**{args_obj.kwarg.arg}")

        return ", ".join(args)

    def visit_node(node, indent=0):
        prefix = " " * indent

        if isinstance(node, ast.FunctionDef):
            args_str = format_args(node.args)
            output_lines.append(f"{prefix}def {node.name}({args_str}): ...")

        elif isinstance(node, ast.ClassDef):
            # output_lines.append(f"{prefix}class {node.name}:")
            if node.bases:
                bases = [ast.unparse(base) for base in node.bases]
                bases_str = f"({', '.join(bases)})"
            else:
                bases_str = ""
            output_lines.append(f"{prefix}class {node.name}{bases_str}:")
            for child in node.body:
                visit_node(child, indent + 4)

        elif isinstance(node, ast.Assign):
            # Handle multiple assignments (e.g. A = B = 5)
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    value = ast.unparse(node.value) if hasattr(ast, 'unparse') else "..."
                    output_lines.append(f"{prefix}{target.id} = {value}")

        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id.isupper():
                target = node.target.id
                value = ast.unparse(node.value) if node.value else "..."
                output_lines.append(f"{prefix}{target} = {value}")

    for filename in filename_list:
        source = ""
        try:
            with open(filename, 'r') as f:
                source = f.read()
            line_count = source.count('\n') + 1
            line_sum += line_count
            output_lines.append(f"# --- From file: {filename} ({line_count} lines) ---")    
            tree = ast.parse(source)
            for node in tree.body:
                visit_node(node)
        except Exception as e:
            output_lines.append(f"# Failed to parse {filename}: {e}")
        output_lines.append("")  # Blank line between files
    output_lines.append(f"# --- TOTAL: ({line_sum} lines) ---")

    with open(output_filename, 'w') as f:
        for line in output_lines:
            f.write(line + "\n")
            
# Set working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
folder = "./"
# extraction 
extract_function_signatures_from_list([
    folder+"globals_variables.py",
    folder+"game.py",
    folder+"gui.py",
    folder+"reality.py",
    folder+"mapping.py",
    folder+"events.py",
    folder+"pyqt_layer_framework.py",
    folder+"start.pyw",
    folder+"serialization.py",
    folder+"performance.py",
    folder+"artificial_behavior.py",
    folder+"special_tiles.py"
], "_sign.py")

