import sys
import psycopg2
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QPushButton, QMessageBox, QDialog, QFormLayout,
    QComboBox, QDateEdit, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLineEdit
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QColor, QPalette, QIcon
from MedicalCard import MedicalCardApp

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='client_app.log')

class ClientApp(QMainWindow):
    def __init__(self, user_id=None, role=None):
        super().__init__()
        self.user_id = user_id
        self.role = role
        self.setWindowTitle("Медицинская информационная система - Главное меню")
        self.setGeometry(100, 100, 600, 400)

        try:
            self.setWindowIcon(QIcon("icon.jpg"))
        except Exception as e:
            logging.error(f"Ошибка при установке иконки окна: {str(e)}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить иконку окна: {str(e)}")

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
                min-width: 150px;
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
            QDialog {{
                background-color: {self.med_light.name()};
            }}
            QComboBox, QDateEdit, QLineEdit {{
                border: 1px solid #d1d8e0;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                max-width: 300px;
            }}
            QLineEdit[readOnly="true"] {{
                background-color: #f0f0f0;
            }}
            QTableWidget {{
                background-color: {self.med_white.name()};
                border: 1px solid #d1d8e0;
                border-radius: 5px;
                gridline-color: #d1d8e0;
                font-size: 14px;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: {self.med_blue.name()};
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
        """)

        # Настройка цветовой палитры
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, self.med_light)
        palette.setColor(QPalette.ColorRole.Base, self.med_white)
        palette.setColor(QPalette.ColorRole.Highlight, self.med_blue)
        self.setPalette(palette)

        self.conn = None
        self.cursor = None
        self.patient_id = None
        self.doctors = []
        self.doctor_prices = {}
        self.connect_to_db()
        self.load_doctors()
        self.load_doctor_prices()
        self.load_patient_id()
        self.setup_ui()

    def connect_to_db(self):
        logging.debug("Попытка подключения к базе данных")
        try:
            self.conn = psycopg2.connect(
                dbname='Practice',
                user='postgres',
                password='123',
                host='localhost'
            )
            self.cursor = self.conn.cursor()
            logging.debug("Подключение к базе данных успешно")
        except Exception as e:
            logging.error(f"Ошибка подключения к БД: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к БД: {str(e)}")
            sys.exit(1)

    def load_doctors(self):
        logging.debug("Загрузка списка врачей")
        try:
            self.cursor.execute("""
                SELECT d.doctorid, 
                       d.secondname || ' ' || d.firstname || ' ' || COALESCE(d.midname, '') as doctor_name
                FROM doctor d
                ORDER BY d.secondname, d.firstname
            """)
            self.doctors = self.cursor.fetchall()
            logging.debug(f"Загружено {len(self.doctors)} врачей")
        except Exception as e:
            logging.error(f"Ошибка при загрузке врачей: {str(e)}")
            self.doctors = []
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить список врачей: {str(e)}")

    def load_doctor_prices(self):
        logging.debug("Загрузка цен врачей")
        try:
            self.cursor.execute("""
                SELECT d.doctorid, p.price
                FROM doctor d
                LEFT JOIN price p ON d.priceid = p.priceid
            """)
            self.doctor_prices = dict(self.cursor.fetchall())
            logging.debug(f"Загружены цены для {len(self.doctor_prices)} врачей")
        except Exception as e:
            logging.error(f"Ошибка при загрузке цен врачей: {str(e)}")
            self.doctor_prices = {}
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить цены врачей: {str(e)}")

    def load_patient_id(self):
        logging.debug("Загрузка ID пациента")
        try:
            if self.user_id is not None:
                self.cursor.execute("""
                    SELECT patientid 
                    FROM patient 
                    WHERE userid = %s
                """, (self.user_id,))
                result = self.cursor.fetchone()
                if result:
                    self.patient_id = result[0]
                    logging.debug(f"ID пациента загружен: {self.patient_id}")
                else:
                    logging.warning(f"Пациент не найден для user_id: {self.user_id}")
                    QMessageBox.warning(self, "Предупреждение", "Пациент не найден для текущего пользователя!")
            else:
                logging.error("user_id не указан")
        except Exception as e:
            logging.error(f"Ошибка при загрузке ID пациента: {str(e)}")
            self.patient_id = None

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

        # Контейнер для кнопок
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)

        # Кнопка для перехода на окно Мед. карты
        self.medicalcard_btn = QPushButton("Мед. карты")
        self.medicalcard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.medicalcard_btn.clicked.connect(self.open_medicalcard)

        # Кнопка для записи на прием
        self.schedule_btn = QPushButton("Записаться на прием")
        self.schedule_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.schedule_btn.clicked.connect(self.show_schedule_dialog)

        # Кнопка выхода
        self.logout_btn = QPushButton("Выход")
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.clicked.connect(self.open_login)

        # Добавление кнопок в layout
        buttons_layout.addWidget(self.medicalcard_btn)
        buttons_layout.addWidget(self.schedule_btn)
        buttons_layout.addWidget(self.logout_btn)

        layout.addLayout(buttons_layout)

        # Растяжка для центрирования
        layout.addStretch()

    def show_schedule_dialog(self):
        logging.debug("Открытие диалога записи на прием")
        if self.role != "Пользователь" or not self.patient_id:
            logging.warning("Запись на прием доступна только для пользователей с определенным пациентом")
            QMessageBox.warning(self, "Ошибка", "Запись на прием доступна только для зарегистрированных пациентов")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Записаться на прием")
        dialog.setFixedSize(600, 650)  # Increased height to accommodate price field

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        doctor_combo = QComboBox()
        doctor_combo.addItem("Выберите врача", None)
        for doctor_id, doctor_name in self.doctors:
            doctor_combo.addItem(doctor_name, doctor_id)

        medical_card_combo = QComboBox()
        medical_card_combo.addItem("Выберите медицинскую карту", None)
        try:
            self.cursor.execute("""
                SELECT medicalcardid, type 
                FROM medicalcard 
                WHERE patientid = %s
                ORDER BY establishmentdate
            """, (self.patient_id,))
            medical_cards = self.cursor.fetchall()
            for card_id, card_type in medical_cards:
                medical_card_combo.addItem(f"{card_type} (ID: {card_id})", card_id)
        except Exception as e:
            logging.error(f"Ошибка при загрузке медицинских карт: {str(e)}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить медицинские карты: {str(e)}")

        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        date_input.setDisplayFormat("dd.MM.yyyy")

        time_table = QTableWidget()
        time_table.setColumnCount(1)
        time_table.setHorizontalHeaderLabels(["Время"])
        time_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        time_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        time_table.horizontalHeader().setStretchLastSection(True)
        time_table.verticalHeader().setVisible(False)
        time_table.setFixedHeight(300)

        price_input = QLineEdit()
        price_input.setReadOnly(True)
        price_input.setPlaceholderText("Цена будет установлена автоматически")

        selected_time = [None]  # Store selected time in a list to allow modification in nested function

        def update_time_table():
            try:
                # Generate time slots from 8:00 to 16:00 with 30-minute intervals
                start_hour = 8
                end_hour = 16
                slots_per_hour = 2  # 30-minute intervals
                time_slots = []
                for hour in range(start_hour, end_hour):
                    for minute in range(0, 60, 30):
                        time = QTime(hour, minute)
                        time_slots.append(time)

                time_table.setRowCount(len(time_slots))
                for row, slot in enumerate(time_slots):
                    item = QTableWidgetItem(slot.toString("HH:mm"))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setBackground(QColor(0, 255, 0))  # Green by default (free)
                    time_table.setItem(row, 0, item)

                doctor_id = doctor_combo.currentData()
                appointment_date = date_input.date().toString("yyyy-MM-dd")
                if not doctor_id or not appointment_date:
                    return

                occupied_slots = []
                # Fetch occupied time slots
                self.cursor.execute("""
                    SELECT starttime, endtime
                    FROM appointment
                    WHERE doctorid = %s AND appointmentdate = %s
                """, (doctor_id, appointment_date))
                appointments = self.cursor.fetchall()

                for start_time, end_time in appointments:
                    start = QTime.fromString(str(start_time), "HH:mm:ss")
                    end = QTime.fromString(str(end_time), "HH:mm:ss")
                    current = start
                    while current < end:
                        occupied_slots.append(current)
                        current = current.addSecs(30 * 60)  # Increment by 30 minutes

                for row, slot in enumerate(time_slots):
                    item = time_table.item(row, 0)
                    if slot in occupied_slots:
                        item.setBackground(QColor(255, 0, 0))  # Red for occupied
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    else:
                        item.setBackground(QColor(0, 255, 0))  # Green for free
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable)

            except Exception as e:
                logging.error(f"Ошибка при обновлении таблицы времени: {str(e)}")
                QMessageBox.warning(dialog, "Ошибка", f"Не удалось загрузить временные слоты: {str(e)}")

        def update_price():
            doctor_id = doctor_combo.currentData()
            price = self.doctor_prices.get(doctor_id, None)
            price_input.setText(f"{price:.2f}" if price is not None else "")

        def on_time_table_clicked():
            selected_items = time_table.selectedItems()
            if selected_items:
                selected_time[0] = QTime.fromString(selected_items[0].text(), "HH:mm")

        doctor_combo.currentIndexChanged.connect(update_time_table)
        doctor_combo.currentIndexChanged.connect(update_price)
        date_input.dateChanged.connect(update_time_table)
        time_table.itemClicked.connect(on_time_table_clicked)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(20)
        ok_btn = QPushButton("Записаться")
        cancel_btn = QPushButton("Отмена")
        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Врач:", doctor_combo)
        layout.addRow("Медицинская карта:", medical_card_combo)
        layout.addRow("Дата:", date_input)
        layout.addRow("Доступное время:", time_table)
        layout.addRow("Цена:", price_input)
        layout.addRow(btn_box)

        def schedule_appointment():
            try:
                doctor_id = doctor_combo.currentData()
                medical_card_id = medical_card_combo.currentData()
                appointment_date = date_input.date().toString("yyyy-MM-dd")
                if selected_time[0] is None:
                    QMessageBox.warning(dialog, "Ошибка", "Выберите время из таблицы")
                    return
                start_time = selected_time[0].toString("HH:mm:ss")
                end_time = selected_time[0].addSecs(1800).toString("HH:mm:ss")  # 30 minutes later
                price = price_input.text().strip()

                if not all([doctor_id, medical_card_id, appointment_date, start_time, price]):
                    QMessageBox.warning(dialog, "Ошибка", "Заполните все обязательные поля, включая врача для установки цены")
                    return

                # Check for overlapping appointments
                self.cursor.execute("""
                    SELECT COUNT(*) 
                    FROM appointment 
                    WHERE doctorid = %s 
                    AND appointmentdate = %s 
                    AND (
                        (starttime <= %s AND endtime > %s) OR
                        (starttime < %s AND endtime >= %s) OR
                        (starttime >= %s AND endtime <= %s)
                    )
                """, (doctor_id, appointment_date, start_time, start_time, end_time, end_time, start_time, end_time))
                overlap_count = self.cursor.fetchone()[0]
                if overlap_count > 0:
                    QMessageBox.warning(dialog, "Ошибка", "В это время врач уже занят")
                    return

                price_value = float(price) if price else None

                self.cursor.execute(
                    """INSERT INTO appointment 
                    (patientid, medicalcardid, doctorid, appointmentdate, starttime, endtime, status, appointmentprice) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (self.patient_id, medical_card_id, doctor_id, appointment_date, start_time, end_time, "В процессе", price_value)
                )
                self.conn.commit()
                QMessageBox.information(dialog, "Успех", "Вы успешно записались на прием")
                dialog.close()
            except Exception as e:
                self.conn.rollback()
                logging.error(f"Ошибка при записи на прием: {str(e)}")
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось записаться на прием:\n{str(e)}")

        ok_btn.clicked.connect(schedule_appointment)
        cancel_btn.clicked.connect(dialog.close)

        # Initial table update
        update_time_table()

        dialog.exec()

    def open_medicalcard(self):
        if MedicalCardApp is None:
            QMessageBox.critical(self, "Ошибка", "Модуль 'Мед. карты' не найден.")
            return
        self.medicalcard_window = MedicalCardApp(user_id=self.user_id, role=self.role)
        self.medicalcard_window.show()

    def open_login(self):
        """Закрывает текущее окно и открывает окно авторизации"""
        try:
            from Login import LoginWindow
            self.close()
            self.login_window = LoginWindow()
            self.login_window.show()
        except ImportError as e:
            logging.error(f"Ошибка импорта LoginWindow: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно авторизации: {str(e)}")

    def closeEvent(self, event):
        logging.debug("Закрытие окна ClientApp")
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ClientApp(user_id=1, role="Пользователь")
    window.show()
    sys.exit(app.exec())