import sys
import psycopg2
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit,
    QHeaderView, QDialog, QFormLayout, QDateEdit, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QPalette, QIcon

class PatientsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Медицинская информационная система - Пациенты")
        self.setGeometry(100, 100, 1200, 800)
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
            QLineEdit, QDateEdit, QComboBox {{
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

        # Настройка цветовой палитры
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, self.med_light)
        palette.setColor(QPalette.ColorRole.Base, self.med_white)
        palette.setColor(QPalette.ColorRole.Highlight, self.med_blue)
        self.setPalette(palette)

        self.conn = None
        self.cursor = None
        self.connect_to_db()
        self.setup_ui()
        self.load_medical_cards()
        self.load_data()

    def connect_to_db(self):
        try:
            self.conn = psycopg2.connect(
                dbname='Practice',
                user='postgres',
                password='123',
                host='localhost'
            )
            self.cursor = self.conn.cursor()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения к БД: {str(e)}")
            sys.exit(1)

    def load_medical_cards(self):
        try:
            self.cursor.execute("""
                SELECT medicalcardid 
                FROM medicalcard 
                WHERE patientid IS NULL
                ORDER BY medicalcardid
            """)
            self.medical_cards = self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при загрузке медицинских карт: {e}")
            self.medical_cards = []

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_label = QLabel("Управление пациентами")
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

        for btn in [self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.add_btn.clicked.connect(self.show_add_dialog)
        self.edit_btn.clicked.connect(self.show_edit_dialog)
        self.delete_btn.clicked.connect(self.delete_patient)
        self.refresh_btn.clicked.connect(self.refresh_all)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Номер мед. карты", "Фамилия", "Имя", "Отчество", "Дата рождения", "Телефон", "ID пользователя"
        ])
        self.table.setColumnHidden(0, True)
        self.table.setColumnHidden(7, True)

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
        for i in range(self.table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f5f5f5;
            }
        """)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

    def refresh_all(self):
        self.load_medical_cards()
        self.load_data()

    def load_data(self):
        if not hasattr(self, 'cursor') or not self.cursor:
            print("Курсор не инициализирован")
            return

        try:
            query = """
                SELECT p.patientid, p.medicalcardid, p.lastname, p.firstname, p.midname, 
                       p.birthdate, p.phonenumber, p.userid
                FROM patient p
                ORDER BY p.lastname, p.firstname, p.midname
            """
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            self.table.setRowCount(len(data))
            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    if col_idx == 5 and value is not None:
                        value = value.strftime("%d.%m.%Y")
                    elif col_idx == 6 and value is not None:
                        value = f"+7{value}"
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if row_idx % 2 == 0:
                        item.setForeground(QColor(53, 59, 72))
                    else:
                        item.setForeground(QColor(47, 53, 66))
                    self.table.setItem(row_idx, col_idx, item)
            print(f"Загружено {len(data)} записей")
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            QMessageBox.critical(self, "Ошибка загрузки", f"Не удалось загрузить данные из базы:\n{str(e)}")

    def show_add_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить пациента")
        dialog.setFixedSize(500, 550)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lastname_input = QLineEdit()
        lastname_input.setPlaceholderText("Введите фамилию")
        lastname_input.setMaxLength(50)

        firstname_input = QLineEdit()
        firstname_input.setPlaceholderText("Введите имя")
        firstname_input.setMaxLength(50)

        midname_input = QLineEdit()
        midname_input.setPlaceholderText("Введите отчество")
        midname_input.setMaxLength(50)

        birthdate_input = QDateEdit()
        birthdate_input.setDisplayFormat("dd.MM.yyyy")
        birthdate_input.setDate(QDate.currentDate())
        birthdate_input.setCalendarPopup(True)

        phone_input = QLineEdit()
        phone_input.setPlaceholderText("Введите номер телефона")
        phone_input.setInputMask("+7(999)999-99-99;_")

        login_input = QLineEdit()
        login_input.setPlaceholderText("Введите логин для пациента")
        login_input.setMaxLength(50)

        password_input = QLineEdit()
        password_input.setPlaceholderText("Введите пароль")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setMaxLength(50)

        medical_card_combo = QComboBox()
        medical_card_combo.addItem("Не выбрано", None)
        for card_id, in self.medical_cards:
            medical_card_combo.addItem(str(card_id), card_id)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        ok_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")
        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Номер мед. карты:", medical_card_combo)
        layout.addRow("Фамилия:", lastname_input)
        layout.addRow("Имя:", firstname_input)
        layout.addRow("Отчество:", midname_input)
        layout.addRow("Дата рождения:", birthdate_input)
        layout.addRow("Телефон:", phone_input)
        layout.addRow("Логин пользователя:", login_input)
        layout.addRow("Пароль пользователя:", password_input)
        layout.addRow(btn_box)

        def add_patient():
            lastname = lastname_input.text().strip()
            firstname = firstname_input.text().strip()
            midname = midname_input.text().strip()
            birthdate = birthdate_input.date().toString("yyyy-MM-dd")
            phone = phone_input.text().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            medical_card_id = medical_card_combo.currentData()
            login = login_input.text().strip()
            password = password_input.text().strip()

            if not all([lastname, firstname, phone]):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все обязательные поля (кроме отчества)")
                return

            try:
                if medical_card_id:
                    self.cursor.execute("SELECT patientid FROM patient WHERE medicalcardid = %s", (medical_card_id,))
                    if self.cursor.fetchone():
                        QMessageBox.warning(dialog, "Ошибка", "Эта медицинская карта уже занята другим пациентом")
                        return

                if login:
                    self.cursor.execute("SELECT login FROM users WHERE login = %s", (login,))
                    if self.cursor.fetchone():
                        QMessageBox.warning(dialog, "Ошибка", "Пользователь с таким логином уже существует")
                        return

                phone_num = int(phone[2:]) if phone.startswith("+7") else int(phone)
                user_id = None
                if login and password:
                    self.cursor.execute(
                        """INSERT INTO users (login, password, isblocked, role) 
                        VALUES (%s, %s, %s, %s) RETURNING userid""",
                        (login, password, False, "Пользователь")
                    )
                    user_id = self.cursor.fetchone()[0]

                self.cursor.execute(
                    """INSERT INTO patient 
                    (medicalcardid, lastname, firstname, midname, birthdate, phonenumber, userid) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s) 
                    RETURNING patientid""",
                    (medical_card_id, lastname, firstname, midname or None, birthdate, phone_num, user_id))

                new_id = self.cursor.fetchone()[0]
                self.conn.commit()

                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)
                formatted_birthdate = birthdate_input.date().toString("dd.MM.yyyy")
                card_number = str(medical_card_combo.currentData()) if medical_card_id else ""
                columns = [
                    str(new_id),
                    card_number,
                    lastname,
                    firstname,
                    midname or "",
                    formatted_birthdate,
                    phone_input.text() if phone else "",
                    str(user_id) if user_id else ""
                ]

                for col_idx, value in enumerate(columns):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row_pos, col_idx, item)

                dialog.close()
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить пациента:\n{str(e)}")

        ok_btn.clicked.connect(add_patient)
        cancel_btn.clicked.connect(dialog.close)
        dialog.exec()

    def show_edit_dialog(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите пациента для редактирования")
            return

        row = selected_items[0].row()
        patient_id = int(self.table.item(row, 0).text())
        user_id = self.table.item(row, 7).text() if self.table.item(row, 7) else None
        current_card = self.table.item(row, 1).text()
        current_lastname = self.table.item(row, 2).text()
        current_firstname = self.table.item(row, 3).text()
        current_midname = self.table.item(row, 4).text()
        current_birthdate = QDate.fromString(self.table.item(row, 5).text(), "dd.MM.yyyy")
        current_phone = self.table.item(row, 6).text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать пациента")
        dialog.setFixedSize(500, 450)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        medical_card_combo = QComboBox()
        medical_card_combo.addItem("Не выбрано", None)
        if current_card:
            medical_card_combo.addItem(current_card, int(current_card) if current_card.isdigit() else None)
        for card_id, in self.medical_cards:
            if str(card_id) != current_card:
                medical_card_combo.addItem(str(card_id), card_id)
        current_card_index = 0 if not current_card else 1
        medical_card_combo.setCurrentIndex(current_card_index)

        lastname_input = QLineEdit(current_lastname)
        lastname_input.setMaxLength(50)
        firstname_input = QLineEdit(current_firstname)
        firstname_input.setMaxLength(50)
        midname_input = QLineEdit(current_midname)
        midname_input.setMaxLength(50)
        birthdate_input = QDateEdit(current_birthdate)
        birthdate_input.setDisplayFormat("dd.MM.yyyy")
        birthdate_input.setCalendarPopup(True)
        phone_input = QLineEdit()
        phone_input.setInputMask("+7(999)999-99-99;_")
        phone_input.setText(current_phone)

        user_id_label = QLabel(str(user_id) if user_id else "Не привязан")
        layout.addRow("ID пользователя:", user_id_label)
        layout.addRow("Номер мед. карты:", medical_card_combo)
        layout.addRow("Фамилия:", lastname_input)
        layout.addRow("Имя:", firstname_input)
        layout.addRow("Отчество:", midname_input)
        layout.addRow("Дата рождения:", birthdate_input)
        layout.addRow("Телефон:", phone_input)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)
        layout.addRow(btn_box)

        def update_patient():
            lastname = lastname_input.text().strip()
            firstname = firstname_input.text().strip()
            midname = midname_input.text().strip()
            birthdate = birthdate_input.date().toString("yyyy-MM-dd")
            phone = phone_input.text().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            medical_card_id = medical_card_combo.currentData()

            if not all([lastname, firstname, phone]):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все обязательные поля (кроме отчества)")
                return

            try:
                if medical_card_id and str(medical_card_id) != current_card:
                    self.cursor.execute("SELECT patientid FROM patient WHERE medicalcardid = %s", (medical_card_id,))
                    if self.cursor.fetchone():
                        QMessageBox.warning(dialog, "Ошибка", "Эта медицинская карта уже занята другим пациентом")
                        return

                phone_num = int(phone[2:]) if phone.startswith("+7") else int(phone)
                self.cursor.execute(
                    """UPDATE patient SET 
                    medicalcardid = %s, lastname = %s, firstname = %s, midname = %s, 
                    birthdate = %s, phonenumber = %s
                    WHERE patientid = %s""",
                    (medical_card_id, lastname, firstname, midname or None, birthdate, phone_num, patient_id))
                self.conn.commit()
                formatted_birthdate = birthdate_input.date().toString("dd.MM.yyyy")
                card_number = str(medical_card_combo.currentData()) if medical_card_id else ""
                self.table.item(row, 1).setText(card_number)
                self.table.item(row, 2).setText(lastname)
                self.table.item(row, 3).setText(firstname)
                self.table.item(row, 4).setText(midname or "")
                self.table.item(row, 5).setText(formatted_birthdate)
                self.table.item(row, 6).setText(phone_input.text() if phone else "")
                dialog.close()
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить данные пациента:\n{str(e)}")

        ok_btn.clicked.connect(update_patient)
        cancel_btn.clicked.connect(dialog.close)
        dialog.exec()

    def delete_patient(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите пациента для удаления")
            return

        row = selected_items[0].row()
        patient_id = int(self.table.item(row, 0).text())
        user_id = self.table.item(row, 7).text() if self.table.item(row, 7) else None
        patient_name = f"{self.table.item(row, 2).text()} {self.table.item(row, 3).text()}"

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить пациента '{patient_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute("DELETE FROM patient WHERE patientid = %s", (patient_id,))
                if user_id:
                    self.cursor.execute("DELETE FROM users WHERE userid = %s", (user_id,))
                self.conn.commit()
                self.table.removeRow(row)
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить пациента:\n{str(e)}")

    def closeEvent(self, event):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PatientsApp()
    window.show()
    sys.exit(app.exec())