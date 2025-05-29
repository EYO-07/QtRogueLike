# Inventories 

# -- basic python 

""" Inventory [ Dictionary ] { Basic Python }
1. my_dict = {} ; Creates an empty dictionary.
2. my_dict = {'key': 'value'} ; Creates a dictionary with one or more key-value pairs.
3. my_dict['key'] = value ; Adds or updates a key with a specified value.
4. value = my_dict['key'] ; Retrieves the value for the given key (raises KeyError if missing).
5. value = my_dict.get('key') ; Retrieves the value safely (returns None or default if key not found).
6. my_dict.keys() ; Returns a view of all keys in the dictionary.
7. my_dict.values() ; Returns a view of all values in the dictionary.
8. my_dict.items() ; Returns a view of all key-value pairs (as tuples).
9. 'key' in my_dict ; Checks if a key exists in the dictionary.
10. my_dict.pop('key') ; Removes a key and returns its value (raises KeyError if missing).
11. my_dict.pop('key', default) ; Removes a key and returns its value (returns default if missing).
12. del my_dict['key'] ; Deletes a key-value pair (raises KeyError if key is absent).
13. my_dict.update(other_dict) ; Updates the dictionary with key-value pairs from another dictionary.
14. len(my_dict) ; Returns the number of key-value pairs in the dictionary.
15. my_dict.clear() ; Removes all key-value pairs from the dictionary.
16. dict.fromkeys(['a', 'b'], default) ; Creates a dictionary from keys with the same default value.
17. my_dict.setdefault('key', default) ; Gets value for key, inserts default if key is missing.
18. for key in my_dict: ; Iterates over keys in the dictionary.
19. for key, value in my_dict.items(): ; Iterates over key-value pairs.
20. type(my_dict) is dict ; Checks that the object is a dictionary.
"""

""" Inventory [ List ] { Basic Python }
1. my_list = [] ; Creates an empty list.
2. my_list = [1, 2, 3] ; Creates a list with initial elements.
3. my_list.append(item) ; Adds an item to the end of the list.
4. my_list.insert(index, item) ; Inserts an item at the specified index.
5. my_list.extend([4, 5]) ; Appends all elements from another iterable to the list.
6. item = my_list[index] ; Accesses the item at the given index (0-based).
7. my_list[index] = new_value ; Updates the value at the given index.
8. del my_list[index] ; Deletes the item at the given index.
9. my_list.remove(value) ; Removes the first occurrence of a value (raises ValueError if not found).
10. item = my_list.pop(index) ; Removes and returns the item at the index (last by default).
11. len(my_list) ; Returns the number of items in the list.
12. my_list.sort() ; Sorts the list in-place (ascending by default).
13. my_list.sort(reverse=True) ; Sorts the list in descending order.
14. sorted(my_list) ; Returns a new sorted list (original remains unchanged).
15. my_list.reverse() ; Reverses the list in-place.
16. reversed(my_list) ; Returns a reversed iterator.
17. my_list.index(value) ; Returns the index of the first occurrence of a value.
18. my_list.count(value) ; Returns the number of times a value appears in the list.
19. for item in my_list: ; Iterates through each item in the list.
20. [x for x in my_list if condition] ; List comprehension for filtering or transforming.
"""

""" Inventory [ Set ] { Basic Python }
1. my_set = set() ; Creates an empty set.
2. my_set = {1, 2, 3} ; Creates a set with initial unique elements.
3. my_set.add(item) ; Adds an item to the set (duplicates are ignored).
4. my_set.update([2, 3, 4]) ; Adds multiple items from another iterable.
5. my_set.remove(item) ; Removes an item (raises KeyError if not found).
6. my_set.discard(item) ; Removes an item if present (no error if missing).
7. item = my_set.pop() ; Removes and returns an arbitrary item from the set.
8. my_set.clear() ; Removes all elements from the set.
9. len(my_set) ; Returns the number of elements in the set.
10. item in my_set ; Checks if an item is in the set.
11. my_set.union(other_set) ; Returns a new set with elements from both sets.
12. my_set | other_set ; Shorthand for union.
13. my_set.intersection(other_set) ; Returns a new set with common elements.
14. my_set & other_set ; Shorthand for intersection.
15. my_set.difference(other_set) ; Returns elements in my_set but not in other_set.
16. my_set - other_set ; Shorthand for difference.
17. my_set.symmetric_difference(other_set) ; Returns elements in either set, but not both.
18. my_set ^ other_set ; Shorthand for symmetric difference.
19. my_set.issubset(other_set) ; Checks if all elements of my_set are in other_set.
20. my_set.issuperset(other_set) ; Checks if my_set contains all elements of other_set.
""" 

""" Inventory [ String ] { Basic Python }
1. my_str = "Hello" ; Creates a string.
2. len(my_str) ; Returns the number of characters in the string.
3. my_str[i] ; Accesses the character at index i (0-based).
4. my_str.lower() ; Returns a lowercase version of the string.
5. my_str.upper() ; Returns an uppercase version of the string.
6. my_str.capitalize() ; Capitalizes the first character.
7. my_str.title() ; Capitalizes the first letter of each word.
8. my_str.strip() ; Removes leading and trailing whitespace.
9. my_str.lstrip() ; Removes leading whitespace.
10. my_str.rstrip() ; Removes trailing whitespace.
11. my_str.replace("old", "new") ; Replaces occurrences of a substring.
12. my_str.split("sep") ; Splits the string into a list using a separator.
13. "sep".join(list) ; Joins elements of a list into a string using a separator.
14. my_str.find("sub") ; Returns the first index of substring, or -1 if not found.
15. my_str.index("sub") ; Like find(), but raises ValueError if not found.
16. my_str.count("sub") ; Returns the number of times a substring appears.
17. my_str.startswith("prefix") ; Checks if string starts with a prefix.
18. my_str.endswith("suffix") ; Checks if string ends with a suffix.
19. my_str.isalpha() ; Returns True if all characters are letters.
20. my_str.isdigit() ; Returns True if all characters are digits.
"""

""" Inventory [ Math ] { Python Built-in Library }
1. math.sqrt(x) ; Returns the square root of x.
2. math.pow(x, y) ; Returns x raised to the power of y (x^y) as a float.
3. math.exp(x) ; Returns e raised to the power of x.
4. math.log(x) ; Returns the natural logarithm of x (base e).
5. math.log(x, base) ; Returns the logarithm of x to the specified base.
6. math.log10(x) ; Returns the base-10 logarithm of x.
7. math.log2(x) ; Returns the base-2 logarithm of x.
8. math.floor(x) ; Returns the largest integer less than or equal to x.
9. math.ceil(x) ; Returns the smallest integer greater than or equal to x.
10. math.trunc(x) ; Truncates x to the nearest integer toward zero.
11. math.fabs(x) ; Returns the absolute value of x as a float.
12. math.factorial(x) ; Returns the factorial of x (x!).
13. math.gcd(a, b) ; Returns the greatest common divisor of a and b.
14. math.lcm(a, b) ; Returns the least common multiple of a and b (Python 3.9+).
15. math.isclose(a, b, rel_tol=1e-09, abs_tol=0.0) ; Checks if a and b are close in value.
16. math.sin(x) ; Returns the sine of x (x in radians).
17. math.cos(x) ; Returns the cosine of x (x in radians).
18. math.tan(x) ; Returns the tangent of x (x in radians).
19. math.asin(x) ; Returns the arcsine of x in radians.
20. math.acos(x) ; Returns the arccosine of x in radians.
21. math.atan(x) ; Returns the arctangent of x in radians.
22. math.atan2(y, x) ; Returns atan(y/x) in radians, accounting for quadrant.
23. math.radians(x) ; Converts angle x from degrees to radians.
24. math.degrees(x) ; Converts angle x from radians to degrees.
25. math.hypot(x, y) ; Returns the Euclidean norm √(x² + y²).
26. math.copysign(x, y) ; Returns x with the sign of y.
27. math.fmod(x, y) ; Returns the remainder of x/y (same sign as x).
28. math.remainder(x, y) ; Returns IEEE 754-style remainder of x with respect to y.
29. math.frexp(x) ; Returns (m, e) such that x = m * 2**e and m is in [0.5, 1).
30. math.ldexp(m, e) ; Returns m * 2**e (inverse of frexp).
31. math.modf(x) ; Returns fractional and integer parts of x as a tuple.
32. math.pi ; Mathematical constant π (3.14159...).
33. math.e ; Mathematical constant e (2.71828...).
34. math.tau ; Mathematical constant τ (2π).
35. math.inf ; Floating-point positive infinity.
36. math.nan ; Floating-point NaN (Not a Number).
"""

# -- pyqt5

""" Inventory [ pyqt5 ] { Python, General Methods and Variables }
1. QApplication([]) ; Initializes the application environment (required for all PyQt5 apps).
2. QWidget() ; Base class for all UI objects like windows, dialogs, and controls.
3. QMainWindow() ; Main application window with menu bar, toolbars, status bar, etc.
4. QLabel("Text") ; Widget to display text or images.
5. QPushButton("Click Me") ; Clickable button widget.
6. QVBoxLayout() ; Layout manager for vertical stacking of widgets.
7. QHBoxLayout() ; Layout manager for horizontal stacking of widgets.
8. QGridLayout() ; Layout manager for arranging widgets in a grid.
9. .setLayout(layout) ; Assigns a layout manager to a widget.
10. .show() ; Displays the widget on the screen.
11. .exec_() ; Starts the application's event loop (usually called on QApplication or dialogs).
12. .setText("New Text") ; Sets the text of a label or button.
13. .text() ; Retrieves the current text of a widget (e.g., QLineEdit).
14. .clicked.connect(function) ; Connects a button click to a Python function.
15. QTimer.singleShot(ms, func) ; Calls a function once after a delay in milliseconds.
16. .resize(w, h) ; Sets the width and height of a widget.
17. .move(x, y) ; Positions the widget at x, y coordinates.
18. QDialog() ; Modal or non-modal dialog window.
19. QFileDialog.getOpenFileName() ; Opens a file picker dialog and returns the selected file path.
20. QMessageBox.information(widget, title, message) ; Displays an informational popup dialog.
"""

""" Inventory [ QWidget ] { Setting Event Handles }
1. mousePressEvent(self, event) ; Handles mouse button press events. Override to respond when the user presses a mouse button on the widget.
2. mouseMoveEvent(self, event) ; Handles mouse move events. Override to track or respond to mouse movement while a button is held down.
3. mouseReleaseEvent(self, event) ; Handles mouse button release events. Override to define behavior when the user releases a mouse button.
4. keyPressEvent(self, event) ; Handles key press events. Override to respond to keyboard input when the widget has focus.
5. keyReleaseEvent(self, event) ; Handles key release events. Override to detect when a key is released.
6. enterEvent(self, event) ; Triggered when the mouse enters the widget's area. Useful for hover effects or tooltips.
7. leaveEvent(self, event) ; Triggered when the mouse leaves the widget's area. Often used to end hover effects.
8. focusInEvent(self, event) ; Called when the widget gains keyboard focus. Override to handle focus changes.
9. focusOutEvent(self, event) ; Called when the widget loses keyboard focus. Useful for validating input or ending interactions.
10. resizeEvent(self, event) ; Called when the widget is resized. Override to handle layout or redraw on size change.
11. moveEvent(self, event) ; Called when the widget is moved. Can be used to track layout-dependent logic.
12. closeEvent(self, event) ; Called when the widget is requested to close. Override to confirm or block closing.
13. paintEvent(self, event) ; Handles all custom painting. Override to draw directly on the widget using QPainter.
14. contextMenuEvent(self, event) ; Triggered on right-click. Override to show a custom context menu.
15. wheelEvent(self, event) ; Handles mouse wheel input. Useful for scrolling or zoom functionality.
16. event(self, event) ; Central event dispatcher. Can be overridden to intercept and handle all events generically.
"""

""" Inventory [ QEvent ]
1. QEvent(type: QEvent.Type) ; Constructor to create an event of the given type.
2. type() ; Returns the type of the event (e.g. QEvent.MouseButtonPress, QEvent.KeyPress).
3. accept() ; Marks the event as accepted, preventing it from being propagated further if applicable.
4. ignore() ; Marks the event as ignored, allowing it to be handled by the parent or default handler.
5. isAccepted() ; Returns whether the event has been accepted.
6. spontaneous() ; Returns True if the event originated outside the application (e.g. from the OS or user input).
7. registerEventType([hint]) ; Static method to register a custom event type, optionally with a hint ID.
8. QEvent.MouseButtonPress ; Event type for mouse button press.
9. QEvent.MouseButtonRelease ; Event type for mouse button release.
10. QEvent.MouseButtonDblClick ; Event type for mouse double-click.
11. QEvent.MouseMove ; Event type for mouse movement.
12. QEvent.KeyPress ; Event type for key press.
13. QEvent.KeyRelease ; Event type for key release.
14. QEvent.Enter ; Event type when the mouse enters a widget.
15. QEvent.Leave ; Event type when the mouse leaves a widget.
16. QEvent.FocusIn ; Event type for widget gaining keyboard focus.
17. QEvent.FocusOut ; Event type for widget losing keyboard focus.
18. QEvent.ContextMenu ; Event type for context menu trigger (usually right-click).
19. QEvent.Wheel ; Event type for mouse wheel movement.
20. QEvent.Resize ; Event type for widget resize.
21. QEvent.Move ; Event type for widget move.
22. QEvent.Close ; Event type for widget close request.
23. QEvent.Paint ; Event type for widget redraw.
24. QEvent.Timer ; Event type for QTimer timeout.
25. QEvent.User ; Base value for user-defined events (start from here when defining custom types).
""" 

""" Inventory [ QWidget.mousePressEvent ] { Detecting which mouse button was pressed }
1. event.button() == Qt.LeftButton ; Checks if the left mouse button was pressed.
2. event.button() == Qt.RightButton ; Checks if the right mouse button was pressed.
3. event.button() == Qt.MiddleButton ; Checks if the middle mouse button (wheel click) was pressed.
4. event.button() == Qt.BackButton ; Checks if the back mouse button (usually a side button) was pressed.
5. event.button() == Qt.ForwardButton ; Checks if the forward mouse button (usually a side button) was pressed.
6. event.button() == Qt.NoButton ; Indicates no button was pressed (rare in press events).
7. event.buttons() & Qt.LeftButton ; Checks if the left button is part of the current button state (can detect multiple buttons).
8. event.buttons() & Qt.RightButton ; Checks if the right button is part of the current button state.
9. event.pos() ; Returns the position of the mouse cursor relative to the widget.
10. event.globalPos() ; Returns the global position of the mouse cursor on the screen.
11. event.type() == QEvent.MouseButtonPress ; Confirms the event is a mouse button press (used in generic event handling).
"""

""" Inventory [ Qt Events Preferentially Handled with .connect ] { Signal-Slot Pattern }
1. clicked ; Emitted by QPushButton, QCheckBox, etc. when the widget is clicked. Example: button.clicked.connect(handler)
2. toggled(bool) ; Emitted when the check state of a toggle-able widget changes (e.g., QCheckBox, QRadioButton). Example: checkbox.toggled.connect(handler)
3. stateChanged(int) ; Emitted by QCheckBox when its check state changes. Example: checkbox.stateChanged.connect(handler)
4. currentIndexChanged(int / str) ; Emitted by QComboBox when the selection changes. Example: combo.currentIndexChanged.connect(handler)
5. textChanged(str) ; Emitted by QLineEdit, QTextEdit, etc. when the text is edited. Example: lineedit.textChanged.connect(handler)
6. returnPressed ; Emitted by QLineEdit when the Enter or Return key is pressed. Example: lineedit.returnPressed.connect(handler)
7. valueChanged(int / float) ; Emitted by QSpinBox, QSlider, QDial, etc. when the value changes. Example: slider.valueChanged.connect(handler)
8. itemClicked(QListWidgetItem*) ; Emitted by QListWidget when an item is clicked. Example: listwidget.itemClicked.connect(handler)
9. itemDoubleClicked(QListWidgetItem*) ; Emitted by QListWidget when an item is double-clicked. Example: listwidget.itemDoubleClicked.connect(handler)
10. itemSelectionChanged ; Emitted when the selection in QListWidget or QTreeWidget changes. Example: listwidget.itemSelectionChanged.connect(handler)
11. editingFinished ; Emitted by QLineEdit when the user finishes editing (e.g. presses Enter or focus is lost). Example: lineedit.editingFinished.connect(handler)
12. activated(int / str) ; Emitted by QComboBox when an item is selected (by user interaction). Example: combo.activated.connect(handler)
13. accepted / rejected ; Emitted by QDialogButtonBox when the user accepts or rejects a dialog. Example: buttonBox.accepted.connect(on_accept)
14. timeout ; Emitted by QTimer when its interval elapses. Example: timer.timeout.connect(handler)
15. customContextMenuRequested(QPoint) ; Emitted when a widget with `setContextMenuPolicy(Qt.CustomContextMenu)` is right-clicked. Example: widget.customContextMenuRequested.connect(show_context_menu)
16. hovered ; Emitted by QAction when the action is hovered over (requires UI elements like toolbars or menus). Example: action.hovered.connect(handler)
"""

""" Inventory [ QWidget ]
1. QWidget(parent=None) ; Initializes a widget, optionally with a parent.
2. .show() ; Displays the widget on the screen.
3. .hide() ; Hides the widget from the screen.
4. .resize(width, height) ; Sets the widget size.
5. .move(x, y) ; Moves the widget to (x, y) coordinates.
6. .setWindowTitle(str) ; Sets the window title.
7. .setGeometry(x, y, w, h) ; Moves and resizes widget in one call.
8. .setFixedSize(w, h) ; Sets a fixed size for the widget.
9. .close() ; Closes the widget.
10. .isVisible() ; Returns True if widget is visible.
11. .setStyleSheet(str) ; Applies CSS-like styling.
12. .update() ; Triggers a repaint of the widget.
13. .repaint() ; Immediately repaints the widget.
14. .setEnabled(bool) ; Enables/disables the widget.
15. .setLayout(QLayout) ; Sets a layout manager for child widgets.
16. .setParent(QWidget) ; Sets the parent widget.
17. .setToolTip(str) ; Sets a tooltip shown on hover.
18. .setFocus() ; Gives keyboard focus to this widget.
19. .hasFocus() ; Returns True if the widget has focus.
20. .grab() ; Captures the widget's content as a QPixmap.
21. .event(QEvent) ; Base event handler (can be overridden).
22. .mousePressEvent(event) ; Handles mouse press (custom override).
23. .keyPressEvent(event) ; Handles key press (custom override).
24. .paintEvent(event) ; Handles painting the widget (custom override).
25. .minimumSizeHint() ; Suggests a minimum size.
26. .sizeHint() ; Suggests a preferred size.
27. .setWindowFlags(Qt.WindowFlags) ; Sets window behavior (e.g., frameless).
28. .setAttribute(Qt.WidgetAttribute, on=True) ; Sets widget attributes.
29. .pos() ; Returns widget position.
30. .size() ; Returns widget size.
"""

""" Inventory [ QSlider ] { pyqt5 }
1. QSlider(Qt.Orientation) ; Constructs a slider (horizontal or vertical).
2. setMinimum(value) ; Sets the minimum value of the slider.
3. setMaximum(value) ; Sets the maximum value of the slider.
4. setRange(min, max) ; Sets both minimum and maximum values.
5. setValue(value) ; Sets the current slider value.
6. value() ; Returns the current slider value.
7. setOrientation(Qt.Horizontal or Qt.Vertical) ; Sets the slider's orientation.
8. orientation() ; Returns the current orientation.
9. setTickPosition(QSlider.TickPosition) ; Sets where ticks are drawn (e.g., TicksBelow).
10. tickPosition() ; Returns the tick position setting.
11. setTickInterval(interval) ; Sets the spacing between tick marks.
12. tickInterval() ; Returns the tick interval.
13. setSingleStep(step) ; Sets the step size for arrow key or scroll actions.
14. singleStep() ; Returns the current step size.
15. setPageStep(step) ; Sets how much the value changes on page up/down keys.
16. pageStep() ; Returns the page step value.
17. setTracking(bool) ; Enables or disables live value updates while dragging.
18. hasTracking() ; Returns whether tracking is enabled.
19. setInvertedAppearance(bool) ; Inverts visual direction of the slider.
20. setInvertedControls(bool) ; Inverts control behavior (e.g., key input).
21. setSliderPosition(position) ; Moves slider to a specific visual position.
22. sliderPosition() ; Returns the current slider's handle position.
23. setEnabled(bool) ; Enables or disables the slider.
24. isEnabled() ; Returns True if slider is enabled.
25. setVisible(bool) ; Shows or hides the slider.
26. valueChanged[int] ; Signal emitted when value changes (with int argument).
27. sliderPressed() ; Signal emitted when slider handle is pressed.
28. sliderReleased() ; Signal emitted when slider handle is released.
29. sliderMoved(int) ; Signal emitted when user moves the slider handle.
30. slider.valueChanged.connect(lambda val: print(f"New value: {val}")) 
"""

""" Inventory [ QPushButton ] { PyQt5 GUI button component }
1. QPushButton(text, parent=None) ; Create a push button with optional text label
2. .setText(str) ; Set the text displayed on the button
3. .text() ; Get the current button text
4. .setIcon(QIcon) ; Set an icon (image) on the button
5. .icon() ; Get the current icon of the button
6. .setIconSize(QSize) ; Set the display size of the button icon
7. .setCheckable(bool) ; Make the button toggleable (like a switch)
8. .isCheckable() ; Check if the button is checkable
9. .setChecked(bool) ; Programmatically check/uncheck the button
10. .isChecked() ; Return True if the button is checked
11. .setEnabled(bool) ; Enable or disable the button
12. .isEnabled() ; Check if the button is currently enabled
13. .click() ; Programmatically click the button (emits `clicked` signal)
14. .toggle() ; Toggle the checked state (if checkable)
15. .setFlat(bool) ; Make button flat (no 3D shadow)
16. .isFlat() ; Return True if the button is flat
17. .setShortcut(QKeySequence or str) ; Set keyboard shortcut to trigger the button
18. .setStyleSheet(str) ; Apply CSS-style custom styling to the button
19. .clicked.connect(func) ; Connect a function to the button click event
20. .pressed.connect(func) ; Connect a function to the button pressed-down event
21. .released.connect(func) ; Connect a function to the button released event
22. .toggled.connect(func) ; Connect a function to the toggled signal (checkable buttons)

Inventory [ QPushButton Stylesheet Properties ] { PyQt5 GUI Design }
1. QPushButton { property: value; } ; Base selector to style all QPushButton widgets
2. QPushButton:hover { property: value; } ; Styles applied when the mouse hovers over the button
3. QPushButton:pressed { property: value; } ; Styles applied when the button is clicked/pressed
4. QPushButton:checked { property: value; } ; Styles for buttons with checkable=True when selected
5. QPushButton:disabled { property: value; } ; Styles applied when the button is disabled
6. background-color: #RRGGBB; ; Sets the background color of the button
7. color: #RRGGBB; ; Sets the text color of the button
8. font: bold 14px "Arial"; ; Defines font weight, size, and family
9. border: 1px solid black; ; Creates a border around the button
10. border-radius: 5px; ; Rounds the corners of the button
11. padding: 5px 10px; ; Controls space inside the button (top/bottom, left/right)
12. margin: 5px; ; Controls space outside the button relative to other widgets
13. min-width / min-height: Npx; ; Sets the minimum dimensions of the button
14. max-width / max-height: Npx; ; Sets the maximum dimensions of the button
15. qproperty-icon: url(:/icons/icon.png); ; Sets the icon from a resource path
16. qproperty-iconSize: 32px 32px; ; Defines the size of the icon shown on the button
17. text-align: left/right/center; ; Aligns text inside the button
18. QPushButton:focus { outline: none; } ; Removes or customizes focus border
19. QPushButton[customProperty="value"] { ... } ; Applies style based on dynamic property
20. transition: all 0.3s ease; ; [Not supported in Qt stylesheets] — Qt does not support CSS transitions
"""

""" Inventory [ QTabWidget ] { Tabbed Interface with Associated Widgets }
1. QTabWidget(parent=None) ; Creates a tab widget container
2. addTab(widget, label) ; Adds a new tab with the given content widget and tab label
3. insertTab(index, widget, label) ; Inserts a tab at the given index
4. removeTab(index) ; Removes the tab at the specified index
5. count() ; Returns the number of tabs
6. currentIndex() ; Returns the index of the currently selected tab
7. setCurrentIndex(index) ; Sets the active tab by index
8. widget(index) ; Returns the content widget at the specified tab index
9. setTabText(index, label) ; Changes the label of the tab at the given index
10. setTabIcon(index, QIcon) ; Sets an icon on the tab
11. setTabsClosable(bool) ; Enables a close button on each tab
12. tabCloseRequested(index) ; Signal emitted when a tab's close button is clicked
13. setMovable(bool) ; Allows tabs to be reordered by the user
14. tabBar() ; Returns the underlying QTabBar for further customization
15. setTabEnabled(index, bool) ; Enables or disables a specific tab
16. setTabToolTip(index, text) ; Sets a tooltip for the tab at the given index
17. currentChanged(index) ; Signal emitted when the current tab changes
18. setDocumentMode(bool) ; Sets document-style tabs (flat look)
19. setElideMode(Qt.ElideRight) ; Controls text eliding when tab text is too long
20. setTabPosition(QTabWidget.North/South/East/West) ; Sets where tabs appear (top, bottom, etc.)
"""

""" Inventory [ QHBoxLayout ] { Horizontal layout manager in PyQt5 }
1. QHBoxLayout(parent=None) ; Create a new horizontal layout
2. .addWidget(widget) ; Add a widget to the layout, from left to right
3. .addSpacing(pixels) ; Add fixed horizontal space (in pixels)
4. .addStretch(stretch=1) ; Add stretchable empty space (pushes widgets apart)
5. .insertWidget(index, widget) ; Insert a widget at a specific position
6. .insertSpacing(index, pixels) ; Insert fixed space at specific index
7. .insertStretch(index, stretch=1) ; Insert stretch at a specific index
8. .addLayout(layout) ; Nest another layout inside this one
9. .setSpacing(pixels) ; Set the space between widgets in the layout
10. .setContentsMargins(left, top, right, bottom) ; Set outer margins of the layout
11. .count() ; Return number of items (widgets/spacers) in the layout
12. .itemAt(index) ; Get the layout item at given index
13. .takeAt(index) ; Remove and return the item at given index
14. .removeWidget(widget) ; Remove a specific widget from the layout
15. .invalidate() ; Mark the layout as dirty, forcing a relayout
16. .setAlignment(widget or layout, alignment) ; Align a specific widget or layout (e.g. Qt.AlignRight)
"""

""" Inventory [ QPixmap ] { pyqt5 }
1. QPixmap(filePath) ; Loads an image from a file into the pixmap.
2. QPixmap() ; Creates an empty pixmap.
3. QPixmap(width, height) ; Creates a pixmap with given dimensions.
4. isNull() ; Returns True if the pixmap is null (i.e., uninitialized).
5. load(filePath[, format[, flags]]) ; Loads an image from a file path with optional format and flags.
6. save(filePath[, format[, quality]]) ; Saves the pixmap to a file.
7. width() ; Returns the width of the pixmap.
8. height() ; Returns the height of the pixmap.
9. size() ; Returns the QSize of the pixmap.
10. scaled(width, height[, aspectRatioMode[, transformMode]]) ; Returns a scaled copy of the pixmap.
11. scaled(QSize[, aspectRatioMode[, transformMode]]) ; Returns a scaled copy with a QSize.
12. copy(x, y, width, height) ; Returns a copy of a rectangular area of the pixmap.
13. toImage() ; Converts the pixmap to a QImage.
14. fill(color) ; Fills the pixmap with the specified color.
15. fromImage(QImage) ; Static method to create a QPixmap from a QImage.
16. hasAlphaChannel() ; Returns True if the pixmap has an alpha channel.
17. setDevicePixelRatio(ratio) ; Sets the device pixel ratio for high-DPI support.
18. devicePixelRatio() ; Returns the current device pixel ratio.
19. cacheKey() ; Returns a cache key that uniquely identifies the pixmap.
"""

""" Inventory [ QPainter ] { pyqt5 }
1. QPainter(device) ; Constructs a painter to begin drawing on a paint device (e.g., QPixmap, QWidget, QImage).
2. begin(device) ; Begins painting on the given device (alternative to constructor).
3. end() ; Ends painting and flushes changes.
4. isActive() ; Returns True if the painter is currently active.
5. setPen(QPen or QColor) ; Sets the pen for outlining shapes and text.
6. setBrush(QBrush or QColor) ; Sets the brush for filling shapes.
7. setFont(QFont) ; Sets the font used for drawing text.
8. setRenderHint(hint, on=True) ; Enables rendering hints (e.g., Antialiasing, TextAntialiasing).
9. drawLine(x1, y1, x2, y2) ; Draws a line between two points.
10. drawRect(x, y, w, h) ; Draws a rectangle.
11. drawEllipse(x, y, w, h) ; Draws an ellipse inside the given rectangle.
12. drawPolygon(QPolygon or list of QPoint) ; Draws a polygon.
13. drawPixmap(x, y, QPixmap) ; Draws a pixmap at a given position.
14. drawImage(x, y, QImage) ; Draws an image.
15. drawText(x, y, text) ; Draws text at the specified position.
16. drawPath(QPainterPath) ; Draws a complex path.
17. translate(dx, dy) ; Moves the coordinate system origin.
18. rotate(angle) ; Rotates the coordinate system.
19. scale(sx, sy) ; Scales the coordinate system.
20. shear(sh, sv) ; Applies a shear transformation.
21. setTransform(QTransform[, combine]) ; Applies or replaces the transformation matrix.
22. resetTransform() ; Resets transformations to identity.
23. save() ; Saves the current painter state (pen, brush, transform, etc.).
24. restore() ; Restores the previously saved state.
25. clipRect() ; Returns the current clip rectangle.
26. setClipRect(x, y, w, h[, operation]) ; Sets a clip rectangle to limit the drawing area.
27. setOpacity(opacity) ; Sets the global opacity (0.0–1.0).
28. fillRect(x, y, w, h, brush or color) ; Fills a rectangle with a brush or color.
29. eraseRect(x, y, w, h) ; Erases a rectangle area (sets it to background).
30. compositionMode() ; Returns the current composition mode.
31. setCompositionMode(mode) ; Sets how pixels are blended (e.g., SourceOver, Multiply).
"""

""" Inventory [ QMediaPlayer ] { PyQt5.QtMultimedia }
1. play() ; Inicia a reprodução do conteúdo de mídia atual.
2. pause() ; Pausa a reprodução do conteúdo de mídia atual.
3. stop() ; Interrompe a reprodução do conteúdo de mídia atual.
4. setMedia(media, stream=None) ; Define o conteúdo de mídia a ser reproduzido.
5. setMuted(muted) ; Define o estado de mudo do áudio.
6. setPlaybackRate(rate) ; Define a taxa de reprodução do conteúdo de mídia.
7. setPlaylist(playlist) ; Define a lista de reprodução associada ao player.
8. setPosition(position) ; Define a posição atual de reprodução em milissegundos.
9. setVolume(volume) ; Define o volume do áudio (0 a 100).
10. setVideoOutput(output) ; Define o destino de saída de vídeo (QVideoWidget ou QGraphicsVideoItem).
11. audioAvailableChanged(available) ; Sinal emitido quando a disponibilidade de áudio muda.
12. audioRoleChanged(role) ; Sinal emitido quando o papel do áudio muda.
13. bufferStatusChanged(percentFilled) ; Sinal emitido quando o status do buffer muda.
14. currentMediaChanged(media) ; Sinal emitido quando o conteúdo de mídia atual muda.
15. mediaChanged(media) ; Sinal emitido quando o conteúdo de mídia muda.
16. mediaStatusChanged(status) ; Sinal emitido quando o status da mídia muda.
17. mutedChanged(muted) ; Sinal emitido quando o estado de mudo do áudio muda.
18. playbackRateChanged(rate) ; Sinal emitido quando a taxa de reprodução muda.
19. positionChanged(position) ; Sinal emitido quando a posição de reprodução muda.
20. stateChanged(state) ; Sinal emitido quando o estado do player muda.
21. volumeChanged(volume) ; Sinal emitido quando o volume do áudio muda.

# Inventory [QMediaPlayer] {Eventos de Estado de Mídia}
# 1. mediaStatusChanged(QMediaPlayer.MediaStatus) ; Emite mudanças no status da mídia, como carregando ou finalizada.
# 2. stateChanged(QMediaPlayer.State) ; Emite mudanças no estado do player (StoppedState, PlayingState, PausedState).
# 3. QMediaPlayer.EndOfMedia ; Enum do status da mídia indicando que a reprodução chegou ao fim.
# 4. QMediaPlayer.LoadingMedia ; Enum indicando que a mídia está sendo carregada.
# 5. QMediaPlayer.LoadedMedia ; Enum indicando que a mídia foi carregada com sucesso.
# 6. QMediaPlayer.BufferedMedia ; Enum indicando que a mídia foi completamente armazenada em buffer.
# 7. QMediaPlayer.NoMedia ; Enum indicando que nenhuma mídia foi definida.
# 8. QMediaPlayer.InvalidMedia ; Enum indicando erro ao carregar a mídia.
# 9. QMediaPlayer.StalledMedia ; Enum indicando que o buffer de mídia foi interrompido (rede lenta, etc.).
# 10. QMediaPlayer.UnknownMediaStatus ; Enum indicando que o status da mídia é indefinido.
"""

""" Inventory [ QGraphicsTextItem ]
1. QGraphicsTextItem([str text], [QGraphicsItem parent]) ; Constructor, optionally sets text and parent item
2. setPlainText(str text) ; Sets the displayed text (plain, not rich text)
3. toPlainText() -> str ; Returns the current text
4. setDefaultTextColor(QColor color) ; Sets the color of the text
5. defaultTextColor() -> QColor ; Gets the current text color
6. setFont(QFont font) ; Sets the font used for rendering the text
7. font() -> QFont ; Returns the current font
8. setTextWidth(float width) ; Sets the width for wrapping the text
9. textWidth() -> float ; Gets the current text width (used for wrapping)
10. setHtml(str html) ; Sets the text as rich HTML-formatted content
11. toHtml() -> str ; Gets the current HTML content
12. setPos(float x, float y) ; Sets the position of the text item in the scene
13. pos() -> QPointF ; Gets the current position
14. setRotation(float angle) ; Rotates the text item
15. setZValue(float z) ; Sets the stacking order (z-index)
16. zValue() -> float ; Returns the z-order value
17. setScale(float factor) ; Uniformly scales the item
18. setTransform(QTransform transform) ; Applies a custom transformation (e.g., rotate, scale, shear)
19. setFlag(QGraphicsItem.GraphicsItemFlag, bool enabled=True) ; Sets item-specific behavior (e.g., movable, selectable)
20. boundingRect() -> QRectF ; Returns the bounding rectangle of the text item
"""

""" Inventory [ QGraphicsRectItem ] { pyqt5 }
1. QGraphicsRectItem() ; Creates a default rectangular graphics item.
2. QGraphicsRectItem(rect: QRectF) ; Creates the item with the specified rectangle.
3. QGraphicsRectItem(x, y, w, h) ; Alternative constructor with coordinates.
4. setRect(x, y, w, h) ; Sets the rectangle's geometry using coordinates.
5. setRect(QRectF) ; Sets the rectangle geometry using a QRectF.
6. rect() ; Returns the current QRectF of the item.
7. setPen(QPen) ; Sets the pen used to draw the rectangle’s outline.
8. setBrush(QBrush) ; Sets the brush used to fill the rectangle.
9. pen() ; Returns the current QPen.
10. brush() ; Returns the current QBrush.
11. paint(painter, option, widget) ; Custom painting routine (can be overridden).
12. boundingRect() ; Returns the outer bounds of the item for painting & collision.
13. contains(point) ; Returns True if the item contains the given point.
14. shape() ; Returns the precise shape of the item as a QPainterPath.
15. setPos(x, y) ; Sets the position of the item in the scene.
16. pos() ; Returns the position of the item.
17. setRotation(angle) ; Rotates the item around its transform origin point.
18. rotation() ; Returns the rotation angle.
19. setTransform(transform, combine=False) ; Applies a QTransform to the item.
20. setFlags(flags) ; Sets item interaction flags (e.g. selectable, movable).
21. setZValue(z) ; Sets the z-order stacking value.
22. zValue() ; Returns the current z-order value.
23. setParentItem(item) ; Sets another QGraphicsItem as this item’s parent.
24. parentItem() ; Returns the parent item.
25. collidesWithItem(item) ; Checks collision with another item.
26. collidesWithPath(path) ; Checks collision with a QPainterPath.
"""
# --- END