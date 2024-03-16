import sys
import dataclasses
from typing import List, Tuple
import pyperclip
from pathlib import Path
from PyQt5.QtWidgets import QApplication,QDialog,QMessageBox, QMainWindow, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QProgressBar
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from .login_dialog import LoginDialog
from .text_gen import  ApiTextGenerator, TextGenerator, HuggingFaceTextGenerator, TextGenInput
from .config import APP_NAME, BASE_DIR



try:
    from ctypes import windll  # Only exists on Windows.
    myappid = 'tz01x.textsuggestion.dsapp.1'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


@dataclasses.dataclass
class TextGenWorkerProgressEvent:
    text: str
    step_count: int


class TextGenWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(TextGenWorkerProgressEvent)

    def __init__(self, text_gen: TextGenerator, text_gen_input: TextGenInput) -> None:
        super().__init__()
        self.text_gen_input = text_gen_input
        self.text_gen = text_gen

    def run(self):
        gen = self.text_gen.generate(input=self.text_gen_input)

        for i, txt in enumerate(gen):
            self.progress.emit(
                TextGenWorkerProgressEvent(text=str(txt), step_count=i)
            )
        self.finished.emit()


class ClipboardApp(QMainWindow):
    def __init__(self, textGen: TextGenerator):
        super().__init__()
        self.textGen = textGen
        self.setWindowTitle(APP_NAME)
        self.setGeometry(100, 100, 400, 300)
        self.previously_copied_text = None

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.copied_text_label = QLabel("Currently Copied Text:", self)
        self.layout.addWidget(self.copied_text_label)

        self.copied_text_display = QTextEdit(self)
        self.copied_text_display.setFixedHeight(80)
        self.layout.addWidget(self.copied_text_display)

        self.update_copied_text()

        self.action_buttons_frame = QWidget(self)
        self.layout.addWidget(self.action_buttons_frame)

        self.btn_layout, self.action_btn_widgets = self.create_action_buttons()
        
        output_btn_frame = QWidget(self)
        self.layout.addWidget(output_btn_frame)
        
        hlayout = QHBoxLayout(output_btn_frame)
        
        self.output_text_label = QLabel("Output:", self)
        self.copy_btn = QPushButton('Copy', self)
        self.copy_btn.clicked.connect(self.copy_to_clip_board)

    
        hlayout.addWidget(self.output_text_label)
        hlayout.addStretch()
        hlayout.addWidget(self.copy_btn)

        self.output_text_display = QTextEdit(self)
        self.output_text_display.setReadOnly(True)

        self.layout.addWidget(self.output_text_display,1) # Add a stretch factor of 1 to QTextEdit
        self.layout.addStretch()

        self.progress_bar = QProgressBar(self)
        self.layout.addWidget(self.progress_bar)
        self.progress_bar.setHidden(True)
        self.progress_bar.setStyleSheet('QProgressBar {border-radius: 5px;height:2px;}')
        
        # internal state:
        self.output_text_content = ''
    
    def copy_to_clip_board(self):
        pyperclip.copy(self.output_text_content)

    def create_action_buttons(self) -> Tuple[QHBoxLayout, List[QPushButton]]:
        actions = ['Standard', 'Corporate', 'Friendly']
        btn_widgets = []
        btn_layout = QHBoxLayout(self.action_buttons_frame)
        # styleSheet = 'background-color:blue; color: white; padding:2px;'

        for action_text in actions:
            button = QPushButton(action_text, self)
            button.clicked.connect(
                lambda _, a=action_text: self.perform_action(a))
            # button.setStyleSheet(styleSheet)
            btn_layout.addWidget(button, 0)
            # button.setEnabled(False)
            btn_widgets.append(button)

        return btn_layout, btn_widgets

    def set_enable_action_button(self, val: bool):
        for btn in self.action_btn_widgets:
            btn.setEnabled(val)

    def perform_action(self, action):
        # Simulate a time-consuming task
        gen_input = TextGenInput(
            tone=action,
            text=self.copied_text_display.toPlainText())

        self.output_text_content = ''
        self.output_text_display.setPlainText(self.output_text_content)

        self.start_loading()

        self.set_enable_action_button(False)
        self.thread = QThread()
        self.worker = TextGenWorker(
            text_gen=self.textGen, text_gen_input=gen_input)
        #  Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        self.thread.started.connect(
            self.worker.run
        )
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.reportProgress)
        self.thread.start()
        self.thread.finished.connect(self.finished_action)

    def reportProgress(self, event: TextGenWorkerProgressEvent):
        self.output_text_content += event.text
        self.output_text_display.setPlainText(self.output_text_content)
        self.progress_bar.setValue(event.step_count)
        self.output_text_display.verticalScrollBar().setValue(self.output_text_display.verticalScrollBar().maximum())


    def finished_action(self):
        self.finish_loading()
        self.set_enable_action_button(True)

    def start_loading(self):
        self.progress_bar.setHidden(False)
        self.progress_bar.setRange(0, 0)

    def finish_loading(self):
        self.progress_bar.setHidden(True)
        self.progress_bar.setRange(0, 100)

    def update_copied_text(self):
        copied_text = pyperclip.paste()
        if copied_text != self.previously_copied_text:
            self.previously_copied_text = copied_text
            self.copied_text_display.setPlainText(copied_text)
        QTimer.singleShot(1000, self.update_copied_text)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet((BASE_DIR/'main.qss').read_text())
    app.setWindowIcon(QIcon((BASE_DIR/ "book.png").as_posix()))

    login_dialog = LoginDialog()
    if login_dialog.exec() == QDialog.Accepted:

        try:
            textGenerator = HuggingFaceTextGenerator()
        except Exception as e:
            QMessageBox.warning(app, "Login Failed", str(e))
            sys.exit()

        window = ClipboardApp(textGen=textGenerator)
        window.show()
    else:
        sys.exit()  
    
    sys.exit(app.exec_())
