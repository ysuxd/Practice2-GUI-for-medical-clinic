import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette,QIcon

from Appointment import AppointmentsApp
from Diagnosis import DiagnosisApp
from JobTitle import JobTitleApp
from Specialization import SpecializationApp
from Doctor import DoctorsApp
from MedicalCard import MedicalCardApp
from Users import UsersApp
from Patient import PatientsApp

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Медицинская информационная система - Главное меню")
        self.setGeometry(100, 100, 600, 400)

        self.setWindowIcon(QIcon("icon.jpg"))

        # Медицинская цветовая схема
        self.med_blue = QColor(0, 109, 176)  # Основной синий цвет
        self.med_light = QColor(229, 243, 255)  # Светлый фон
        self.med_white = QColor(255, 255, 255)  # Белый
        self.med_red = QColor(200, 16, 46)  # Для предупреждений

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

        self.setup_ui()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title_label = QLabel("Главное меню")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {self.med_blue.name()};
                padding: 10px;
            }}
        """)
        layout.addWidget(title_label)

        # Контейнер для кнопок (две колонки)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        # Левая колонка кнопок
        left_column = QVBoxLayout()
        left_column.setSpacing(10)

        # Правая колонка кнопок
        right_column = QVBoxLayout()
        right_column.setSpacing(10)

        # Создание кнопок
        self.appointment_btn = QPushButton("Приёмы")
        self.diagnosis_btn = QPushButton("Диагнозы")
        self.doctor_btn = QPushButton("Врачи")
        self.jobtitle_btn = QPushButton("Должности")
        self.medicalcard_btn = QPushButton("Мед. карты")
        self.patient_btn = QPushButton("Пациенты")
        self.specialization_btn = QPushButton("Специализации")
        self.users_btn = QPushButton("Пользователи")
        self.logout_btn = QPushButton("Выход")

        # Установка курсора для кнопок
        for btn in [
            self.appointment_btn, self.diagnosis_btn, self.doctor_btn, self.jobtitle_btn,
            self.medicalcard_btn, self.patient_btn, self.specialization_btn, self.users_btn,
            self.logout_btn
        ]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Подключение кнопок к методам открытия окон
        self.appointment_btn.clicked.connect(self.open_appointment)
        self.diagnosis_btn.clicked.connect(self.open_diagnosis)
        self.doctor_btn.clicked.connect(self.open_doctor)
        self.jobtitle_btn.clicked.connect(self.open_jobtitle)
        self.medicalcard_btn.clicked.connect(self.open_medicalcard)
        self.patient_btn.clicked.connect(self.open_patient)
        self.specialization_btn.clicked.connect(self.open_specialization)
        self.users_btn.clicked.connect(self.open_users)
        self.logout_btn.clicked.connect(self.open_login)

        # Распределение кнопок по колонкам (без кнопки выхода)
        left_column.addWidget(self.appointment_btn)
        left_column.addWidget(self.diagnosis_btn)
        left_column.addWidget(self.doctor_btn)
        left_column.addWidget(self.jobtitle_btn)

        right_column.addWidget(self.medicalcard_btn)
        right_column.addWidget(self.patient_btn)
        right_column.addWidget(self.specialization_btn)
        right_column.addWidget(self.users_btn)

        # Добавление колонок в основной layout
        buttons_layout.addLayout(left_column)
        buttons_layout.addLayout(right_column)

        layout.addLayout(buttons_layout)

        # Создаем отдельный layout для кнопки "Выход" и центрируем её
        logout_layout = QHBoxLayout()
        logout_layout.addStretch()  # Растяжка слева
        logout_layout.addWidget(self.logout_btn)
        logout_layout.addStretch()  # Растяжка справа

        # Добавляем layout с кнопкой "Выход" в основной layout
        layout.addLayout(logout_layout)

        # Растяжка для центрирования всего контента по вертикали
        layout.addStretch()

    def open_appointment(self):
        if AppointmentsApp is None:
            QMessageBox.critical(self, "Ошибка", "Модуль 'Приёмы' не найден.")
            return
        self.appointment_window = AppointmentsApp()
        self.appointment_window.show()

    def open_diagnosis(self):
        if DiagnosisApp is None:
            QMessageBox.critical(self, "Ошибка", "Модуль 'Диагнозы' не найден.")
            return
        self.diagnosis_window = DiagnosisApp()
        self.diagnosis_window.show()

    def open_doctor(self):
        if DoctorsApp is None:
            QMessageBox.critical(self, "Ошибка", "Модуль 'Врачи' не найден.")
            return
        self.doctor_window = DoctorsApp()
        self.doctor_window.show()

    def open_jobtitle(self):
        if JobTitleApp is None:
            QMessageBox.critical(self, "Ошибка", "Модуль 'Должности' не найден.")
            return
        self.jobtitle_window = JobTitleApp()
        self.jobtitle_window.show()

    def open_medicalcard(self):
        if MedicalCardApp is None:
            QMessageBox.critical(self, "Ошибка", "Модуль 'Мед. карты' не найден.")
            return
        self.medicalcard_window = MedicalCardApp()
        self.medicalcard_window.show()

    def open_patient(self):
        if PatientsApp is None:
            QMessageBox.critical(self, "Ошибка", "Модуль 'Пациенты' не найден.")
            return
        self.patient_window = PatientsApp()
        self.patient_window.show()

    def open_specialization(self):
        if SpecializationApp is None:
            QMessageBox.critical(self, "Ошибка", "Модуль 'Специализации' не найден.")
            return
        self.specialization_window = SpecializationApp()
        self.specialization_window.show()

    def open_users(self):
        if UsersApp is None:
            QMessageBox.critical(self, "Ошибка", "Модуль 'Пользователи' не найден.")
            return
        self.users_window = UsersApp()
        self.users_window.show()

    def open_login(self):
        """Закрывает текущее окно и открывает окно авторизации"""
        from Login import LoginWindow
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainApp()
    window.show()
    sys.exit(app.exec())