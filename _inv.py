# Inventories 

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
"""

# --- END