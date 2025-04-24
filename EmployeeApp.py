import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette, QIcon

from MedicalCard import MedicalCardApp
from Doctor import DoctorsApp
from Appointment import AppointmentsApp

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class MainApp(QMainWindow):
    def __init__(self, user_id=None, role=None):
        super().__init__()
        logging.debug("Инициализация EmployeeApp")
        logging.debug(f"Переданные параметры: user_id={user_id}, role={role}")

        self.user_id = user_id
        self.role = role
        self.setWindowTitle("Медицинская информационная система - Главное меню сотрудника")
        self.setGeometry(100, 100, 600, 400)

        self.setWindowIcon(QIcon("icon.jpg"))

        # Медицинская цветовая схема
        self.med_blue = QColor(0, 109, 176)
        self.med_light = QColor(229, 243, 255)
        self.med_white = QColor(255, 255, 255)
        self.med_red = QColor(200, 16, 46)

        # Установка стиля приложения
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.med_light.name()};
            }}
            QPushButton {{
                background-color: {self.med_blue.name()};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 15px 20px;
                font-size: 16px;
                min-width: 200px;
            }}
            QPushButton:hover {{
                background-color: {self.med_blue.darker(110).name()};
            }}
            QPushButton:pressed {{
                background-color: {self.med_blue.darker(120).name()};
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
            }}
        """)

        # Настройка цветовой палитры
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, self.med_light)
        palette.setColor(QPalette.ColorRole.Base, self.med_white)
        palette.setColor(QPalette.ColorRole.Highlight, self.med_blue)
        self.setPalette(palette)

        logging.debug("Настройка UI EmployeeApp")
        self.setup_ui()
        logging.debug("UI EmployeeApp настроен успешно")

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title_label = QLabel("Главное меню сотрудника")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {self.med_blue.name()};
                padding: 10px;
            }}
        """)
        layout.addWidget(title_label)

        # Контейнер для кнопок
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)

        # Кнопка для перехода на окно Мед. карты
        self.medicalcard_btn = QPushButton("Мед. карты")
        self.medicalcard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.medicalcard_btn.clicked.connect(self.open_medicalcard)

        # Кнопка для перехода на окно Врачи
        self.doctors_btn = QPushButton("Врачи")
        self.doctors_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.doctors_btn.clicked.connect(self.open_doctors)

        # Кнопка для перехода на окно Приемы
        self.services_btn = QPushButton("Приемы")
        self.services_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.services_btn.clicked.connect(self.open_services)

        # Кнопка выхода
        self.logout_btn = QPushButton("Выход")
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.clicked.connect(self.open_login)

        # Добавление кнопок в layout
        buttons_layout.addWidget(self.medicalcard_btn)
        buttons_layout.addWidget(self.doctors_btn)
        buttons_layout.addWidget(self.services_btn)
        buttons_layout.addWidget(self.logout_btn)

        layout.addLayout(buttons_layout)

        # Растяжка для центрирования
        layout.addStretch()

    def open_medicalcard(self):
        logging.debug("Открытие MedicalCardApp")
        try:
            self.medicalcard_window = MedicalCardApp(user_id=self.user_id, role=self.role)
            self.medicalcard_window.show()
            logging.debug("MedicalCardApp открыт успешно")
        except Exception as e:
            logging.error(f"Ошибка при открытии MedicalCardApp: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть Мед. карты:\n{str(e)}")

    def open_doctors(self):
        logging.debug("Открытие DoctorsApp")
        try:
            self.doctors_window = DoctorsApp()
            self.doctors_window.show()
            logging.debug("DoctorsApp открыт успешно")
        except Exception as e:
            logging.error(f"Ошибка при открытии DoctorsApp: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть Врачи:\n{str(e)}")

    def open_services(self):
        logging.debug("Открытие AppointmentsApp")
        try:
            self.services_window = AppointmentsApp()
            self.services_window.show()
            logging.debug("AppointmentsApp открыт успешно")
        except Exception as e:
            logging.error(f"Ошибка при открытии AppointmentsApp: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть Приемы:\n{str(e)}")

    def open_login(self):
        """Закрывает текущее окно и открывает окно авторизации"""
        logging.debug("Переход на окно авторизации")
        try:
            from Login import LoginWindow
            self.close()
            self.login_window = LoginWindow()
            self.login_window.show()
            logging.debug("Окно авторизации открыто успешно")
        except Exception as e:
            logging.error(f"Ошибка при открытии окна авторизации: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно авторизации:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainApp(user_id=1, role="Сотрудник")  # Тестовый запуск
    window.show()
    sys.exit(app.exec())