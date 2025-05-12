# overview.pyw - standalone window to view the project code 

# third-party 
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor

# project 
from pyqt_layer_framework import *
from gui import * 
from serialization import *

# built-in 
import ast,os, sys

def new_list_widget(callback = None, get_filtered_event_from = None):
    list_widget = QListWidget()
    list_widget.setStyleSheet("""
        QListWidget {
            background-color: rgba(0, 0, 0, 150);
            color: white;
            border: 1px solid rgba(255, 255, 255, 50);
            border-radius: 5px;
            padding: 5px;
            font-size: 12px;
            font-weight: bold;
        }
        QListWidget::item:selected {
            background-color: rgba(255, 255, 255, 20);
            color: cyan; 
        }
    """)
    list_widget.setSelectionMode(QListWidget.SingleSelection)
    list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
    list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    if callback: list_widget.itemDoubleClicked.connect(callback)
    if get_filtered_event_from: list_widget.installEventFilter(get_filtered_event_from) # now the list_widget will use the keyPressEvent function 
    return list_widget

def extract_function_signatures(filename):
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
                bases_str = f" ( {', '.join(bases)} )"
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

    output_lines = []
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
    return output_lines
    
class Overview(Widget, Serializable):
    __serialize_only__ = ["window_width", "window_height"]
    def __init__(self):
        Widget.__init__(self)
        Serializable.__init__(self)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.75)
        self.setWindowTitle("Project Overview")
        self.setFocusPolicy(Qt.StrongFocus)  # Ensure Game accepts focus
        self.setWindowTitle("Project Overview")
        self.window_width = 600
        self.window_height = 700
        self.Load_JSON("overview.ini")
        self.resize(self.window_width, self.window_height)
        self.build_parts()
        self.assemble_parts()
        # --
        self.collapsables = {}
        # --
        self.update()
    def resizeEvent(self, event):
        # This method is called whenever the window is resized
        rect = self.geometry()
        self.window_width = rect.width()
        self.window_height = rect.height()
        super().resizeEvent(event)  # Make sure to call the base class implementation    
    def closeEvent(self, event):
        """Save the game state when the window is closed."""
        try:
            self.Save_JSON("overview.ini")
        except Exception as e:
            print(f"Error saving game on exit: {e}")
        event.accept()
    def build_parts(self):
        self.layer = VLayout()
        self.tabs = new_tab_bar("start.pyw", self.update)
        self.tabs.addTab("globals_variables.py")
        self.tabs.addTab("game.py")
        self.tabs.addTab("gui.py")
        self.tabs.addTab("reality.py")
        self.tabs.addTab("mapping.py")
        self.tabs.addTab("pyqt_layer_framework.py")
        self.tabs.addTab("serialization.py")
        self.tabs.addTab("performance.py")
        self.tabs.addTab("overview.pyw")
        self.list_widget = new_list_widget(self.double_click)
        self.base_text_button = "Copy to Clipboard"
        self.button = new_button(self.base_text_button, self.copy_to_clipboard)
    def assemble_parts(self):
        self / (self.layer / self.tabs / self.list_widget / self.button)
    def set_item_color(self, text):
        if "add_" in text: return QColor(255,150,150,255)
        if "is_" in text: return QColor(150,150,255,255)
        if "can_" in text: return QColor(150,150,255,255)
        if "get_" in text: return QColor("orange")
        if "set_" in text: return QColor("orange")
        if "update" in text: return QColor(0,255,0,255)
        if "__" in text: return QColor("magenta")
        if "_" in text and text[0]=="_": return QColor("gray")
        if ("class" in text) and (not "def" in text): return QColor("yellow")
        if "#" in text: return QColor(0,255,0,255)
        return QColor("white")
    def process_item_text(self, text):
        if "def" in text and text[:3]=="def":            
            return text.replace("def "," ").replace(": ...",""), True
        if "def" in text:
            return text.replace("def "," ").replace(": ...",""), False
        if "class" in text:
            return text.replace("class ","").replace(":",""), True
        else:
            return text, True
    def update(self, index = None):
        text = None
        if not index: 
            text = "start.pyw"
        else: 
            text = self.tabs.tabText(index)
        self.list_widget.clear()
        if not text: return 
        idx = 0
        list_collapsable = []
        self.collapsables.clear()
        ext = extract_function_signatures(text)
        for item in ext:
            proc_text, b_is_pivot = self.process_item_text(item)
            if b_is_pivot:
                if len(list_collapsable)>0:
                    self.collapsables.update({ tuple(list_collapsable) : True })
                    list_collapsable.clear()
            list_collapsable.append(idx)
            self.list_widget.addItem( proc_text )
            item_widget = self.list_widget.item(idx)
            item_widget.setForeground( self.set_item_color(item) )
            # --
            idx += 1
            if idx == len(ext):
                self.collapsables.update({ tuple(list_collapsable) : True })
                list_collapsable.clear()
        for k,v in self.collapsables.items():
            b_first = True
            for idx in k:
                item = self.list_widget.item(idx)
                if not item: continue 
                if b_first:
                    item.setHidden(False)
                    b_first = False
                    continue 
                item.setHidden(v)
    def double_click(self, item = None):
        if not item: item = self.list_widget.currentItem()
        idx = self.list_widget.currentRow()
        def change_state(index, tpl):
            if index == idx: return tpl 
            return None 
        iterab = self.foreach_pivot( change_state )
        if not iterab: 
            self.copy_to_clipboard()
            return 
        self.collapsables[iterab] = not self.collapsables[iterab]
        b_first = True
        for k in iterab:
            item = self.list_widget.item(k)
            if b_first:
                item.setHidden(False)
                b_first = False
                continue 
            item.setHidden(self.collapsables[iterab])
    def foreach_pivot(self, inner_function, **kwargs):
        for k,v in self.collapsables.items():
            result = inner_function(k[0], k, **kwargs)
            if result == None:
                continue 
            else:
                if result == True: 
                    return 
                else:
                    return result 
    def copy_to_clipboard(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            text = selected_items[0].text()            
            clipboard = QApplication.clipboard()
            clipboard.setText(text.lstrip().rstrip())
            self.button.setText( self.base_text_button+f"( {text.lstrip().rstrip()} )" )
    
# --- Entry Point 

# Set working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    obj = Overview()
    obj.show()
    sys.exit(app.exec_()) 

# -- END     