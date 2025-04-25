import sys
import psycopg2
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit,
    QHeaderView, QDialog, QFormLayout, QDateEdit, QComboBox, QTimeEdit
)
from PyQt6.QtCore import Qt, QDate, QTime, QDateTime
from PyQt6.QtGui import QColor, QPalette, QIcon
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='Appointment.log'
)

class AppointmentsApp(QMainWindow):
    def __init__(self, medical_card_id=None, role=None, user_id=None):
        super().__init__()
        logging.debug(f"Инициализация AppointmentsApp с medical_card_id={medical_card_id}, role={role}, user_id={user_id}")
        self.medical_card_id = medical_card_id
        self.role = role
        self.user_id = user_id
        self.patient_id = None
        try:
            title = "Медицинская информационная система - Все приемы" if medical_card_id is None else f"Медицинская информационная система - Приемы (Карта №{medical_card_id})"
            self.setWindowTitle(title)
            self.setGeometry(100, 100, 1200, 800)

            try:
                self.setWindowIcon(QIcon('icon.jpg'))
                logging.debug("Иконка окна успешно установлена")
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
                QPushButton {{
                    background-color: {self.med_blue.name()};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 15px;
                    font-size: 14px;
                    min-width: 100px;
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
                QLineEdit, QDateEdit, QTimeEdit, QComboBox {{
                    border: 1px solid #d1d8e0;
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 14px;
                    max-width: 300px;
                }}
                QLineEdit[readOnly="true"] {{
                    background-color: #f0f0f0;
                }}
                QDialog {{
                    background-color: {self.med_light.name()};
                }}
            """)

            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Window, self.med_light)
            palette.setColor(QPalette.ColorRole.Base, self.med_white)
            palette.setColor(QPalette.ColorRole.Highlight, self.med_blue)
            self.setPalette(palette)

            self.conn = None
            self.cursor = None
            logging.debug("Вызов connect_to_db")
            self.connect_to_db()
            if self.role == "Пользователь" and self.medical_card_id is not None:
                self.load_patient_id()
            logging.debug("Вызов setup_ui")
            self.setup_ui()
            logging.debug("Вызов load_patients")
            self.load_patients()
            logging.debug("Вызов load_medical_cards")
            self.load_medical_cards()
            logging.debug("Вызов load_doctors")
            self.load_doctors()
            logging.debug("Вызов load_doctor_prices")
            self.load_doctor_prices()
            logging.debug("Вызов load_diagnoses")
            self.load_diagnoses()
            logging.debug("Вызов load_data")
            self.load_data()
            logging.debug("Инициализация AppointmentsApp завершена")
        except Exception as e:
            logging.error(f"Ошибка в инициализации AppointmentsApp: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось инициализировать форму: {str(e)}")
            self.close()

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
            self.cursor.execute("SELECT 1")
            logging.debug("Подключение к базе данных успешно")
        except Exception as e:
            logging.error(f"Ошибка подключения к БД: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к БД: {str(e)}")
            raise

    def load_patient_id(self):
        logging.debug("Загрузка ID пациента")
        try:
            if self.medical_card_id is not None:
                self.cursor.execute("""
                    SELECT patientid 
                    FROM patient 
                    WHERE medicalcardid = %s
                """, (self.medical_card_id,))
                result = self.cursor.fetchone()
                if result:
                    self.patient_id = result[0]
                    logging.debug(f"ID пациента загружен: {self.patient_id}")
                else:
                    logging.warning(f"Пациент не найден для medical_card_id: {self.medical_card_id}")
                    QMessageBox.warning(self, "Предупреждение", "Пациент не найден для данной медицинской карты!")
            else:
                logging.error("medical_card_id не указан")
        except Exception as e:
            logging.error(f"Ошибка при загрузке ID пациента: {str(e)}")
            self.patient_id = None

    def load_patients(self):
        logging.debug("Загрузка списка пациентов")
        try:
            if self.medical_card_id is None:
                query = """
                    SELECT p.patientid, 
                           p.lastname || ' ' || p.firstname || ' ' || COALESCE(p.midname, '') as patient_name, 
                           p.medicalcardid 
                    FROM patient p 
                    ORDER BY p.lastname, p.firstname
                """
                self.cursor.execute(query)
            else:
                query = """
                    SELECT p.patientid, 
                           p.lastname || ' ' || p.firstname || ' ' || COALESCE(p.midname, '') as patient_name, 
                           p.medicalcardid 
                    FROM patient p 
                    WHERE p.medicalcardid = %s
                    ORDER BY p.lastname, p.firstname
                """
                self.cursor.execute(query, (self.medical_card_id,))
            self.patients = self.cursor.fetchall()
            self.patient_dict = {patient[0]: patient[1] for patient in self.patients}
            logging.debug(f"Загружено {len(self.patients)} пациентов")
        except Exception as e:
            logging.error(f"Ошибка при загрузке пациентов: {str(e)}")
            self.conn.rollback()
            self.patients = []
            self.patient_dict = {}
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить пациентов: {str(e)}")

    def load_medical_cards(self):
        logging.debug("Загрузка списка медицинских карт")
        try:
            if self.medical_card_id is None:
                self.cursor.execute("SELECT medicalcardid FROM medicalcard ORDER BY medicalcardid")
            else:
                self.cursor.execute("SELECT medicalcardid FROM medicalcard WHERE medicalcardid = %s", (self.medical_card_id,))
            self.medical_cards = self.cursor.fetchall()
            logging.debug(f"Загружено {len(self.medical_cards)} медицинских карт")
        except Exception as e:
            logging.error(f"Ошибка при загрузке медицинских карт: {str(e)}")
            self.conn.rollback()
            self.medical_cards = []
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить медицинские карты: {str(e)}")

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
            self.doctor_dict = {doctor[0]: doctor[1] for doctor in self.doctors}
            logging.debug(f"Загружено {len(self.doctors)} врачей")
        except Exception as e:
            logging.error(f"Ошибка при загрузке врачей: {str(e)}")
            self.conn.rollback()
            self.doctors = []
            self.doctor_dict = {}
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить врачей: {str(e)}")

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
            self.conn.rollback()
            self.doctor_prices = {}
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить цены врачей: {str(e)}")

    def load_diagnoses(self):
        logging.debug("Загрузка списка диагнозов")
        try:
            self.cursor.execute("""
                SELECT diagnosisid, diagnosisname 
                FROM diagnosis
                ORDER BY diagnosisname
            """)
            self.diagnoses = self.cursor.fetchall()
            self.diagnosis_dict = {diagnosis[0]: diagnosis[1] for diagnosis in self.diagnoses}
            logging.debug(f"Загружено {len(self.diagnoses)} диагнозов")
        except Exception as e:
            logging.error(f"Ошибка при загрузке диагнозов: {str(e)}")
            self.conn.rollback()
            self.diagnoses = []
            self.diagnosis_dict = {}
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить диагнозы: {str(e)}")

    def setup_ui(self):
        logging.debug("Настройка пользовательского интерфейса")
        try:
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            title_text = "Управление приемами" if self.medical_card_id is None else f"Управление приемами (Медицинская карта №{self.medical_card_id})"
            title_label = QLabel(title_text)
            title_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 18px;
                    font-weight: bold;
                    color: {self.med_blue.name()};
                    padding: 10px;
                }}
            """)
            layout.addWidget(title_label)

            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(10)

            # Initialize buttons
            self.add_btn = QPushButton("Добавить")
            self.edit_btn = QPushButton("Редактировать")
            self.delete_btn = QPushButton("Удалить")
            self.refresh_btn = QPushButton("Обновить")
            self.pdf_btn = QPushButton("Создать PDF")
            self.schedule_btn = QPushButton("Записаться на прием")

            # Set cursor for all buttons
            for btn in [self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn, self.pdf_btn, self.schedule_btn]:
                btn.setCursor(Qt.CursorShape.PointingHandCursor)

            # Connect signals for admin buttons
            try:
                self.add_btn.clicked.connect(self.show_add_dialog)
                logging.debug("Сигнал add_btn.clicked подключен")
            except Exception as e:
                logging.error(f"Ошибка подключения add_btn.clicked: {str(e)}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка подключения сигнала add_btn: {str(e)}")

            try:
                self.edit_btn.clicked.connect(self.show_edit_dialog)
                logging.debug("Сигнал edit_btn.clicked подключен")
            except Exception as e:
                logging.error(f"Ошибка подключения edit_btn.clicked: {str(e)}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка подключения сигнала edit_btn: {str(e)}")

            try:
                self.delete_btn.clicked.connect(self.delete_appointment)
                logging.debug("Сигнал delete_btn.clicked подключен")
            except Exception as e:
                logging.error(f"Ошибка подключения delete_btn.clicked: {str(e)}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка подключения сигнала delete_btn: {str(e)}")

            try:
                self.refresh_btn.clicked.connect(self.refresh_all)
                logging.debug("Сигнал refresh_btn.clicked подключен")
            except Exception as e:
                logging.error(f"Ошибка подключения refresh_btn.clicked: {str(e)}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка подключения сигнала refresh_btn: {str(e)}")

            try:
                self.pdf_btn.clicked.connect(self.generate_pdf)
                logging.debug("Сигнал pdf_btn.clicked подключен")
            except Exception as e:
                logging.error(f"Ошибка подключения pdf_btn.clicked: {str(e)}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка подключения сигнала pdf_btn: {str(e)}")

            try:
                self.schedule_btn.clicked.connect(self.show_schedule_dialog)
                logging.debug("Сигнал schedule_btn.clicked подключен")
            except Exception as e:
                logging.error(f"Ошибка подключения schedule_btn.clicked: {str(e)}")
                QMessageBox.critical(self, "Ошибка", f"Ошибка подключения сигнала schedule_btn: {str(e)}")

            # Conditionally add buttons based on role
            if self.role != "Пользователь":
                btn_layout.addWidget(self.add_btn)
                btn_layout.addWidget(self.edit_btn)
                btn_layout.addWidget(self.delete_btn)
                btn_layout.addWidget(self.refresh_btn)
                btn_layout.addWidget(self.pdf_btn)
            else:
                btn_layout.addWidget(self.schedule_btn)

            self.table = QTableWidget()
            self.table.setColumnCount(10)
            self.table.setHorizontalHeaderLabels([
                "ID", "Пациент", "Номер мед. карты", "Врач", "Дата",
                "Время начала", "Время окончания", "Статус", "Диагноз", "Цена"
            ])
            self.table.setColumnHidden(0, True)

            self.table.setWordWrap(True)
            self.table.setTextElideMode(Qt.TextElideMode.ElideNone)

            header = self.table.horizontalHeader()
            for col in range(self.table.columnCount()):
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

            self.table.setColumnWidth(1, 150)  # Пациент
            self.table.setColumnWidth(3, 150)  # Врач
            self.table.setColumnWidth(8, 200)  # Диагноз

            self.table.verticalHeader().setVisible(False)

            self.table.setAlternatingRowColors(True)
            self.table.setStyleSheet("""
                QTableWidget {
                    alternate-background-color: #f5f5f5;
                }
            """)

            layout.addLayout(btn_layout)
            layout.addWidget(self.table)
            logging.debug("Интерфейс успешно настроен")
        except Exception as e:
            logging.error(f"Ошибка при настройке интерфейса: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при настройке интерфейса: {str(e)}")

    def show_schedule_dialog(self):
        logging.debug("Открытие диалога записи на прием")
        if self.role != "Пользователь" or not self.patient_id:
            logging.warning("Запись на прием доступна только для пользователей с определенным пациентом")
            QMessageBox.warning(self, "Ошибка", "Запись на прием доступна только для зарегистрированных пациентов")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Записаться на прием")
        dialog.setFixedSize(600, 650)

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
            for i in range(medical_card_combo.count()):
                if medical_card_combo.itemData(i) == self.medical_card_id:
                    medical_card_combo.setCurrentIndex(i)
                    break
        except Exception as e:
            logging.error(f"Ошибка при загрузке медицинских карт: {str(e)}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить медицинские карты: {str(e)}")

        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        date_input.setDisplayFormat("dd.MM.yyyy")
        date_input.setMinimumDate(QDate.currentDate())  # Prevent past dates

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

        selected_time = [None]

        def update_time_table():
            try:
                start_hour = 8
                end_hour = 16
                slots_per_hour = 2
                time_slots = []
                current_date = QDate.currentDate()
                selected_date = date_input.date()
                now = QTime.currentTime()

                for hour in range(start_hour, end_hour):
                    for minute in range(0, 60, 30):
                        time = QTime(hour, minute)
                        time_slots.append(time)

                time_table.setRowCount(len(time_slots))
                for row, slot in enumerate(time_slots):
                    item = QTableWidgetItem(slot.toString("HH:mm"))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setBackground(QColor(0, 255, 0))
                    if selected_date == current_date and slot < now:
                        item.setBackground(QColor(128, 128, 128))  # Gray for past times
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    time_table.setItem(row, 0, item)

                doctor_id = doctor_combo.currentData()
                appointment_date = date_input.date().toString("yyyy-MM-dd")
                if not doctor_id or not appointment_date:
                    return

                occupied_slots = []
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
                        current = current.addSecs(30 * 60)

                for row, slot in enumerate(time_slots):
                    item = time_table.item(row, 0)
                    if slot in occupied_slots:
                        item.setBackground(QColor(255, 0, 0))
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    elif selected_date == current_date and slot < now:
                        item.setBackground(QColor(128, 128, 128))
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    else:
                        item.setBackground(QColor(0, 255, 0))
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
                appointment_date = date_input.date()
                if selected_time[0] is None:
                    QMessageBox.warning(dialog, "Ошибка", "Выберите время из таблицы")
                    return
                start_time = selected_time[0].toString("HH:mm:ss")
                end_time = selected_time[0].addSecs(1800).toString("HH:mm:ss")
                price = price_input.text().strip()

                current_date = QDate.currentDate()
                current_time = QTime.currentTime()
                appointment_datetime = QDateTime(appointment_date, selected_time[0])
                current_datetime = QDateTime(current_date, current_time)

                if appointment_datetime < current_datetime:
                    QMessageBox.warning(dialog, "Ошибка", "Нельзя записаться на прошедшую дату или время")
                    return

                if not all([doctor_id, medical_card_id, appointment_date, start_time, price]):
                    QMessageBox.warning(dialog, "Ошибка", "Заполните все обязательные поля, включая врача для установки цены")
                    return

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
                """, (doctor_id, appointment_date.toString("yyyy-MM-dd"), start_time, start_time, end_time, end_time, start_time, end_time))
                overlap_count = self.cursor.fetchone()[0]
                if overlap_count > 0:
                    QMessageBox.warning(dialog, "Ошибка", "В это время врач уже занят")
                    return

                price_value = float(price) if price else None

                self.cursor.execute(
                    """INSERT INTO appointment 
                    (patientid, medicalcardid, doctorid, appointmentdate, starttime, endtime, status, appointmentprice) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (self.patient_id, medical_card_id, doctor_id, appointment_date.toString("yyyy-MM-dd"), start_time, end_time, "В процессе", price_value)
                )
                self.conn.commit()
                QMessageBox.information(dialog, "Успех", "Вы успешно записались на прием")
                self.load_data()
                dialog.close()
            except Exception as e:
                self.conn.rollback()
                logging.error(f"Ошибка при записи на прием: {str(e)}")
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось записаться на прием:\n{str(e)}")

        ok_btn.clicked.connect(schedule_appointment)
        cancel_btn.clicked.connect(dialog.close)

        update_time_table()

        dialog.exec()

    def show_add_dialog(self):
        logging.debug("Открытие диалога добавления приема")
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Добавить прием")
            dialog.setFixedSize(500, 700)

            layout = QFormLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            patient_combo = QComboBox()
            patient_combo.addItem("Не выбрано", None)
            for patient in self.patients:
                patient_combo.addItem(patient[1], patient[0])

            medical_card_combo = QComboBox()
            medical_card_combo.addItem("Не выбрано", None)
            for card_id, in self.medical_cards:
                medical_card_combo.addItem(str(card_id), card_id)
            medical_card_combo.setEnabled(False)

            def update_medical_card():
                selected_patient_id = patient_combo.currentData()
                medical_card_combo.setCurrentIndex(0)
                if selected_patient_id:
                    for patient in self.patients:
                        if patient[0] == selected_patient_id:
                            medical_card_id = patient[2]
                            for i in range(medical_card_combo.count()):
                                if medical_card_combo.itemData(i) == medical_card_id:
                                    medical_card_combo.setCurrentIndex(i)
                                    break
                            break

            patient_combo.currentIndexChanged.connect(update_medical_card)

            doctor_combo = QComboBox()
            doctor_combo.addItem("Не выбрано", None)
            for doctor in self.doctors:
                doctor_combo.addItem(doctor[1], doctor[0])

            diagnosis_combo = QComboBox()
            diagnosis_combo.addItem("Не выбрано", None)
            for diagnosis in self.diagnoses:
                diagnosis_combo.addItem(diagnosis[1], diagnosis[0])

            date_input = QDateEdit()
            date_input.setDisplayFormat("dd.MM.yyyy")
            date_input.setDate(QDate.currentDate())
            date_input.setCalendarPopup(True)
            date_input.setMinimumDate(QDate.currentDate())  # Prevent past dates

            time_table = QTableWidget()
            time_table.setColumnCount(1)
            time_table.setHorizontalHeaderLabels(["Время"])
            time_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            time_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            time_table.horizontalHeader().setStretchLastSection(True)
            time_table.verticalHeader().setVisible(False)
            time_table.setFixedHeight(150)

            selected_time = [None]

            def update_time_table():
                try:
                    start_hour = 8
                    end_hour = 16
                    slots_per_hour = 2
                    time_slots = []
                    current_date = QDate.currentDate()
                    selected_date = date_input.date()
                    now = QTime.currentTime()

                    for hour in range(start_hour, end_hour):
                        for minute in range(0, 60, 30):
                            time = QTime(hour, minute)
                            time_slots.append(time)

                    time_table.setRowCount(len(time_slots))
                    for row, slot in enumerate(time_slots):
                        item = QTableWidgetItem(slot.toString("HH:mm"))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        item.setBackground(QColor(0, 255, 0))
                        if selected_date == current_date and slot < now:
                            item.setBackground(QColor(128, 128, 128))
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                        time_table.setItem(row, 0, item)

                    doctor_id = doctor_combo.currentData()
                    appointment_date = date_input.date().toString("yyyy-MM-dd")
                    if not doctor_id or not appointment_date:
                        return

                    occupied_slots = []
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
                            current = current.addSecs(30 * 60)

                    for row, slot in enumerate(time_slots):
                        item = time_table.item(row, 0)
                        if slot in occupied_slots:
                            item.setBackground(QColor(255, 0, 0))
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                        elif selected_date == current_date and slot < now:
                            item.setBackground(QColor(128, 128, 128))
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                        else:
                            item.setBackground(QColor(0, 255, 0))
                            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable)

                except Exception as e:
                    logging.error(f"Ошибка при обновлении таблицы времени: {str(e)}")
                    QMessageBox.warning(dialog, "Ошибка", f"Не удалось загрузить временные слоты: {str(e)}")

            def on_time_table_clicked():
                selected_items = time_table.selectedItems()
                if selected_items:
                    selected_time[0] = QTime.fromString(selected_items[0].text(), "HH:mm")

            doctor_combo.currentIndexChanged.connect(update_time_table)
            date_input.dateChanged.connect(update_time_table)
            time_table.itemClicked.connect(on_time_table_clicked)

            status_combo = QComboBox()
            status_options = ["Завершён", "Отменён", "Назначен"]
            status_combo.addItems(status_options)
            status_combo.setCurrentText("Назначен")

            price_input = QLineEdit()
            price_input.setReadOnly(True)
            price_input.setPlaceholderText("Цена будет установлена автоматически")

            def update_price():
                doctor_id = doctor_combo.currentData()
                price = self.doctor_prices.get(doctor_id, None)
                price_input.setText(f"{price:.2f}" if price is not None else "")

            doctor_combo.currentIndexChanged.connect(update_price)

            btn_box = QHBoxLayout()
            btn_box.setSpacing(10)

            ok_btn = QPushButton("Добавить")
            cancel_btn = QPushButton("Отмена")

            btn_box.addWidget(ok_btn)
            btn_box.addWidget(cancel_btn)

            layout.addRow("Пациент:", patient_combo)
            layout.addRow("Номер мед. карты:", medical_card_combo)
            layout.addRow("Врач:", doctor_combo)
            layout.addRow("Диагноз:", diagnosis_combo)
            layout.addRow("Дата:", date_input)
            layout.addRow("Доступное время:", time_table)
            layout.addRow("Статус:", status_combo)
            layout.addRow("Цена:", price_input)
            layout.addRow(btn_box)

            def add_appointment():
                try:
                    patient_id = patient_combo.currentData()
                    medical_card_id = medical_card_combo.currentData()
                    doctor_id = doctor_combo.currentData()
                    diagnosis_id = diagnosis_combo.currentData()
                    date = date_input.date()
                    if selected_time[0] is None:
                        QMessageBox.warning(dialog, "Ошибка", "Выберите время из таблицы")
                        return
                    starttime = selected_time[0].toString("HH:mm:ss")
                    endtime = selected_time[0].addSecs(1800).toString("HH:mm:ss")
                    status = status_combo.currentText()
                    price = price_input.text().strip()

                    current_date = QDate.currentDate()
                    current_time = QTime.currentTime()
                    appointment_datetime = QDateTime(date, selected_time[0])
                    current_datetime = QDateTime(current_date, current_time)

                    if appointment_datetime < current_datetime:
                        QMessageBox.warning(dialog, "Ошибка", "Нельзя добавить прием на прошедшую дату или время")
                        return

                    if not all([patient_id, medical_card_id, doctor_id, date, starttime, price]):
                        QMessageBox.warning(dialog, "Ошибка",
                                            "Заполните все обязательные поля, включая врача для установки цены")
                        return

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
                    """, (doctor_id, date.toString("yyyy-MM-dd"), starttime, starttime, endtime, endtime, starttime, endtime))
                    overlap_count = self.cursor.fetchone()[0]
                    if overlap_count > 0:
                        QMessageBox.warning(dialog, "Ошибка", "В это время врач уже занят")
                        return

                    price_value = float(price) if price else None

                    self.cursor.execute(
                        """INSERT INTO appointment 
                        (patientid, medicalcardid, doctorid, diagnosisid, appointmentdate, 
                        starttime, endtime, status, appointmentprice) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
                        RETURNING appointmentid""",
                        (patient_id, medical_card_id, doctor_id, diagnosis_id, date.toString("yyyy-MM-dd"), starttime, endtime,
                         status or None, price_value))

                    new_id = self.cursor.fetchone()[0]
                    self.conn.commit()

                    row_pos = self.table.rowCount()
                    self.table.insertRow(row_pos)

                    patient_name = self.patient_dict.get(patient_id, "Неизвестный пациент")
                    doctor_name = self.doctor_dict.get(doctor_id, "Неизвестный врач")
                    diagnosis_name = self.diagnosis_dict.get(diagnosis_id, "Неизвестный диагноз")

                    formatted_date = date_input.date().toString("dd.MM.yyyy")
                    formatted_starttime = selected_time[0].toString("HH:mm")
                    formatted_endtime = selected_time[0].addSecs(1800).toString("HH:mm")
                    formatted_price = f"{price_value:.2f}" if price_value is not None else ""

                    columns = [
                        str(new_id), patient_name, str(medical_card_id), doctor_name,
                        formatted_date, formatted_starttime, formatted_endtime,
                        status or "", diagnosis_name, formatted_price
                    ]

                    for col_idx, value in enumerate(columns):
                        item = QTableWidgetItem(value)
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        if col_idx == 8:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                        else:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.table.setItem(row_pos, col_idx, item)

                    self.table.resizeRowToContents(row_pos)

                    dialog.close()
                    logging.debug("Прием успешно добавлен")
                except Exception as e:
                    self.conn.rollback()
                    logging.error(f"Ошибка при добавлении приема: {str(e)}")
                    QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить прием:\n{str(e)}")

            ok_btn.clicked.connect(add_appointment)
            cancel_btn.clicked.connect(dialog.close)

            update_time_table()

            dialog.exec()
        except Exception as e:
            logging.error(f"Ошибка в диалоге добавления: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка в диалоге добавления: {str(e)}")

    def show_edit_dialog(self):
        logging.debug("Открытие диалога редактирования приема")
        try:
            selected_items = self.table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Ошибка", "Выберите прием для редактирования")
                return

            row = selected_items[0].row()
            appointment_id = int(self.table.item(row, 0).text())

            current_patient_name = self.table.item(row, 1).text()
            current_medical_card = self.table.item(row, 2).text()
            current_doctor_name = self.table.item(row, 3).text()
            current_date = QDate.fromString(self.table.item(row, 4).text(), "dd.MM.yyyy")
            current_starttime = QTime.fromString(self.table.item(row, 5).text(), "HH:mm")
            current_endtime = QTime.fromString(self.table.item(row, 6).text(), "HH:mm")
            current_status = self.table.item(row, 7).text()
            current_diagnosis_name = self.table.item(row, 8).text()
            current_price = self.table.item(row, 9).text()

            current_patient_id = None
            for patient_id, patient_name in self.patient_dict.items():
                if patient_name == current_patient_name:
                    current_patient_id = patient_id
                    break

            current_doctor_id = None
            for doctor_id, doctor_name in self.doctor_dict.items():
                if doctor_name == current_doctor_name:
                    current_doctor_id = doctor_id
                    break

            current_diagnosis_id = None
            for diagnosis_id, diagnosis_name in self.diagnosis_dict.items():
                if diagnosis_name == current_diagnosis_name:
                    current_diagnosis_id = diagnosis_id
                    break

            dialog = QDialog(self)
            dialog.setWindowTitle("Редактировать прием")
            dialog.setFixedSize(500, 700)

            layout = QFormLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            patient_combo = QComboBox()
            patient_combo.addItem("Не выбрано", None)
            current_patient_index = 0
            for i, patient in enumerate(self.patients):
                patient_combo.addItem(patient[1], patient[0])
                if patient[0] == current_patient_id:
                    current_patient_index = i + 1
            patient_combo.setCurrentIndex(current_patient_index)

            medical_card_combo = QComboBox()
            medical_card_combo.addItem("Не выбрано", None)
            current_card_index = 0
            for i, (card_id,) in enumerate(self.medical_cards):
                medical_card_combo.addItem(str(card_id), card_id)
                if str(card_id) == current_medical_card:
                    current_card_index = i + 1
            medical_card_combo.setCurrentIndex(current_card_index)
            medical_card_combo.setEnabled(False)

            def update_medical_card():
                selected_patient_id = patient_combo.currentData()
                medical_card_combo.setCurrentIndex(0)
                if selected_patient_id:
                    for patient in self.patients:
                        if patient[0] == selected_patient_id:
                            medical_card_id = patient[2]
                            for i in range(medical_card_combo.count()):
                                if medical_card_combo.itemData(i) == medical_card_id:
                                    medical_card_combo.setCurrentIndex(i)
                                    break
                            break

            patient_combo.currentIndexChanged.connect(update_medical_card)

            doctor_combo = QComboBox()
            doctor_combo.addItem("Не выбрано", None)
            current_doctor_index = 0
            for i, doctor in enumerate(self.doctors):
                doctor_combo.addItem(doctor[1], doctor[0])
                if doctor[0] == current_doctor_id:
                    current_doctor_index = i + 1
            doctor_combo.setCurrentIndex(current_doctor_index)

            diagnosis_combo = QComboBox()
            diagnosis_combo.addItem("Не выбрано", None)
            current_diagnosis_index = 0
            for i, diagnosis in enumerate(self.diagnoses):
                diagnosis_combo.addItem(diagnosis[1], diagnosis[0])
                if diagnosis[0] == current_diagnosis_id:
                    current_diagnosis_index = i + 1
            diagnosis_combo.setCurrentIndex(current_diagnosis_index)

            date_input = QDateEdit(current_date)
            date_input.setDisplayFormat("dd.MM.yyyy")
            date_input.setCalendarPopup(True)
            date_input.setMinimumDate(QDate.currentDate())  # Prevent past dates

            time_table = QTableWidget()
            time_table.setColumnCount(1)
            time_table.setHorizontalHeaderLabels(["Время"])
            time_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            time_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            time_table.horizontalHeader().setStretchLastSection(True)
            time_table.verticalHeader().setVisible(False)
            time_table.setFixedHeight(150)

            selected_time = [current_starttime]

            def update_time_table():
                try:
                    start_hour = 8
                    end_hour = 16
                    slots_per_hour = 2
                    time_slots = []
                    current_date = QDate.currentDate()
                    selected_date = date_input.date()
                    now = QTime.currentTime()

                    for hour in range(start_hour, end_hour):
                        for minute in range(0, 60, 30):
                            time = QTime(hour, minute)
                            time_slots.append(time)

                    time_table.setRowCount(len(time_slots))
                    for row, slot in enumerate(time_slots):
                        item = QTableWidgetItem(slot.toString("HH:mm"))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        item.setBackground(QColor(0, 255, 0))
                        if selected_date == current_date and slot < now:
                            item.setBackground(QColor(128, 128, 128))
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                        time_table.setItem(row, 0, item)

                    doctor_id = doctor_combo.currentData()
                    appointment_date = date_input.date().toString("yyyy-MM-dd")
                    if not doctor_id or not appointment_date:
                        return

                    occupied_slots = []
                    self.cursor.execute("""
                        SELECT starttime, endtime
                        FROM appointment
                        WHERE doctorid = %s AND appointmentdate = %s AND appointmentid != %s
                    """, (doctor_id, appointment_date, appointment_id))
                    appointments = self.cursor.fetchall()

                    for start_time, end_time in appointments:
                        start = QTime.fromString(str(start_time), "HH:mm:ss")
                        end = QTime.fromString(str(end_time), "HH:mm:ss")
                        current = start
                        while current < end:
                            occupied_slots.append(current)
                            current = current.addSecs(30 * 60)

                    for row, slot in enumerate(time_slots):
                        item = time_table.item(row, 0)
                        if slot in occupied_slots:
                            item.setBackground(QColor(255, 0, 0))
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                        elif selected_date == current_date and slot < now:
                            item.setBackground(QColor(128, 128, 128))
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                        else:
                            item.setBackground(QColor(0, 255, 0))
                            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsSelectable)

                        if slot == current_starttime:
                            time_table.setCurrentCell(row, 0)

                except Exception as e:
                    logging.error(f"Ошибка при обновлении таблицы времени: {str(e)}")
                    QMessageBox.warning(dialog, "Ошибка", f"Не удалось загрузить временные слоты: {str(e)}")

            def on_time_table_clicked():
                selected_items = time_table.selectedItems()
                if selected_items:
                    selected_time[0] = QTime.fromString(selected_items[0].text(), "HH:mm")

            doctor_combo.currentIndexChanged.connect(update_time_table)
            date_input.dateChanged.connect(update_time_table)
            time_table.itemClicked.connect(on_time_table_clicked)

            status_combo = QComboBox()
            status_options = ["Завершён", "Отменён", "Назначен"]
            status_combo.addItems(status_options)
            status_combo.setCurrentText(current_status if current_status in status_options else "Назначен")

            price_input = QLineEdit(current_price)
            price_input.setReadOnly(True)

            def update_price():
                doctor_id = doctor_combo.currentData()
                price = self.doctor_prices.get(doctor_id, None)
                price_input.setText(f"{price:.2f}" if price is not None else "")

            doctor_combo.currentIndexChanged.connect(update_price)

            btn_box = QHBoxLayout()
            btn_box.setSpacing(10)

            ok_btn = QPushButton("Сохранить")
            cancel_btn = QPushButton("Отмена")

            btn_box.addWidget(ok_btn)
            btn_box.addWidget(cancel_btn)

            layout.addRow("Пациент:", patient_combo)
            layout.addRow("Номер мед. карты:", medical_card_combo)
            layout.addRow("Врач:", doctor_combo)
            layout.addRow("Диагноз:", diagnosis_combo)
            layout.addRow("Дата:", date_input)
            layout.addRow("Доступное время:", time_table)
            layout.addRow("Статус:", status_combo)
            layout.addRow("Цена:", price_input)
            layout.addRow(btn_box)

            def update_appointment():
                try:
                    patient_id = patient_combo.currentData()
                    medical_card_id = medical_card_combo.currentData()
                    doctor_id = doctor_combo.currentData()
                    diagnosis_id = diagnosis_combo.currentData()
                    date = date_input.date()
                    if selected_time[0] is None:
                        QMessageBox.warning(dialog, "Ошибка", "Выберите время из таблицы")
                        return
                    starttime = selected_time[0].toString("HH:mm:ss")
                    endtime = selected_time[0].addSecs(1800).toString("HH:mm:ss")
                    status = status_combo.currentText()
                    price = price_input.text().strip()

                    current_date = QDate.currentDate()
                    current_time = QTime.currentTime()
                    appointment_datetime = QDateTime(date, selected_time[0])
                    current_datetime = QDateTime(current_date, current_time)

                    if appointment_datetime < current_datetime:
                        QMessageBox.warning(dialog, "Ошибка", "Нельзя изменить прием на прошедшую дату или время")
                        return

                    if not all([patient_id, medical_card_id, doctor_id, date, starttime, price]):
                        QMessageBox.warning(dialog, "Ошибка",
                                            "Заполните все обязательные поля, включая врача для установки цены")
                        return

                    self.cursor.execute("""
                        SELECT COUNT(*) 
                        FROM appointment 
                        WHERE doctorid = %s 
                        AND appointmentdate = %s 
                        AND appointmentid != %s
                        AND (
                            (starttime <= %s AND endtime > %s) OR
                            (starttime < %s AND endtime >= %s) OR
                            (starttime >= %s AND endtime <= %s)
                        )
                    """, (doctor_id, date.toString("yyyy-MM-dd"), appointment_id, starttime, starttime, endtime, endtime, starttime, endtime))
                    overlap_count = self.cursor.fetchone()[0]
                    if overlap_count > 0:
                        QMessageBox.warning(dialog, "Ошибка", "В это время врач уже занят")
                        return

                    price_value = float(price) if price else None

                    self.cursor.execute(
                        """UPDATE appointment SET 
                        patientid = %s,
                        medicalcardid = %s,
                        doctorid = %s,
                        diagnosisid = %s,
                        appointmentdate = %s,
                        starttime = %s,
                        endtime = %s,
                        status = %s,
                        appointmentprice = %s
                        WHERE appointmentid = %s""",
                        (patient_id, medical_card_id, doctor_id, diagnosis_id, date.toString("yyyy-MM-dd"), starttime, endtime,
                         status or None, price_value, appointment_id))

                    self.conn.commit()

                    patient_name = self.patient_dict.get(patient_id, "Неизвестный пациент")
                    doctor_name = self.doctor_dict.get(doctor_id, "Неизвестный врач")
                    diagnosis_name = self.diagnosis_dict.get(diagnosis_id, "Неизвестный диагноз")
                    formatted_date = date_input.date().toString("dd.MM.yyyy")
                    formatted_starttime = selected_time[0].toString("HH:mm")
                    formatted_endtime = selected_time[0].addSecs(1800).toString("HH:mm")
                    formatted_price = f"{price_value:.2f}" if price_value is not None else ""

                    self.table.item(row, 1).setText(patient_name)
                    self.table.item(row, 2).setText(str(medical_card_id))
                    self.table.item(row, 3).setText(doctor_name)
                    self.table.item(row, 4).setText(formatted_date)
                    self.table.item(row, 5).setText(formatted_starttime)
                    self.table.item(row, 6).setText(formatted_endtime)
                    self.table.item(row, 7).setText(status or "")
                    self.table.item(row, 8).setText(diagnosis_name or "")
                    self.table.item(row, 8).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    self.table.item(row, 9).setText(formatted_price)

                    self.table.resizeRowToContents(row)

                    dialog.close()
                    logging.debug("Прием успешно обновлен")
                except Exception as e:
                    self.conn.rollback()
                    logging.error(f"Ошибка при обновлении приема: {str(e)}")
                    QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить данные приема:\n{str(e)}")

            ok_btn.clicked.connect(update_appointment)
            cancel_btn.clicked.connect(dialog.close)

            update_time_table()

            dialog.exec()
        except Exception as e:
            logging.error(f"Ошибка в диалоге редактирования: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка в диалоге редактирования: {str(e)}")

    def generate_pdf(self):
        logging.debug("Генерация PDF-файла")
        try:
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
                logging.debug("Шрифт DejaVuSans зарегистрирован")
            except Exception as e:
                logging.error(f"Не удалось загрузить шрифт: {str(e)}")
                QMessageBox.critical(self, "Ошибка", "Не удалось загрузить шрифт DejaVuSans.ttf")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if self.medical_card_id is not None and self.patients:
                patient_name = self.patients[0][1] if self.patients else "unknown_patient"
                patient_name_cleaned = patient_name.replace(" ", "_").replace("'", "").replace(",", "")
                pdf_filename = f"appointments_report_{patient_name_cleaned}_{timestamp}.pdf"
            else:
                pdf_filename = f"общий_отчёт_{timestamp}.pdf"

            page_width, page_height = A4
            left_margin = 36
            right_margin = 36
            top_margin = 36
            bottom_margin = 36
            available_width = page_width - left_margin - right_margin

            doc = SimpleDocTemplate(
                pdf_filename,
                pagesize=A4,
                leftMargin=left_margin,
                rightMargin=right_margin,
                topMargin=top_margin,
                bottomMargin=bottom_margin
            )
            elements = []

            styles = getSampleStyleSheet()
            styles['Title'].fontName = 'DejaVuSans'
            styles['Normal'].fontName = 'DejaVuSans'
            title = Paragraph("Отчёт по приёмам", styles['Title'])
            elements.append(title)
            elements.append(
                Paragraph(f"Дата создания: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", styles['Normal']))
            elements.append(Paragraph("<br/><br/>", styles['Normal']))

            data = []
            headers = ["Пациент/Мед.Карта", "Врач", "Дата/время", "Диагноз", "Статус", "Итог"]
            data.append(headers)

            for row in range(self.table.rowCount()):
                medical_card = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
                patient = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                doctor = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
                date = self.table.item(row, 4).text() if self.table.item(row, 4) else ""
                start_time = self.table.item(row, 5).text() if self.table.item(row, 5) else ""
                end_time = self.table.item(row, 6).text() if self.table.item(row, 6) else ""
                status = self.table.item(row, 7).text() if self.table.item(row, 7) else ""
                diagnosis = self.table.item(row, 8).text() if self.table.item(row, 8) else ""
                price = self.table.item(row, 9).text() if self.table.item(row, 9) else ""

                date_time = f"{date}\n{start_time}-{end_time}"
                medical_card_patient = f"{patient}\n№ мед. карты {medical_card}"
                if status == "Назначен":
                    status = "Назначен"

                row_data = [medical_card_patient, doctor, date_time, diagnosis, status, price]

                for col_idx, text in enumerate(row_data):
                    if col_idx in [0, 1, 2, 3, 4]:
                        style = styles['Normal'].clone('cell_style')
                        style.wordWrap = 'CJK'
                        if col_idx == 0:
                            style.fontSize = 8
                            style.leading = 10
                            style.alignment = 1
                        elif col_idx in [1, 2, 3]:
                            style.fontSize = 8
                            style.leading = 10
                        elif col_idx == 4:
                            style.fontSize = 7
                            style.leading = 8
                            style.alignment = 1
                        row_data[col_idx] = Paragraph(text, style)

                data.append(row_data)

            relative_widths = [25, 20, 15, 25, 10, 10]
            total_relative_width = sum(relative_widths)
            col_widths = [(width / total_relative_width) * available_width for width in relative_widths]

            table = Table(data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006DB0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
                ('WORDWRAP', (0, 0), (-1, -1), True),
                ('LEADING', (0, 0), (-1, -1), 12),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('VALIGN', (0, 1), (0, -1), 'TOP'),
                ('FONTSIZE', (0, 1), (0, -1), 8),
                ('LEADING', (0, 1), (0, -1), 10),
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),
                ('VALIGN', (3, 1), (3, -1), 'TOP'),
                ('FONTSIZE', (3, 1), (3, -1), 8),
                ('LEADING', (3, 1), (3, -1), 10),
                ('ALIGN', (4, 1), (4, -1), 'CENTER'),
                ('VALIGN', (4, 1), (4, -1), 'MIDDLE'),
                ('FONTSIZE', (4, 1), (4, -1), 7),
                ('LEADING', (4, 1), (4, -1), 8),
            ]))

            elements.append(table)
            doc.build(elements)

            QMessageBox.information(self, "Успех", f"PDF-файл успешно создан: {pdf_filename}")
            logging.debug("PDF-файл успешно создан")
        except Exception as e:
            logging.error(f"Ошибка при создании PDF: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать PDF-файл:\n{str(e)}")

    def refresh_all(self):
        logging.debug("Обновление всех данных")
        try:
            self.load_patients()
            self.load_medical_cards()
            self.load_doctors()
            self.load_doctor_prices()
            self.load_diagnoses()
            self.load_data()
        except Exception as e:
            logging.error(f"Ошибка при обновлении данных: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить данные: {str(e)}")

    def load_data(self):
        logging.debug(f"Загрузка данных для medical_card_id={self.medical_card_id}")
        if not hasattr(self, 'cursor') or not self.cursor:
            logging.error("Курсор не инициализирован")
            QMessageBox.critical(self, "Ошибка", "Курсор базы данных не инициализирован")
            return

        try:
            if self.medical_card_id is None:
                query = """
                    SELECT a.appointmentid, a.patientid, a.medicalcardid, a.doctorid, a.appointmentdate, 
                           a.starttime, a.endtime, a.status, a.diagnosisid, a.appointmentprice
                    FROM appointment a
                    ORDER BY a.appointmentdate, a.starttime
                """
                self.cursor.execute(query)
            else:
                query = """
                    SELECT a.appointmentid, a.patientid, a.medicalcardid, a.doctorid, a.appointmentdate, 
                           a.starttime, a.endtime, a.status, a.diagnosisid, a.appointmentprice
                    FROM appointment a
                    WHERE a.medicalcardid = %s
                    ORDER BY a.appointmentdate, a.starttime
                """
                self.cursor.execute(query, (self.medical_card_id,))
            data = self.cursor.fetchall()
            logging.debug(f"Получено {len(data)} записей о приемах")

            self.table.setRowCount(len(data))
            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    if col_idx == 1:
                        value = self.patient_dict.get(value, "Неизвестный пациент")
                    elif col_idx == 3:
                        value = self.doctor_dict.get(value, "Неизвестный врач")
                    elif col_idx == 4 and value is not None:
                        value = value.strftime("%d.%m.%Y")
                    elif col_idx in (5, 6) and value is not None:
                        value = value.strftime("%H:%M")
                    elif col_idx == 8:
                        value = self.diagnosis_dict.get(value, "Неизвестный диагноз")
                    elif col_idx == 9 and value is not None:
                        value = f"{value:.2f}"

                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    if col_idx == 8:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                        self.table.resizeRowToContents(row_idx)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    if row_idx % 2 == 0:
                        item.setForeground(QColor(53, 59, 72))
                    else:
                        item.setForeground(QColor(47, 53, 66))

                    self.table.setItem(row_idx, col_idx, item)

                self.table.resizeRowToContents(row_idx)

            logging.debug(f"Таблица заполнена {len(data)} записями")
        except Exception as e:
            logging.error(f"Ошибка при загрузке данных: {str(e)}")
            self.conn.rollback()
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить данные из базы:\n{str(e)}"
            )

    def delete_appointment(self):
        logging.debug("Удаление приема")
        try:
            selected_items = self.table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Ошибка", "Выберите прием для удаления")
                return

            row = selected_items[0].row()
            appointment_id = int(self.table.item(row, 0).text())
            appointment_date = self.table.item(row, 4).text()

            reply = QMessageBox.question(
                self, "Подтверждение",
                f"Вы уверены, что хотите удалить прием от {appointment_date}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                self.cursor.execute(
                    "DELETE FROM appointment WHERE appointmentid = %s",
                    (appointment_id,))
                self.conn.commit()
                self.table.removeRow(row)
                logging.debug("Прием успешно удален")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Ошибка при удалении приема: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить прием:\n{str(e)}")

    def closeEvent(self, event):
        logging.debug("Закрытие окна AppointmentsApp")
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
            logging.debug("Соединение с базой данных закрыто")
        except Exception as e:
            logging.error(f"Ошибка при закрытии соединения: {str(e)}")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = AppointmentsApp()
    window.show()
    sys.exit(app.exec())