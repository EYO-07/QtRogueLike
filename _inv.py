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

# --- END