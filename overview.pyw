# overview.pyw - standalone window to view the project code 

# built-in 
import tempfile, shutil, os, json, ast, sys, threading, time, re
from pathlib import Path
from collections import defaultdict
# third-party
from PyQt5.QtWidgets import QApplication, QWidget, QListWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMenu, QDialog, QLabel, QTextEdit, QSizePolicy, QInputDialog, QLayout, QTabBar
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QTextCursor, QColor
# Set working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
pattern_py = re.compile(r'.*\.py$', re.IGNORECASE)
pattern_pyw = re.compile(r'.*\.pyw$', re.IGNORECASE)

# -- performance
def tic():
    """
    Start a high-resolution timer.

    Returns:
        float: The current value of a high-precision performance counter,
               suitable for measuring short durations with `toc()`.

    Example:
        >>> t0 = tic()
        >>> # ... code to profile ...
        >>> toc(t0, "Section A")
    """
    return time.perf_counter()
def toc(initial, message = "", t_bound = 0.25):
    """
    Measure and optionally print the elapsed time since `initial`.

    Args:
        initial (float): Start time, typically obtained from `tic()`.
        message (str, optional): Message to prepend in the output. Defaults to "".
        t_bound (float, optional): Minimum duration in seconds required to print output.
                                   Prevents logging trivial timings. Defaults to 0.1.

    Returns:
        None

    Example:
        >>> t0 = tic()
        >>> heavy_computation()
        >>> toc(t0, "Computation done")  # prints if elapsed time > 0.1s

    Output (example):
        Computation done dt = 0.347
    """
    dt = time.perf_counter() - initial
    if dt < t_bound: return 
    print(f"{message} dt = {dt:.3f}")

# -- helper functions for widgets
def color_to_css(foreground):
    if isinstance(foreground, QColor):
        return foreground.name(QColor.HexArgb) if foreground.alpha() < 255 else foreground.name()
    elif isinstance(foreground, str):
        return foreground  # assume it's a valid CSS color string
    return "white"  # default fallback
def set_relative_horizontal_position(widget, widget_reference, side = "right", gap = 10):
    if not widget or not widget_reference: return     
    # -- 
    ref_pos = widget_reference.mapToGlobal(widget_reference.rect().topLeft())
    ref_width = widget_reference.width()
    ref_height = widget_reference.height()
    _width = widget.width()
    _height = widget.height()
    # --
    x = 0
    match side:
        case "right":
            x = ref_pos.x() + ref_width + gap 
        case "left":
            x = ref_pos.x() - _width - gap
        case _:
            raise ValueError(f"Unsupported side: {side}")    
    y = ref_pos.y() + (ref_height - _height) // 2 # Vertical centering
    widget.move(x, y)
def set_relative_vertical_position(widget, widget_reference, side = "down", gap = 5):
    if not widget or not widget_reference: return     
    # -- 
    ref_pos = widget_reference.mapToGlobal(widget_reference.rect().topLeft())
    ref_width = widget_reference.width()
    ref_height = widget_reference.height()   
    _width = widget.width()
    _height = widget.height()
    # -- 
    x = ref_pos.x() + (ref_width - _width) // 2
    y = 0
    match side:
        case "down":
            y = ref_pos.y() + ref_height + gap 
        case "top":
            y = ref_pos.y() - _height - gap
        case _:
            raise ValueError(f"Unsupported side: {side}")
    widget.move(x, y)
def set_text_cursor_to(text_widget, position = QTextCursor.End):
    cursor = text_widget.textCursor()
    cursor.movePosition(position)
    text_widget.setTextCursor(cursor)
    text_widget.ensureCursorVisible()
def apply_filter_to_list_widget(list_widget, text):
    for index in range(list_widget.count()):
        item = list_widget.item(index)
        item.setHidden(text.lower() not in item.text().lower())

# -- helper classes for widgets
class VLayout(QVBoxLayout):
    def __truediv__(self, other):
        if isinstance(other, QWidget):
            self.addWidget(other)
        elif isinstance(other, QLayout):
            self.addLayout(other)
        else:
            raise TypeError(f"Cannot divide layout by object of type {type(other).__name__}")
        return self
class HLayout(QHBoxLayout):
    def __truediv__(self, other):
        if isinstance(other, QWidget):
            self.addWidget(other)
        elif isinstance(other, QLayout):
            self.addLayout(other)
        else:
            raise TypeError(f"Cannot divide layout by object of type {type(other).__name__}")
        return self
class Dialog(QDialog):
    def __truediv__(self, other):
        if isinstance(other, QLayout):
            self.setLayout(other)
        else:
            raise TypeError(f"Cannot divide layout by object of type {type(other).__name__}")
        return self
class Widget(QWidget):
    def __truediv__(self, other):
        if isinstance(other, QLayout):
            self.setLayout(other)
        else:
            raise TypeError(f"Cannot divide layout by object of type {type(other).__name__}")
        return self
    def __add__(self, other):
        if not isinstance(other, QWidget):
            raise TypeError(f"Cannot add object of type {type(other).__name__} to Widget")
        container = Widget()
        layout = VLayout()
        layout.addWidget(self)
        layout.addWidget(other)
        container.setLayout(layout)
        return container
    def __sub__(self, other):
        if not isinstance(other, QWidget):
            raise TypeError(f"Cannot subtract object of type {type(other).__name__} from Widget")
        container = Widget()
        layout = HLayout()
        layout.addWidget(self)
        layout.addWidget(other)
        container.setLayout(layout)
        return container

# -- widget constructors 
def new_text(foreground = "white", layout = None):
    color_css = color_to_css(foreground)
    text_edit = QTextEdit()
    text_edit.setStyleSheet(f"""
        QTextEdit {{
            background-color: rgba(0, 0, 0, 150);
            color: {color_css};
            border: 1px solid rgba(255, 255, 255, 50);
            border-radius: 5px;
            padding: 5px;
            font-size: 11px;
        }}
    """)
    text_edit.setFocusPolicy(Qt.StrongFocus)
    if layout is None: return text_edit
    layout.addWidget(text_edit)
    return text_edit
def new_button(label, callback, foreground = "white", layout = None):
    color_css = color_to_css(foreground)
    button = QPushButton(label)
    button.setStyleSheet(f"""
        QPushButton {{
            background-color: rgba(0, 0, 0, 150);
            color: {color_css};
            border: 1px solid rgba(255, 255, 255, 50);
            border-radius: 5px;
            padding: 5px;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 20);
        }}
    """)
    button.clicked.connect(callback)
    if layout is None: return button 
    layout.addWidget(button)
    return button
def new_label(text = "", foreground = "white", parent = None):
    if not parent is None:
        label = QLabel(parent)
    else:
        label = QLabel()
    color_css = color_to_css(foreground)    
    label.setStyleSheet(f"""
        background-color: rgba(0, 0, 0, 150);
        color: {color_css};
        padding: 5px;
        border-radius: 5px;
        font-size: 10px;
        font-weight: bold;
    """)
    label.setWordWrap(True)
    label.setFocusPolicy(Qt.NoFocus)
    label.setText(text)
    return label 
def new_tab_bar(label="tab 1", callback = None):
    tab_ = QTabBar()
    tab_.addTab(label)
    # Styling (matches your dark semi-transparent style)
    tab_.setStyleSheet("""
        QTabBar::tab {
            background-color: rgba(0, 0, 0, 150);
            color: white;
            padding: 5px 10px;
            border: 1px solid rgba(255, 255, 255, 30);
            border-radius: 3px;
            margin: 2px;
            font-size: 10px;
        }
        QTabBar::tab:selected {
            background-color: rgba(255, 255, 255, 30);
            color: cyan;
        }
        QTabBar::tab:hover {
            background-color: rgba(255, 255, 255, 20);
        }
    """)
    # tab_widget.setFocusPolicy(Qt.StrongFocus)
    if callback: tab_.currentChanged.connect(callback)
    return tab_
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

# -- serialization 
class Serializable:
    """
    WARNING !!! This class could cause infinite saving process for cross referencing Serializables. Make sure only one class save the property. (oZumbiAnalitico) 
    
    A base class providing robust serialization and deserialization support for custom objects.

    The `Serializable` class enables instances of derived classes to be saved to and loaded from 
    JSON format while preserving their class identity, nested structure, and complex data types 
    such as tuples, sets, and dictionaries.

    Features:
        - Automatic registration of subclasses for deserialization by class name.
        - Configurable field selection for serialization using `__serialize_only__` or 
          `__ignore_serialize__` class-level attributes.
        - Thread-safe file saving with atomic writes via temporary files.
        - Support for nested Serializable instances.
        - Custom handling of compound data types: tuples, sets, frozensets, lists, and dicts.

    Usage:
        Subclass `Serializable` and optionally define:
            - `__serialize_only__`: A list of attribute names to explicitly serialize.
            - `__ignore_serialize__`: A list of attribute names to skip during serialization.

        Call `Save_JSON(filename)` to serialize to a file.
        Call `Load_JSON(filename)` to load an instance from a file.
        Use `to_dict()` and `from_dict()` for manual control of (de)serialization.

    Example:
        class Character(Serializable):
            def __init__(self, name, level):
                super().__init__()
                self.name = name
                self.level = level
                self.inventory = []

        c = Character("Knight", 10)
        c.Save_JSON("character.json")

        c2 = Character("Placeholder", 0)
        c2.Load_JSON("character.json")

    Notes:
        - The use of both `__serialize_only__` and `__ignore_serialize__` in the same class
          is disallowed and will raise a ValueError.
        - Player-controlled entities or real-time components may need custom logic to bypass
          or override turn-based persistence mechanisms.

    --- Documentation generated with the assistance of ChatGPT (OpenAI).
    """
    
    _registry = {}
    _registry_lock = threading.Lock()
    _file_locks = defaultdict(threading.Lock)
    
    def __init__(self):
        self.class_name = self.__class__.__name__  # Auto-assign based on class
        # Use class-declared serialization preferences if available
        if hasattr(self.__class__, "__serialize_only__"):
            self._explicit_keys = set(self.__class__.__serialize_only__)
            self._ignored_keys = set()
        else:
            self._ignored_keys = {"_ignored_keys", "class_name"}
            if hasattr(self.__class__, "__ignore_serialize__"):
                self._ignored_keys |= set(self.__class__.__ignore_serialize__)
        
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "__serialize_only__") and hasattr(cls, "__ignore_serialize__"):
            raise ValueError(
                f"{cls.__name__} cannot define both __serialize_only__ and __ignore_serialize__."
            )
        with Serializable._registry_lock:
            Serializable._registry[cls.__name__] = cls
    
    def to_dict(self):
        T1 = tic()
        data = {"class_name": self.class_name}
        
        keys_to_serialize = getattr(self, "_explicit_keys", None)
        if keys_to_serialize is None:
            keys_to_serialize = [k for k in self.__dict__.keys() if k not in self._ignored_keys]
        
        # local variable lookup 
        local_serialize = self._serialize
        local_isinstance = isinstance
        local_Serializable = Serializable
        local_getattr = getattr 

        for key in keys_to_serialize:
            # value = self.__dict__[key]
            value = local_getattr(self, key, None)
            if value is None: continue 
            if local_isinstance(value, local_Serializable):
                data[key] = value.to_dict()
            else:
                data[key] = local_serialize(value)
        toc(T1, "Serializable.to_dict() ||")        
        return data
    
    def from_dict(self, dictionary):
        if dictionary.get("class_name") != self.class_name:
            print(f"Warning: class mismatch ({dictionary.get('class_name')} != {self.class_name})")
            return False
        for key, value in dictionary.items():
            if key in self._ignored_keys or key == "class_name":
                continue
            current_attr = getattr(self, key, None)
            deserialized_value = self._deserialize(value, current_attr)
            setattr(self, key, deserialized_value)
        return True
    
    def Save_JSON(self, filename):
        filename = Path(filename)
        temp_name = None  # ensure it's defined for cleanup
        
        file_lock = Serializable._file_locks[str(filename)]
        
        with file_lock:
            try:
                with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', dir=filename.parent) as tmp_file:
                    T1 = tic()
                    json.dump(self.to_dict(), tmp_file, indent=4)
                    toc(T1, f"Serializable.Save_JSON() || json.dump( Serializable: { self }) ||")
                    temp_name = tmp_file.name
                shutil.move(temp_name, filename)  # atomic replace
                return True
            except Exception as e:
                print(f"Error saving JSON to {filename}: {e}")
                if temp_name and os.path.exists(temp_name):
                    try:
                        os.remove(temp_name)
                    except Exception as cleanup_err:
                        print(f"Warning: failed to clean up temp file {temp_name}: {cleanup_err}")
                return False
    
    def Load_JSON(self, filename):
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return False
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.from_dict(data)
        except Exception as e:
            print(f"Error loading JSON from {filename}: {e}")
            return False
    
    def _serialize(self, value):
        if isinstance(value, Serializable):
            return value.to_dict()
        elif isinstance(value, tuple):
            return {"__tuple__": [self._serialize(v) for v in value]}
        elif isinstance(value, set):
            return {"__set__": [self._serialize(v) for v in value]}
        elif isinstance(value, frozenset):
            return {"__frozenset__": [self._serialize(v) for v in value]}
        elif isinstance(value, list):
            return [self._serialize(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize(v) for k, v in value.items()}
        else:
            return value
        
    def _deserialize(self, value, target):
        if isinstance(value, dict):
            if "__tuple__" in value:
                return tuple(self._deserialize(v, None) for v in value["__tuple__"])
            elif "__set__" in value:
                return set(self._deserialize(v, None) for v in value["__set__"])
            elif "__frozenset__" in value:
                return frozenset(self._deserialize(v, None) for v in value["__frozenset__"])
            elif "class_name" in value:
                if isinstance(target, Serializable):
                    target.from_dict(value)
                    return target
                else:
                    cls_name = value.get("class_name")
                    cls = self._get_class_by_name(cls_name)
                    if cls:
                        obj = cls()
                        obj.from_dict(value)
                        return obj
                    else:
                        print(f"Warning: Unknown class '{cls_name}' during deserialization.")
                        return value
            else:
                return {k: self._deserialize(v, None) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._deserialize(v, None) for v in value]
        else:
            return value

    def set_ignored_keys(self, keys):
        """Explicitly set ignored keys for serialization"""
        self._ignored_keys = set(keys) | {"_ignored_keys", "class_name"}

    def append_ignored_keys(self, *keys):
        """Append one or more keys to the ignored list"""
        self._ignored_keys.update(keys)

    def set_serialized_keys(self, keys):
        """Switch from 'ignore mode' to 'explicit allow list'"""
        self._explicit_keys = set(keys)
        self._ignored_keys = set()  # optional: prevent mixing

    def get_ignored_keys(self):
        return iter(self._ignored_keys)

    def get_serialized_keys(self):
        if hasattr(self, "_explicit_keys"):
            return iter(self._explicit_keys)
        else:
            return (k for k in self.__dict__.keys() if k not in self._ignored_keys)

    # def __repr__(self):
        # return f"<{self.__class__.__name__} {self.to_dict()}>"

    @staticmethod
    def _get_class_by_name(name):
        return Serializable._registry.get(name, None)

# -- python code parser  
def extract_signatures(filename):
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

def extract_signatures_cpp(filename):
    pass 
    
def extract_signatures_cs(filename):
    pass 
    
def extract_signatures_lua(filename):
    pass 

# --- Entry Point 
class MainWindow(Widget, Serializable):
    __serialize_only__ = ["window_width", "window_height", "window_x", "window_y", "list_files", "tab_current_index"]
    def __init__(self):
        Widget.__init__(self)
        Serializable.__init__(self)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.75)
        self.setWindowTitle("Project Overview")
        self.setFocusPolicy(Qt.StrongFocus)  # Ensure Game accepts focus
        self.setWindowTitle("Project Overview")
        self.window_x = 0
        self.window_y = 0
        self.window_width = 600
        self.window_height = 700
        self.list_files = []
        self.collapsables = {}
        self.tab_current_index = 0
        self.Load_JSON("overview.ini")
        # -- after load state 
        self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
        self.build_parts()
        self.assemble_parts()
        self.tabs.setCurrentIndex( self.tab_current_index % self.tabs.count() )
        self.update()
    def clear_tabs(self):
        while self.tabs.count() > 1:
            self.tabs.removeTab(1)    
    def update_file_list(self):
        # & walk through directories || & file in files || % .py or .pyw || add the file_path to list 
        self.list_files.clear()
        for root, dirs, files in os.walk('.'):  # '.' is the current directory
            for file in files:
                file_path = os.path.join(root, file)
                if "overview.pyw" in file_path: continue 
                if pattern_py.match(file_path):
                    self.list_files.append(file_path)
                elif pattern_pyw.match(file_path):
                    self.list_files.append(file_path)
    def update_tabs(self):
        self.clear_tabs()
        for file in self.list_files:
            self.tabs.addTab(file)
    def callback_add_files(self):
        self.update_file_list()
        self.update_tabs()
    def next_tab(self):
        self.tabs.setCurrentIndex( (self.tabs.currentIndex() + 1) % self.tabs.count() )
    def prev_tab(self):
        count = self.tabs.count()
        curr_idx = self.tabs.currentIndex()
        idx_f = ( count - curr_idx ) % count 
        # f_curr_idx  = count - curr_idx - 1
        self.tabs.setCurrentIndex( (count-1) - idx_f ) 
    def eventFilter(self, obj, event):
        # self.list_widget.setFocus()
        if obj == self.list_widget and event.type() == QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Return, Qt.Key_Enter):
                current_item = self.list_widget.currentItem()
                if current_item:
                    self.double_click(current_item)
                    self.copy_to_clipboard()
                    return True
            if key in (Qt.Key_Tab, Qt.Key_Control, Qt.Key_PageDown):
                self.next_tab()
                return True
            if key in (Qt.Key_Shift, Qt.Key_PageUp):
                self.prev_tab()
                return True
        # elif obj != self.list_widget:
            # self.list_widget.setFocus()
            # return super().eventFilter(obj, event)    
        return super().eventFilter(obj, event)    
    def resizeEvent(self, event):
        # This method is called whenever the window is resized
        rect = self.geometry()
        self.window_x = rect.x()
        self.window_y = rect.y()
        self.window_width = rect.width()
        self.window_height = rect.height()
        super().resizeEvent(event)  # Make sure to call the base class implementation    
    def closeEvent(self, event):
        """Save the game state when the window is closed."""
        rect = self.geometry()
        self.window_x = rect.x()
        self.window_y = rect.y()
        self.window_width = rect.width()
        self.window_height = rect.height()
        self.tab_current_index = self.tabs.currentIndex()
        try:
            self.Save_JSON("overview.ini")
        except Exception as e:
            print(f"Error saving game on exit: {e}")
        event.accept()
    def build_parts(self):
        self.layer = VLayout()
        self.tabs = new_tab_bar("overview.pyw", self.update)        
        # self.tabs.addTab("globals_variables.py")
        # self.tabs.addTab("game.py")
        # self.tabs.addTab("gui.py")
        # self.tabs.addTab("reality.py")
        # self.tabs.addTab("mapping.py")
        # self.tabs.addTab("pyqt_layer_framework.py")
        # self.tabs.addTab("serialization.py")
        # self.tabs.addTab("performance.py")
        # self.tabs.addTab("overview.pyw")
        self.list_widget = new_list_widget(self.double_click, self)
        self.base_text_button = "Copy to Clipboard"
        self.base_text_button_add_files = " + "
        self.button_add_files = new_button(self.base_text_button_add_files, self.callback_add_files)
        self.button_copy_to_cliboard = new_button(self.base_text_button, self.copy_to_clipboard)
    def assemble_parts(self):
        self / (self.layer / self.tabs / self.list_widget / ( HLayout() / self.button_add_files / self.button_copy_to_cliboard ) )
        self.update_tabs()
        self.list_widget.setFocus()
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
        if text[:4]=="    ":
            return text, False # false means that isn't a pivot 
        return text, True # true means that is a pivot 
    def update(self, index = None):
        text = None
        if not index: 
            text = "overview.pyw"
        else: 
            text = self.tabs.tabText(index)
        self.list_widget.clear()
        if not text: return 
        idx = 0
        list_collapsable = []
        self.collapsables.clear()
        ext = extract_signatures(text)
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
            self.button_copy_to_cliboard.setText( self.base_text_button+f"( {text[:min(25, len(text))].lstrip().rstrip()} ... )" )
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    obj = MainWindow()
    obj.show()
    sys.exit(app.exec_()) 

# -- END     