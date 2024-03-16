import os
from cryptography.fernet import Fernet
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

from .text_gen import HuggingFaceTextGenerator
from .config import CRED_PATH, BASE_DIR, KEY_PATH

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 200, 150)
        self.initUI()
        self.key = None

    def initUI(self):
        layout = QVBoxLayout()
        self.username_label = QLabel('HuggingFace Email', self)
        layout.addWidget(self.username_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Email")
        layout.addWidget(self.username_input)

        layout.addWidget(QLabel('Password', self))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("...")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        
        self.remember_checkbox = QCheckBox("Remember Me")
        layout.addWidget(self.remember_checkbox)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)
        

        self.setLayout(layout)
        self.auto_login()
    
    def generate_key(self):
        if not os.path.exists(KEY_PATH):
            self.key = Fernet.generate_key()
            with open(KEY_PATH, "wb") as key_file:
                key_file.write(self.key)
        else:
            with open(KEY_PATH, "rb") as key_file:
                self.key = key_file.read()

    def encrypt_credentials(self, username:str, password:str):
        self.generate_key()
        cipher_suite = Fernet(self.key)
        encrypted_username = cipher_suite.encrypt(username.encode())
        encrypted_password = cipher_suite.encrypt(password.encode())
        return encrypted_username, encrypted_password

    def decrypt_credentials(self, encrypted_username, encrypted_password):
        self.generate_key()
        cipher_suite = Fernet(self.key)
        decrypted_username = cipher_suite.decrypt(encrypted_username).decode()
        decrypted_password = cipher_suite.decrypt(encrypted_password).decode()
        return decrypted_username, decrypted_password

    def save_credentials(self, encrypted_username, encrypted_password):

        with open(CRED_PATH, "wb") as file:
            file.write(encrypted_username + b'\n')
            file.write(encrypted_password)

    def read_credentials(self):
        if os.path.exists(CRED_PATH):
            with open(CRED_PATH, "rb") as file:
                encrypted_username = file.readline().strip()
                encrypted_password = file.readline()
            return encrypted_username, encrypted_password
        return None, None
    
    def remove_credentials(self):
        try:
            os.unlink(CRED_PATH)
            os.unlink(KEY_PATH)
        except:
            pass

    
    def auto_login(self):
        encrypted_username, encrypted_password = self.read_credentials()
        if encrypted_username and encrypted_password:
            decrypted_username, decrypted_password = self.decrypt_credentials(encrypted_username, encrypted_password)
            self.username_input.setText(decrypted_username)
            self.password_input.setText(decrypted_password)
            self.remember_checkbox.setCheckState(Qt.CheckState.Checked)


    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        remember_me = self.remember_checkbox.isChecked()

        if remember_me:
            encrypted_username, encrypted_password = self.encrypt_credentials(username, password)
            self.save_credentials(encrypted_username, encrypted_password)
        else:
            self.remove_credentials()
        
        try:
            HuggingFaceTextGenerator.login(username, password)
            self.accept()
        except Exception as e:
            truncate_len = 26
            truncate_msg = str(e)[:truncate_len] + ('...' if len(str(e)) > truncate_len else '')
            QMessageBox.warning(self, "Login Failed", truncate_msg)
