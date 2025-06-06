import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QDialog, QFormLayout,
    QDateEdit, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QPalette, QIcon
import psycopg2
import uuid

from Admin import MainApp as AdminApp
from ClientApp import ClientApp
from EmployeeApp import MainApp as EmployeeApp

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Смена пароля")
        self.setFixedSize(400, 300)
        self.setWindowIcon(QIcon("icon.jpg"))

        # Цветовая схема
        self.med_blue = QColor(0, 109, 176)
        self.med_light = QColor(229, 243, 255)
        self.med_white = QColor(255, 255, 255)

        # Стили
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.med_light.name()};
            }}
            QLineEdit {{
                border: 1px solid #006DB0;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-width: 200px;
                background-color: white;
            }}
            QPushButton {{
                background-color: #006DB0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #005A9C;
            }}
            QPushButton:pressed {{
                background-color: #004080;
            }}
            QLabel {{
                font-size: 14px;
                color: #006DB0;
            }}
        """)

        # Основной layout
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Заголовок
        title_label = QLabel("Смена пароля")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addRow(title_label)

        # Поля ввода
        self.old_password_input = QLineEdit()
        self.old_password_input.setPlaceholderText("Введите старый пароль")
        self.old_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.old_password_input.setMaxLength(50)

        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Введите новый пароль")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setMaxLength(50)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Подтвердите новый пароль")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setMaxLength(50)

        # Кнопки
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        # Добавление в форму
        layout.addRow("Старый пароль:", self.old_password_input)
        layout.addRow("Новый пароль:", self.new_password_input)
        layout.addRow("Подтверждение:", self.confirm_password_input)
        layout.addRow(btn_layout)

        # Подключение сигналов
        ok_btn.clicked.connect(self.change_password)
        cancel_btn.clicked.connect(self.reject)

    def change_password(self):
        old_password = self.old_password_input.text().strip()
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        # Валидация
        if not all([old_password, new_password, confirm_password]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Ошибка", "Новый пароль и подтверждение не совпадают")
            return

        if len(new_password) < 6:
            QMessageBox.warning(self, "Ошибка", "Новый пароль должен содержать не менее 6 символов")
            return

        try:
            cursor = self.parent().cursor
            conn = self.parent().conn

            # Проверка старого пароля
            cursor.execute(
                "SELECT login FROM users WHERE login = %s AND password = %s",
                (self.parent().login_input.text().strip(), old_password)
            )
            if not cursor.fetchone():
                QMessageBox.warning(self, "Ошибка", "Неверный старый пароль")
                return

            # Обновление пароля
            cursor.execute(
                "UPDATE users SET password = %s WHERE login = %s",
                (new_password, self.parent().login_input.text().strip())
            )
            conn.commit()
            QMessageBox.information(self, "Успех", "Пароль успешно изменен!")
            self.accept()

        except Exception as e:
            conn.rollback()
            logging.error(f"Ошибка при смене пароля: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сменить пароль:\n{str(e)}")

class MedicalCardDialog(QDialog):
    def __init__(self, parent=None, patient_id=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.setWindowTitle("Создание медицинской карты")
        self.setFixedSize(400, 250)
        self.setWindowIcon(QIcon("icon.jpg"))

        # Цветовая схема
        self.med_blue = QColor(0, 109, 176)
        self.med_light = QColor(229, 243, 255)
        self.med_white = QColor(255, 255, 255)

        # Стили
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.med_light.name()};
            }}
            QLineEdit, QDateEdit, QComboBox {{
                border: 1px solid #006DB0;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-width: 200px;
                background-color: white;
            }}
            QPushButton {{
                background-color: #006DB0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #005A9C;
            }}
            QPushButton:pressed {{
                background-color: #004080;
            }}
            QLabel {{
                font-size: 14px;
                color: #006DB0;
            }}
        """)

        # Основной layout
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Заголовок
        title_label = QLabel("Выберите тип медицинской карты")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addRow(title_label)

        # Поле для типа карты
        self.card_type_combo = QComboBox()
        self.card_type_combo.addItems(["Амбулаторная", "Стационарная"])

        # Поля для дат (только для отображения, не редактируемые)
        self.establishment_date = QDateEdit()
        self.establishment_date.setDate(QDate.currentDate())
        self.establishment_date.setDisplayFormat("dd.MM.yyyy")
        self.establishment_date.setEnabled(False)

        self.shelf_life_date = QDateEdit()
        self.shelf_life_date.setDate(QDate.currentDate().addYears(5))
        self.shelf_life_date.setDisplayFormat("dd.MM.yyyy")
        self.shelf_life_date.setEnabled(False)

        # Кнопки
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        # Добавление в форму
        layout.addRow("Тип мед. карты:", self.card_type_combo)
        layout.addRow("Дата создания:", self.establishment_date)
        layout.addRow("Срок действия:", self.shelf_life_date)
        layout.addRow(btn_layout)

        # Подключение сигналов
        ok_btn.clicked.connect(self.save_medical_card)
        cancel_btn.clicked.connect(self.reject)

    def save_medical_card(self):
        card_type = self.card_type_combo.currentText()
        establishment_date = self.establishment_date.date().toString("yyyy-MM-dd")
        shelf_life_date = self.shelf_life_date.date().toString("yyyy-MM-dd")

        try:
            cursor = self.parent().cursor
            conn = self.parent().conn

            # Создаем запись в таблице MedicalCard
            cursor.execute(
                """INSERT INTO medicalcard 
                (type, establishmentdate, shelflife, patientid) 
                VALUES (%s, %s, %s, %s) 
                RETURNING medicalcardid""",
                (card_type, establishment_date, shelf_life_date, self.patient_id)
            )
            medicalcard_id = cursor.fetchone()[0]

            # Обновляем Patient с medicalcardid
            cursor.execute(
                """UPDATE patient SET medicalcardid = %s WHERE patientid = %s""",
                (medicalcard_id, self.patient_id)
            )

            conn.commit()
            QMessageBox.information(self, "Успех", "Медицинская карта успешно создана!")
            self.accept()

        except Exception as e:
            self.parent().conn.rollback()
            logging.error(f"Ошибка при создании медицинской карты: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать медицинскую карту:\n{str(e)}")

class FirstLoginDialog(QDialog):
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Первоначальная регистрация пациента")
        self.setFixedSize(400, 400)
        self.setWindowIcon(QIcon("icon.jpg"))

        # Цветовая схема
        self.med_blue = QColor(0, 109, 176)
        self.med_light = QColor(229, 243, 255)
        self.med_white = QColor(255, 255, 255)

        # Стили
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.med_light.name()};
            }}
            QLineEdit, QDateEdit, QComboBox {{
                border: 1px solid #006DB0;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-width: 200px;
                background-color: white;
            }}
            QPushButton {{
                background-color: #006DB0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #005A9C;
            }}
            QPushButton:pressed {{
                background-color: #004080;
            }}
            QLabel {{
                font-size: 14px;
                color: #006DB0;
            }}
        """)

        # Основной layout
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Заголовок
        title_label = QLabel("Введите данные пациента")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addRow(title_label)

        # Поля ввода
        self.lastname_input = QLineEdit()
        self.lastname_input.setPlaceholderText("Введите фамилию")
        self.lastname_input.setMaxLength(50)

        self.firstname_input = QLineEdit()
        self.firstname_input.setPlaceholderText("Введите имя")
        self.firstname_input.setMaxLength(50)

        self.midname_input = QLineEdit()
        self.midname_input.setPlaceholderText("Введите отчество (необязательно)")
        self.midname_input.setMaxLength(50)

        self.birthdate_input = QDateEdit()
        self.birthdate_input.setDisplayFormat("dd.MM.yyyy")
        self.birthdate_input.setDate(QDate.currentDate())
        self.birthdate_input.setCalendarPopup(True)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Введите номер телефона")
        self.phone_input.setInputMask("+7(999)999-99-99;_")

        self.card_type_combo = QComboBox()
        self.card_type_combo.addItems(["Амбулаторная", "Стационарная"])

        # Кнопки
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        # Добавление в форму
        layout.addRow("Фамилия:", self.lastname_input)
        layout.addRow("Имя:", self.firstname_input)
        layout.addRow("Отчество:", self.midname_input)
        layout.addRow("Дата рождения:", self.birthdate_input)
        layout.addRow("Телефон:", self.phone_input)
        layout.addRow("Тип мед. карты:", self.card_type_combo)
        layout.addRow(btn_layout)

        # Подключение сигналов
        ok_btn.clicked.connect(self.save_patient_data)
        cancel_btn.clicked.connect(self.reject)

    def save_patient_data(self):
        lastname = self.lastname_input.text().strip()
        firstname = self.firstname_input.text().strip()
        midname = self.midname_input.text().strip()
        birthdate = self.birthdate_input.date().toString("yyyy-MM-dd")
        phone = self.phone_input.text().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        card_type = self.card_type_combo.currentText()

        # Валидация
        if not all([lastname, firstname, phone]):
            QMessageBox.warning(self, "Ошибка", "Заполните все обязательные поля (фамилия, имя, телефон)")
            return

        try:
            phone_num = int(phone[2:]) if phone.startswith("+7") else int(phone)  # Убираем +7
            cursor = self.parent().cursor
            conn = self.parent().conn

            # Создаем запись в таблице Patient
            cursor.execute(
                """INSERT INTO patient 
                (lastname, firstname, midname, birthdate, phonenumber, userid) 
                VALUES (%s, %s, %s, %s, %s, %s) 
                RETURNING patientid""",
                (lastname, firstname, midname or None, birthdate, phone_num, self.user_id)
            )
            patient_id = cursor.fetchone()[0]

            # Создаем запись в таблице MedicalCard
            establishment_date = QDate.currentDate().toString("yyyy-MM-dd")
            shelflife_date = QDate.currentDate().addYears(5).toString("yyyy-MM-dd")
            cursor.execute(
                """INSERT INTO medicalcard 
                (type, establishmentdate, shelflife, patientid) 
                VALUES (%s, %s, %s, %s) 
                RETURNING medicalcardid""",
                (card_type, establishment_date, shelflife_date, patient_id)
            )
            medicalcard_id = cursor.fetchone()[0]

            # Обновляем Patient с medicalcardid
            cursor.execute(
                """UPDATE patient SET medicalcardid = %s WHERE patientid = %s""",
                (medicalcard_id, patient_id)
            )

            conn.commit()
            QMessageBox.information(self, "Успех", "Данные пациента и медицинская карта успешно созданы!")
            self.accept()

        except Exception as e:
            self.parent().conn.rollback()
            logging.error(f"Ошибка при сохранении данных пациента: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить данные:\n{str(e)}")

class RegisterWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Медицинская информационная система - Регистрация")
        self.setFixedSize(400, 300)
        self.setWindowIcon(QIcon("icon.jpg"))

        # Цветовая схема
        self.med_blue = QColor(0, 109, 176)
        self.med_light = QColor(229, 243, 255)
        self.med_white = QColor(255, 255, 255)

        # Установка стиля окна
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.med_light.name()};
            }}
        """)

        # Настройка цветовой палитры
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, self.med_light)
        palette.setColor(QPalette.ColorRole.Base, self.med_white)
        palette.setColor(QPalette.ColorRole.Highlight, self.med_blue)
        self.setPalette(palette)

        # Основной layout
        layout = QFormLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        # Заголовок
        title_label = QLabel("Регистрация нового пользователя")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #006DB0;
                margin-bottom: 20px;
            }
        """)
        layout.addRow(title_label)

        # Поле логина
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите логин")
        self.login_input.setMaxLength(50)

        # Поле пароля
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMaxLength(50)

        # Стилизация полей ввода
        input_style = """
            QLineEdit {
                border: 1px solid #006DB0;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-width: 200px;
                background-color: white;
            }
        """
        self.login_input.setStyleSheet(input_style)
        self.password_input.setStyleSheet(input_style)

        # Добавляем поля в форму
        layout.addRow("Логин:", self.login_input)
        layout.addRow("Пароль:", self.password_input)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        register_button = QPushButton("Зарегистрироваться")
        register_button.setStyleSheet("""
            QPushButton {
                background-color: #006DB0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #005A9C;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
        """)
        register_button.setCursor(Qt.CursorShape.PointingHandCursor)
        register_button.clicked.connect(self.register_user)

        cancel_button = QPushButton("Отмена")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #cccccc;
                color: black;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b3b3b3;
            }
            QPushButton:pressed {
                background-color: #999999;
            }
        """)
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.clicked.connect(self.reject)

        btn_layout.addWidget(register_button)
        btn_layout.addWidget(cancel_button)
        layout.addRow(btn_layout)

        # Установка фокуса
        self.login_input.setFocus()

    def register_user(self):
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите логин и пароль")
            return

        try:
            # Проверка, существует ли пользователь с таким логином
            cursor = self.parent().cursor
            cursor.execute("SELECT login FROM users WHERE login = %s", (login,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким логином уже существует")
                return

            # Регистрация нового пользователя с ролью "Пользователь" по умолчанию
            cursor.execute(
                "INSERT INTO users (login, password, isblocked, role, failedattempts) VALUES (%s, %s, %s, %s, %s) RETURNING login",
                (login, password, False, "Пользователь", 0)
            )
            self.parent().conn.commit()
            QMessageBox.information(self, "Успех", f"Пользователь {login} успешно зарегистрирован!")
            self.accept()

        except Exception as e:
            self.parent().conn.rollback()
            QMessageBox.critical(self, "Ошибка", f"Не удалось зарегистрировать пользователя:\n{str(e)}")

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.debug("Инициализация LoginWindow")
        self.setWindowTitle("Медицинская информационная система - Авторизация")
        self.setFixedSize(400, 350)
        self.setWindowIcon(QIcon("icon.jpg"))

        # Цветовая схема
        self.med_blue = QColor(0, 109, 176)
        self.med_light = QColor(229, 243, 255)
        self.med_white = QColor(255, 255, 255)

        # Установка стиля окна
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.med_light.name()};
            }}
        """)

        # Настройка цветовой палитры
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, self.med_light)
        palette.setColor(QPalette.ColorRole.Base, self.med_white)
        palette.setColor(QPalette.ColorRole.Highlight, self.med_blue)
        self.setPalette(palette)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(15)

        # Заголовок
        title_label = QLabel("Авторизация в системе")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #006DB0;
                margin-bottom: 20px;
            }
        """)
        main_layout.addWidget(title_label)

        # Форма ввода
        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        # Поле логина
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Введите ваш логин")
        self.login_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Поле пароля
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите ваш пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Стилизация полей ввода
        input_style = """
            QLineEdit {
                border: 1px solid #006DB0;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                min-width: 200px;
                background-color: white;
            }
            QLineEdit:disabled {
                background-color: #e0e0e0;
            }
        """
        self.login_input.setStyleSheet(input_style)
        self.password_input.setStyleSheet(input_style)

        # Добавляем элементы в форму
        form_layout.addRow("Логин:", self.login_input)
        form_layout.addRow("Пароль:", self.password_input)
        main_layout.addLayout(form_layout)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        login_button = QPushButton("Войти")
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #006DB0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #005A9C;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
        """)
        login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        login_button.clicked.connect(self.authenticate)

        register_button = QPushButton("Регистрация")
        register_button.setStyleSheet("""
            QPushButton {
                background-color: #006DB0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #005A9C;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
        """)
        register_button.setCursor(Qt.CursorShape.PointingHandCursor)
        register_button.clicked.connect(self.open_register_window)

        change_password_button = QPushButton("Сменить пароль")
        change_password_button.setStyleSheet("""
            QPushButton {
                background-color: #006DB0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #005A9C;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
        """)
        change_password_button.setCursor(Qt.CursorShape.PointingHandCursor)
        change_password_button.clicked.connect(self.open_change_password_window)

        btn_layout.addWidget(login_button)
        btn_layout.addWidget(register_button)
        btn_layout.addWidget(change_password_button)
        main_layout.addLayout(btn_layout)

        # Инициализация подключения к базе данных
        self.conn = None
        self.cursor = None
        self.connect_to_db()

        # Установка фокуса на поле логина
        self.login_input.setFocus()

    def connect_to_db(self):
        logging.debug("Попытка подключения к базе данных в LoginWindow")
        try:
            self.conn = psycopg2.connect(
                dbname='Practice',
                user='postgres',
                password='123',
                host='localhost'
            )
            self.cursor = self.conn.cursor()
            logging.debug("Подключение к базе данных успешно")
        except psycopg2.Error as e:
            logging.error(f"Ошибка подключения к БД: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к БД: {str(e)}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Критическая ошибка: {str(e)}")
            QMessageBox.critical(self, "Критическая ошибка", f"Неожиданная ошибка: {str(e)}")
            sys.exit(1)

    def open_register_window(self):
        logging.debug("Открытие окна регистрации")
        register_dialog = RegisterWindow(self)
        if register_dialog.exec():
            self.login_input.clear()
            self.password_input.clear()
            self.login_input.setFocus()
        logging.debug("Окно регистрации закрыто")

    def open_change_password_window(self):
        logging.debug("Открытие окна смены пароля")
        if not self.login_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите логин перед сменой пароля")
            return
        change_password_dialog = ChangePasswordDialog(self)
        if change_password_dialog.exec():
            self.login_input.clear()
            self.password_input.clear()
            self.login_input.setFocus()
        logging.debug("Окно смены пароля закрыто")

    def authenticate(self):
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите логин и пароль")
            return

        try:
            # Проверяем, существует ли пользователь
            self.cursor.execute(
                "SELECT isblocked, failedattempts FROM users WHERE login = %s",
                (login,)
            )
            result = self.cursor.fetchone()

            if not result:  # Если пользователь не существует
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Пользователь с таким логином не существует."
                )
                self.password_input.clear()
                self.password_input.setFocus()
                return

            # Пользователь существует, проверяем блокировку
            is_blocked, failed_attempts = result
            if is_blocked:
                QMessageBox.warning(self, "Ошибка", "Ваш аккаунт заблокирован. Обратитесь к администратору.")
                self.password_input.clear()
                self.password_input.setFocus()
                return

            # Проверка логина, пароля и получение user_id и роли
            self.cursor.execute(
                "SELECT userid, login, isblocked, role, failedattempts FROM users WHERE login = %s AND password = %s",
                (login, password)
            )
            user = self.cursor.fetchone()

            if user is None:
                # Увеличиваем счетчик неудачных попыток
                self.cursor.execute(
                    "UPDATE users SET failedattempts = failedattempts + 1 WHERE login = %s RETURNING failedattempts",
                    (login,)
                )
                new_failed_attempts = self.cursor.fetchone()[0]

                if new_failed_attempts >= 3:
                    self.cursor.execute(
                        "UPDATE users SET isblocked = TRUE WHERE login = %s",
                        (login,)
                    )
                    self.conn.commit()
                    QMessageBox.warning(
                        self,
                        "Ошибка",
                        f"Неверный логин или пароль. Аккаунт {login} заблокирован. Обратитесь к администратору"
                    )
                else:
                    attempts_left = 3 - new_failed_attempts
                    self.conn.commit()
                    QMessageBox.warning(
                        self,
                        "Ошибка",
                        f"Неверный логин или пароль. Осталось попыток: {attempts_left}"
                    )
                self.password_input.clear()
                self.password_input.setFocus()
                return

            # Если авторизация успешна, сбрасываем счетчик неудачных попыток
            user_id, login, isblocked, role, failed_attempts = user
            self.cursor.execute(
                "UPDATE users SET failedattempts = 0 WHERE login = %s",
                (login,)
            )
            self.conn.commit()

            if isblocked:
                QMessageBox.warning(self, "Ошибка", "Пользователь заблокирован")
                self.password_input.clear()
                self.password_input.setFocus()
                return

            # Проверка, есть ли пациент для этого пользователя
            if role == "Пользователь":
                self.cursor.execute(
                    "SELECT patientid, medicalcardid FROM patient WHERE userid = %s",
                    (user_id,)
                )
                patient = self.cursor.fetchone()
                if not patient:
                    # Показываем диалог для ввода данных пациента
                    first_login_dialog = FirstLoginDialog(self, user_id=user_id)
                    if not first_login_dialog.exec():
                        self.password_input.clear()
                        self.password_input.setFocus()
                        return  # Пользователь отменил ввод данных
                else:
                    patient_id, medicalcard_id = patient
                    if medicalcard_id is None:
                        # Показываем диалог для создания медицинской карты
                        medical_card_dialog = MedicalCardDialog(self, patient_id=patient_id)
                        if not medical_card_dialog.exec():
                            self.password_input.clear()
                            self.password_input.setFocus()
                            return  # Пользователь отменил создание медицинской карты

            logging.debug(f"Авторизация успешна: user_id={user_id}, role={role}")
            QMessageBox.information(self, "Успех", f"Авторизация прошла успешно!")
            self.close()

            # Открываем соответствующее приложение
            if role == "Администратор":
                logging.debug("Открытие AdminApp")
                self.admin_window = AdminApp()
                self.admin_window.show()
            elif role == "Сотрудник":
                logging.debug("Открытие EmployeeApp")
                self.employee_window = EmployeeApp(user_id=user_id, role=role)
                self.employee_window.show()
            elif role == "Пользователь":
                logging.debug("Открытие ClientApp")
                self.client_window = ClientApp(user_id=user_id, role=role)
                self.client_window.show()
            else:
                logging.error(f"Неизвестная роль пользователя: {role}")
                QMessageBox.warning(self, "Ошибка", "Неизвестная роль пользователя")

        except Exception as e:
            self.conn.rollback()
            logging.error(f"Ошибка при авторизации: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при авторизации: {str(e)}")
            self.password_input.clear()
            self.password_input.setFocus()

    def closeEvent(self, event):
        logging.debug("Закрытие окна LoginWindow")
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())