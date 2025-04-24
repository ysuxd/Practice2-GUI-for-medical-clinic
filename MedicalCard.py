import sys
import psycopg2
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit,
    QHeaderView, QDialog, QFormLayout, QComboBox,
    QDateEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QPalette, QIcon
try:
    from Appointment import AppointmentsApp
except ImportError as e:
    logging.error(f"Ошибка импорта AppointmentsApp: {str(e)}")
    QMessageBox.critical(None, "Ошибка импорта", f"Не удалось импортировать AppointmentsApp: {str(e)}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='medical_card_app.log')

class MedicalCardApp(QMainWindow):
    def __init__(self, user_id=None, role=None):
        super().__init__()
        self.user_id = user_id
        self.role = role
        self.appointments_windows = []
        self.setWindowTitle("Медицинская информационная система - Карты пациентов")
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
            QLineEdit, QComboBox, QDateEdit {{
                border: 1px solid #d1d8e0;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                max-width: 300px;
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
        self.patient_id = None
        self.connect_to_db()
        self.setup_ui()
        self.load_patients()
        self.load_data()

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

    def load_patients(self):
        logging.debug("Загрузка списка пациентов")
        try:
            if self.role == "Пользователь" and self.user_id is not None:
                self.cursor.execute("""
                    SELECT p.patientid, 
                           p.lastname || ' ' || p.firstname || ' ' || COALESCE(p.midname, '') as patient_name
                    FROM patient p
                    WHERE p.userid = %s
                """, (self.user_id,))
                self.patients = self.cursor.fetchall()
                if self.patients:
                    self.patient_id = self.patients[0][0]
                else:
                    logging.warning(f"Пациент не найден для user_id: {self.user_id}")
                    QMessageBox.warning(self, "Предупреждение", "Пациент не найден для текущего пользователя!")
            else:
                self.cursor.execute("""
                    SELECT p.patientid, 
                           p.lastname || ' ' || p.firstname || ' ' || COALESCE(p.midname, '') as patient_name
                    FROM patient p
                    ORDER BY p.lastname, p.firstname
                """)
                self.patients = self.cursor.fetchall()
            logging.debug(f"Загружено {len(self.patients)} пациентов")
        except Exception as e:
            logging.error(f"Ошибка при загрузке пациентов: {str(e)}")
            self.patients = []

    def setup_ui(self):
        logging.debug("Настройка пользовательского интерфейса")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_label = QLabel("Медицинские карты пациентов" if self.role != "Пользователь" else "Мои медицинские карты")
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

        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Редактировать")
        self.delete_btn = QPushButton("Удалить")
        self.refresh_btn = QPushButton("Обновить")
        self.view_btn = QPushButton("Просмотр")

        for btn in [self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn, self.view_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.add_btn.clicked.connect(self.show_add_dialog)
        self.edit_btn.clicked.connect(self.show_edit_dialog)
        self.delete_btn.clicked.connect(self.delete_medical_card)
        self.refresh_btn.clicked.connect(self.load_data)
        self.view_btn.clicked.connect(self.show_appointments)

        # Добавляем кнопки в зависимости от роли
        btn_layout.addWidget(self.add_btn)
        if self.role != "Пользователь":
            btn_layout.addWidget(self.edit_btn)
            btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.view_btn)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Тип карты", "Дата создания", "Срок действия", "Пациент", "ID карты"
        ])
        self.table.setColumnHidden(4, True)

        self.table.setShowGrid(True)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #c0c0c0;
                border: 1px solid #c0c0c0;
            }
            QHeaderView::section {
                border: 1px solid #c0c0c0;
                padding: 5px;
            }
            QTableWidget::item {
                border-right: 1px solid #c0c0c0;
                border-bottom: 1px solid #c0c0c0;
                padding: 5px;
            }
        """)

        header = self.table.horizontalHeader()
        header.setDefaultSectionSize(200)
        header.setMinimumSectionSize(150)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

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

    def load_data(self):
        logging.debug(f"Загрузка данных медицинских карт для user_id: {self.user_id}, роль: {self.role}")
        if not hasattr(self, 'cursor') or not self.cursor:
            logging.error("Курсор не инициализирован")
            return

        if self.role == "Пользователь" and self.user_id is None:
            logging.error("user_id не указан для роли Пользователь")
            QMessageBox.warning(self, "Ошибка", "Не указан пользователь!")
            return

        try:
            if self.role == "Пользователь" and self.patient_id is not None:
                query = """
                    SELECT 
                        mc.type,
                        mc.establishmentdate,
                        mc.shelflife,
                        p.lastname || ' ' || p.firstname || ' ' || COALESCE(p.midname, '') as patient_name,
                        mc.medicalcardid
                    FROM medicalcard mc
                    LEFT JOIN patient p ON mc.patientid = p.patientid
                    WHERE mc.patientid = %s
                    ORDER BY mc.establishmentdate DESC
                """
                self.cursor.execute(query, (self.patient_id,))
            else:
                query = """
                    SELECT 
                        mc.type,
                        mc.establishmentdate,
                        mc.shelflife,
                        p.lastname || ' ' || p.firstname || ' ' || COALESCE(p.midname, '') as patient_name,
                        mc.medicalcardid
                    FROM medicalcard mc
                    LEFT JOIN patient p ON mc.patientid = p.patientid
                    ORDER BY mc.establishmentdate DESC
                """
                self.cursor.execute(query)

            data = self.cursor.fetchall()
            logging.debug(f"Получено {len(data)} записей из базы данных")

            self.table.setRowCount(len(data))
            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    if (col_idx == 1 or col_idx == 2) and value is not None:
                        formatted_value = value.strftime("%d.%m.%Y")
                    else:
                        formatted_value = str(value) if value is not None else ""
                    item = QTableWidgetItem(formatted_value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if row_idx % 2 == 0:
                        item.setForeground(QColor(53, 59, 72))
                    else:
                        item.setForeground(QColor(47, 53, 66))
                    self.table.setItem(row_idx, col_idx, item)
            logging.debug(f"Таблица заполнена {len(data)} записями")
        except Exception as e:
            logging.error(f"Ошибка при загрузке данных: {str(e)}")
            QMessageBox.critical(self, "Ошибка загрузки", f"Не удалось загрузить данные из базы:\n{str(e)}")

    def show_appointments(self):
        logging.debug("Вызван метод show_appointments")
        selected_items = self.table.selectedItems()
        if not selected_items:
            logging.warning("Не выбрана медицинская карта")
            QMessageBox.warning(self, "Ошибка", "Выберите медицинскую карту для просмотра приемов")
            return

        row = selected_items[0].row()
        medical_card_id_item = self.table.item(row, 4)
        if not medical_card_id_item:
            logging.error("Не удалось получить medicalcardid из таблицы")
            QMessageBox.critical(self, "Ошибка", "Не удалось получить ID медицинской карты")
            return

        medical_card_id = medical_card_id_item.text()
        logging.debug(f"Получен medicalcardid: {medical_card_id}")

        try:
            medical_card_id = int(medical_card_id)
            logging.debug(f"Преобразование medicalcardid в int успешно: {medical_card_id}")
            appointments_window = AppointmentsApp(medical_card_id=medical_card_id, role=self.role, user_id=self.user_id)
            logging.debug("Окно AppointmentsApp создано")
            self.appointments_windows.append(appointments_window)
            appointments_window.show()
            logging.debug("Окно AppointmentsApp отображено")
        except ValueError as e:
            logging.error(f"Некорректный medicalcardid: {medical_card_id}, ошибка: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Некорректный ID медицинской карты: {medical_card_id}")
        except Exception as e:
            logging.error(f"Ошибка при открытии формы Приемы: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть форму Приемы:\n{str(e)}")

    def show_add_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить медицинскую карту")
        dialog.setFixedSize(400, 250 if self.role != "Пользователь" else 200)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        type_combo = QComboBox()
        type_combo.addItems(["Амбулаторная", "Стационарная"])

        # Отображаем даты как метки, а не редактируемые поля
        establishment_date_label = QLabel(QDate.currentDate().toString("dd.MM.yyyy"))
        shelf_life_date_label = QLabel(QDate.currentDate().addYears(5).toString("dd.MM.yyyy"))

        patient_combo = None
        if self.role != "Пользователь":
            patient_combo = QComboBox()
            patient_combo.addItem("Не выбрано", None)
            for patient_id, patient_name in self.patients:
                patient_combo.addItem(patient_name, patient_id)

        btn_box = QHBoxLayout()
        ok_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")
        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Тип карты:", type_combo)
        layout.addRow("Дата создания:", establishment_date_label)
        layout.addRow("Срок действия:", shelf_life_date_label)
        if self.role != "Пользователь":
            layout.addRow("Пациент:", patient_combo)
        layout.addRow(btn_box)

        def add_medical_card():
            try:
                if self.role == "Пользователь":
                    if not self.patient_id:
                        QMessageBox.critical(dialog, "Ошибка", "Не удалось определить пациента для текущего пользователя!")
                        return
                    selected_patient_id = self.patient_id
                else:
                    selected_patient_id = patient_combo.currentData()
                    if selected_patient_id is None:
                        QMessageBox.critical(dialog, "Ошибка", "Пожалуйста, выберите пациента!")
                        return

                # Проверка, есть ли у пациента уже медицинская карта (любого типа)
                self.cursor.execute(
                    """SELECT medicalcardid FROM medicalcard 
                    WHERE patientid = %s""",
                    (selected_patient_id,)
                )
                existing_card = self.cursor.fetchone()
                if existing_card:
                    QMessageBox.critical(dialog, "Ошибка", "У пациента уже есть медицинская карта! Один пациент может иметь только одну карту.")
                    return

                # Используем текущую дату и дату +5 лет напрямую
                establishment_date = QDate.currentDate().toString("yyyy-MM-dd")
                shelf_life_date = QDate.currentDate().addYears(5).toString("yyyy-MM-dd")

                self.cursor.execute(
                    """INSERT INTO medicalcard 
                    (type, establishmentdate, shelflife, patientid) 
                    VALUES (%s, %s, %s, %s)""",
                    (
                        type_combo.currentText(),
                        establishment_date,
                        shelf_life_date,
                        selected_patient_id
                    )
                )
                self.conn.commit()
                self.load_data()
                dialog.close()
            except Exception as e:
                self.conn.rollback()
                logging.error(f"Ошибка при добавлении медицинской карты: {str(e)}")
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить медицинскую карту:\n{str(e)}")

        ok_btn.clicked.connect(add_medical_card)
        cancel_btn.clicked.connect(dialog.close)
        dialog.exec()

    def show_edit_dialog(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите медицинскую карту для редактирования")
            return

        row = selected_items[0].row()
        card_type = self.table.item(row, 0).text()
        establishment_date_str = self.table.item(row, 1).text()
        shelf_life_str = self.table.item(row, 2).text() if self.table.item(row, 2).text() else None
        current_patient = self.table.item(row, 3).text()
        medical_card_id = int(self.table.item(row, 4).text())

        try:
            establishment_date = QDate.fromString(establishment_date_str, "dd.MM.yyyy")
            if not establishment_date.isValid():
                raise ValueError("Некорректный формат даты создания")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Некорректный формат даты создания: {establishment_date_str}")
            return

        try:
            if shelf_life_str:
                shelf_life_date = QDate.fromString(shelf_life_str, "dd.MM.yyyy")
                if not shelf_life_date.isValid():
                    raise ValueError("Некорректный формат срока действия")
            else:
                shelf_life_date = QDate.currentDate().addYears(5)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Некорректный формат срока действия: {shelf_life_str}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать медицинскую карту")
        dialog.setFixedSize(400, 250 if self.role != "Пользователь" else 200)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        type_combo = QComboBox()
        type_combo.addItems(["Амбулаторная", "Стационарная"])
        type_combo.setCurrentText(card_type)

        # Отображаем даты как метки, а не редактируемые поля
        establishment_date_label = QLabel(establishment_date.toString("dd.MM.yyyy"))
        shelf_life_date_label = QLabel(shelf_life_date.toString("dd.MM.yyyy"))

        patient_combo = None
        if self.role != "Пользователь":
            patient_combo = QComboBox()
            patient_combo.addItem("Не выбрано", None)
            current_patient_index = 0
            for idx, (patient_id, patient_name) in enumerate(self.patients):
                patient_combo.addItem(patient_name, patient_id)
                if patient_name == current_patient:
                    current_patient_index = idx + 1
            patient_combo.setCurrentIndex(current_patient_index)

        btn_box = QHBoxLayout()
        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Тип карты:", type_combo)
        layout.addRow("Дата создания:", establishment_date_label)
        layout.addRow("Срок действия:", shelf_life_date_label)
        if self.role != "Пользователь":
            layout.addRow("Пациент:", patient_combo)
        layout.addRow(btn_box)

        def update_medical_card():
            try:
                if self.role == "Пользователь":
                    if not self.patient_id:
                        QMessageBox.critical(dialog, "Ошибка", "Не удалось определить пациента для текущего пользователя!")
                        return
                    selected_patient_id = self.patient_id
                else:
                    selected_patient_id = patient_combo.currentData()
                    if selected_patient_id is None:
                        QMessageBox.critical(dialog, "Ошибка", "Пожалуйста, выберите пациента!")
                        return

                    # Проверка, есть ли у выбранного пациента уже медицинская карта (кроме текущей)
                    self.cursor.execute(
                        """SELECT medicalcardid FROM medicalcard 
                        WHERE patientid = %s AND medicalcardid != %s""",
                        (selected_patient_id, medical_card_id)
                    )
                    existing_card = self.cursor.fetchone()
                    if existing_card:
                        QMessageBox.critical(dialog, "Ошибка", "У выбранного пациента уже есть медицинская карта! Один пациент может иметь только одну карту.")
                        return

                self.cursor.execute(
                    """UPDATE medicalcard SET 
                    type = %s, 
                    patientid = %s
                    WHERE medicalcardid = %s""",
                    (
                        type_combo.currentText(),
                        selected_patient_id,
                        medical_card_id
                    )
                )
                self.conn.commit()
                self.load_data()
                dialog.close()
            except Exception as e:
                self.conn.rollback()
                logging.error(f"Ошибка при обновлении медицинской карты: {str(e)}")
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить медицинскую карту:\n{str(e)}")

        ok_btn.clicked.connect(update_medical_card)
        cancel_btn.clicked.connect(dialog.close)
        dialog.exec()

    def delete_medical_card(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите медицинскую карту для удаления")
            return

        row = selected_items[0].row()
        card_type = self.table.item(row, 0).text()
        patient_name = self.table.item(row, 3).text()
        medical_card_id = int(self.table.item(row, 4).text())

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить медицинскую карту?\nТип: {card_type}\nПациент: {patient_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute("DELETE FROM medicalcard WHERE medicalcardid = %s", (medical_card_id,))
                self.conn.commit()
                self.load_data()
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить медицинскую карту:\n{str(e)}")

    def closeEvent(self, event):
        logging.debug("Закрытие окна MedicalCardApp")
        for window in self.appointments_windows:
            try:
                window.close()
            except Exception as e:
                logging.error(f"Ошибка при закрытии окна AppointmentsApp: {str(e)}")
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MedicalCardApp(user_id=None, role="Администратор")
    window.show()
    sys.exit(app.exec())