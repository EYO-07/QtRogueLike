# journal_window.py
from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
import os
from datetime import datetime

class JournalWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.8)  # Match InventoryWindow
        self.setFocusPolicy(Qt.NoFocus)  # Prevent stealing focus
        self.setModal(False)  # Non-blocking
        self.setWindowTitle("Journal")

        # Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(0, 0, 0, 150);
                color: yellow;
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 5px;
                padding: 5px;
                font-size: 11px;
            }
        """)
        self.text_edit.setFocusPolicy(Qt.StrongFocus)  # Allow text input
        self.layout.addWidget(self.text_edit)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20);
            }
        """)
        self.save_button.clicked.connect(self.save_journal)
        button_layout.addWidget(self.save_button)
        self.layout.addLayout(button_layout)

        self.log_button = QPushButton("Log Entry")
        self.log_button.setStyleSheet(self.save_button.styleSheet())
        self.log_button.clicked.connect(self.log_diary_entry)
        button_layout.addWidget(self.log_button)

        self.setLayout(self.layout)
        self.setFixedSize(300, 400)  # Similar size to InventoryWindow
        self.hide()  # Hidden by default
        self.update_position()
        if self.parent():
            self.parent().setFocus()

    def update_position(self):
        """Position the journal window to the right of the parent window, vertically centered."""
        if self.parent():
            parent_pos = self.parent().mapToGlobal(self.parent().rect().topLeft())
            parent_width = self.parent().width()
            parent_height = self.parent().height()
            journal_width = self.width()
            journal_height = self.height()
            x = parent_pos.x() + parent_width + 10  # 10px gap to the right
            y = parent_pos.y() + (parent_height - journal_height) // 2  # Vertical centering
            self.move(x, y)

    def save_journal(self):
        """Save journal contents to the current slot's journal file."""
        if not self.parent():
            return
        slot = self.parent().current_slot if hasattr(self.parent(), 'current_slot') else 1
        saves_dir = "./saves"
        journal_file = os.path.join(saves_dir, f"journal_{slot}.txt")
        try:
            os.makedirs(saves_dir, exist_ok=True)
            with open(journal_file, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            self.parent().add_message("Journal saved")
        except Exception as e:
            self.parent().add_message(f"Failed to save journal: {e}")
            print(f"Error saving journal to {journal_file}: {e}")
            
    def log_diary_entry(self):
        """Create a formatted diary entry with day, map coordinates, and special event text."""
        if not self.parent():
            return
        # Calculate day (1 day = 1000 turns)
        day = self.parent().turn // 1000 + 1
        map_coords = self.parent().current_map
        # Collect special event texts based on flags
        special_texts = []
        if getattr(self.parent(), 'low_hp_triggered', False):
            special_texts.append("I almost died, that enemy was tough, bastard.")
            self.parent().low_hp_triggered = False  # Reset flag
        if getattr(self.parent(), 'low_hunger_triggered', False):
            special_texts.append("I’m hungry, I need food right now, I could eat a horse.")
            self.parent().low_hunger_triggered = False  # Reset flag
        special_text = "\n".join(special_texts) if special_texts else "All is calm for now."
        # Format entry
        # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"Day {day}, Map {map_coords}, Position ({self.parent().player.x},{self.parent().player.y})\n"
            f"{special_text}\n"
            f"\n\n"
        )
        self.append_text(entry)
        self.parent().add_message("Diary entry logged")
    
    def keyPressEvent(self, event):
        """Handle key presses, e.g., Escape to close."""
        if event.key() == Qt.Key_Escape:
            self.hide()
            if self.parent():
                self.parent().setFocus()
        elif event.key() == Qt.Key_J:
            self.hide()
            if self.parent():
                self.parent().setFocus()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        """Ensure the text is scrolled to the end when the journal is shown."""
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()
        super().showEvent(event)
        if self.parent():
            self.parent().setFocus()
    
    def append_text(self, text):
        """Append text to the journal with a timestamp and scroll to end."""
        #timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_text = self.text_edit.toPlainText()
        new_text = f"{text}\n" if current_text else f"{text}"
        self.text_edit.setPlainText(current_text + new_text)
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()
        self.save_journal()  # Autosave after appending

    def load_journal(self, slot=1):
        """Load journal contents from the current slot's journal file."""
        saves_dir = "./saves"
        journal_file = os.path.join(saves_dir, f"journal_{slot}.txt")
        try:
            with open(journal_file, "r", encoding="utf-8") as f:
                self.text_edit.setPlainText(f.read())
        except FileNotFoundError:
            self.text_edit.setPlainText("")  # Empty journal if file doesn't exist
        except Exception as e:
            self.parent().add_message(f"Failed to load journal: {e}")
            print(f"Error loading journal from {journal_file}: {e}")
            self.text_edit.setPlainText("")
        # Move cursor to end and scroll
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()

    def keyPressEvent(self, event):
        """Handle key presses, e.g., Escape to close."""
        if event.key() == Qt.Key_Escape:
            self.hide()
            if self.parent():
                self.parent().setFocus()
        else:
            super().keyPressEvent(event)
            
            
            
            
            
            
            
            
            
