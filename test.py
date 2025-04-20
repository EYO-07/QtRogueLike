from PyQt5.QtWidgets import QApplication, QMainWindow
from message_window import MessagePopup

app = QApplication([])
main = QMainWindow()
main.setFixedSize(200, 200)
msg_window = MessagePopup(main)
msg_window.set_message("Test message")
main.show()
app.exec_()