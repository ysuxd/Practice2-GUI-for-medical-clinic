import sys
import psycopg2
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit,
    QHeaderView, QDialog, QFormLayout, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette,QIcon


class DoctorsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Медицинская информационная система - Врачи")
        self.setGeometry(100, 100, 1200, 800)

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
            QLineEdit, QComboBox {{
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
        self.load_data()
        self.load_specializations()
        self.load_job_titles()

    def connect_to_db(self):
        """Подключение к базе данных"""
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

    def load_specializations(self):
        """Загрузка списка специализаций для комбобокса"""
        try:
            self.cursor.execute(
                "SELECT specializationid, specializationname FROM specialization ORDER BY specializationname")
            self.specializations = self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при загрузке специализаций: {e}")
            self.specializations = []

    def load_job_titles(self):
        """Загрузка списка должностей для комбобокса"""
        try:
            self.cursor.execute("SELECT jobtitleid, jobtitlename FROM jobtitle ORDER BY jobtitlename")
            self.job_titles = self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при загрузке должностей: {e}")
            self.job_titles = []

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title_label = QLabel("Управление врачами")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {self.med_blue.name()};
                padding: 10px;
            }}
        """)
        layout.addWidget(title_label)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Редактировать")
        self.delete_btn = QPushButton("Удалить")
        self.refresh_btn = QPushButton("Обновить")

        # Все кнопки одного цвета (медицинский синий)
        for btn in [self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.add_btn.clicked.connect(self.show_add_dialog)
        self.edit_btn.clicked.connect(self.show_edit_dialog)
        self.delete_btn.clicked.connect(self.delete_doctor)
        self.refresh_btn.clicked.connect(self.load_data)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)

        # Таблица с данными
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Специализация", "Должность",
            "Фамилия", "Имя", "Отчество", "Телефон"
        ])
        self.table.setColumnHidden(0, True)  # Скрываем столбец ID

        # Настройка разделителей столбцов
        self.table.setShowGrid(True)  # Включаем отображение сетки
        self.table.setStyleSheet("""
                    QTableWidget {
                        gridline-color: #c0c0c0;  /* Серый цвет линий сетки */
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

        # Настройка размеров столбцов
        header = self.table.horizontalHeader()
        header.setDefaultSectionSize(150)  # Стандартная ширина столбца
        header.setMinimumSectionSize(120)  # Минимальная ширина

        # Разные режимы растяжения для столбцов
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Специализация
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Должность
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Фамилия
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Имя
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)  # Отчество
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Телефон

        # Настройка вертикальных заголовков
        self.table.verticalHeader().setVisible(False)

        # Альтернативные цвета строк
        self.table.setAlternatingRowColors(True)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
                    QTableWidget {
                        alternate-background-color: #f5f5f5;
                    }
                """)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

    def load_data(self):
        """Загрузка данных о врачах с объединением таблиц"""
        if not hasattr(self, 'cursor') or not self.cursor:
            print("Курсор не инициализирован")
            return

        try:
            query = """
                SELECT d.doctorid, s.specializationname, j.jobtitlename, 
                       d.secondname, d.firstname, d.midname, d.phonenumber
                FROM doctor d
                LEFT JOIN specialization s ON d.specializationid = s.specializationid
                LEFT JOIN jobtitle j ON d.jobtitleid = j.jobtitleid
                ORDER BY d.secondname, d.firstname, d.midname
            """
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            self.table.setRowCount(len(data))
            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    # Для номера телефона форматируем вывод
                    if col_idx == 6 and value is not None:
                        value = str(int(value))  # Убираем дробную часть

                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                    # Устанавливаем цвет текста для четных/нечетных строк
                    if row_idx % 2 == 0:
                        item.setForeground(QColor(53, 59, 72))  # Темно-синий
                    else:
                        item.setForeground(QColor(47, 53, 66))  # Еще темнее

                    self.table.setItem(row_idx, col_idx, item)

            print(f"Загружено {len(data)} записей")

        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить данные из базы:\n{str(e)}"
            )

    def show_add_dialog(self):
        """Диалог добавления нового врача"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить врача")
        dialog.setFixedSize(500, 400)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Комбобоксы для выбора специализации и должности
        spec_combo = QComboBox()
        job_combo = QComboBox()

        # Заполняем комбобоксы
        for spec_id, spec_name in self.specializations:
            spec_combo.addItem(spec_name, spec_id)

        for job_id, job_name in self.job_titles:
            job_combo.addItem(job_name, job_id)

        # Поля для ввода данных
        secondname_input = QLineEdit()
        secondname_input.setPlaceholderText("Введите фамилию")
        secondname_input.setMaxLength(50)

        firstname_input = QLineEdit()
        firstname_input.setPlaceholderText("Введите имя")
        firstname_input.setMaxLength(50)

        midname_input = QLineEdit()
        midname_input.setPlaceholderText("Введите отчество")
        midname_input.setMaxLength(50)

        phone_input = QLineEdit()
        phone_input.setPlaceholderText("Введите номер телефона")
        phone_input.setInputMask("+7(999)999-99-99;_")

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        # Добавляем элементы в форму
        layout.addRow("Специализация:", spec_combo)
        layout.addRow("Должность:", job_combo)
        layout.addRow("Фамилия:", secondname_input)
        layout.addRow("Имя:", firstname_input)
        layout.addRow("Отчество:", midname_input)
        layout.addRow("Телефон:", phone_input)
        layout.addRow(btn_box)

        def add_doctor():
            # Получаем данные из формы
            spec_id = spec_combo.currentData()
            job_id = job_combo.currentData()
            secondname = secondname_input.text().strip()
            firstname = firstname_input.text().strip()
            midname = midname_input.text().strip()
            phone = phone_input.text().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

            # Валидация данных
            if not all([spec_id, job_id, secondname, firstname, phone]):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все обязательные поля (кроме отчества)")
                return

            try:
                # Преобразуем телефон в число
                phone_num = int(phone) if phone else None

                self.cursor.execute(
                    """INSERT INTO doctor 
                    (specializationid, jobtitleid, secondname, firstname, midname, phonenumber) 
                    VALUES (%s, %s, %s, %s, %s, %s) 
                    RETURNING doctorid""",
                    (spec_id, job_id, secondname, firstname, midname or None, phone_num))

                new_id = self.cursor.fetchone()[0]
                self.conn.commit()

                # Добавляем новую строку в таблицу
                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)

                # Получаем названия для отображения
                spec_name = spec_combo.currentText()
                job_name = job_combo.currentText()

                # Заполняем таблицу
                columns = [
                    str(new_id), spec_name, job_name,
                    secondname, firstname, midname or "",
                    phone_input.text() if phone else ""
                ]

                for col_idx, value in enumerate(columns):
                    item = QTableWidgetItem(value)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row_pos, col_idx, item)

                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить врача:\n{str(e)}")

        ok_btn.clicked.connect(add_doctor)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def show_edit_dialog(self):
        """Диалог редактирования врача"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите врача для редактирования")
            return

        row = selected_items[0].row()
        doctor_id = int(self.table.item(row, 0).text())

        # Получаем текущие данные
        current_spec = self.table.item(row, 1).text()
        current_job = self.table.item(row, 2).text()
        current_secondname = self.table.item(row, 3).text()
        current_firstname = self.table.item(row, 4).text()
        current_midname = self.table.item(row, 5).text()
        current_phone = self.table.item(row, 6).text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать врача")
        dialog.setFixedSize(500, 400)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Комбобоксы для выбора специализации и должности
        spec_combo = QComboBox()
        job_combo = QComboBox()

        # Заполняем комбобоксы и устанавливаем текущие значения
        current_spec_index = 0
        current_job_index = 0

        for i, (spec_id, spec_name) in enumerate(self.specializations):
            spec_combo.addItem(spec_name, spec_id)
            if spec_name == current_spec:
                current_spec_index = i

        for i, (job_id, job_name) in enumerate(self.job_titles):
            job_combo.addItem(job_name, job_id)
            if job_name == current_job:
                current_job_index = i

        spec_combo.setCurrentIndex(current_spec_index)
        job_combo.setCurrentIndex(current_job_index)

        # Поля для ввода данных
        secondname_input = QLineEdit(current_secondname)
        secondname_input.setMaxLength(50)

        firstname_input = QLineEdit(current_firstname)
        firstname_input.setMaxLength(50)

        midname_input = QLineEdit(current_midname)
        midname_input.setMaxLength(50)

        phone_input = QLineEdit()
        phone_input.setInputMask("+7(999)999-99-99;_")
        phone_input.setText(current_phone)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        # Добавляем элементы в форму
        layout.addRow("Специализация:", spec_combo)
        layout.addRow("Должность:", job_combo)
        layout.addRow("Фамилия:", secondname_input)
        layout.addRow("Имя:", firstname_input)
        layout.addRow("Отчество:", midname_input)
        layout.addRow("Телефон:", phone_input)
        layout.addRow(btn_box)

        def update_doctor():
            # Получаем данные из формы
            spec_id = spec_combo.currentData()
            job_id = job_combo.currentData()
            secondname = secondname_input.text().strip()
            firstname = firstname_input.text().strip()
            midname = midname_input.text().strip()
            phone = phone_input.text().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

            # Валидация данных
            if not all([spec_id, job_id, secondname, firstname, phone]):
                QMessageBox.warning(dialog, "Ошибка", "Заполните все обязательные поля (кроме отчества)")
                return

            try:
                # Преобразуем телефон в число
                phone_num = int(phone) if phone else None

                self.cursor.execute(
                    """UPDATE doctor SET 
                    specializationid = %s, 
                    jobtitleid = %s, 
                    secondname = %s, 
                    firstname = %s, 
                    midname = %s, 
                    phonenumber = %s
                    WHERE doctorid = %s""",
                    (spec_id, job_id, secondname, firstname, midname or None, phone_num, doctor_id))

                self.conn.commit()

                # Обновляем таблицу
                spec_name = spec_combo.currentText()
                job_name = job_combo.currentText()

                self.table.item(row, 1).setText(spec_name)
                self.table.item(row, 2).setText(job_name)
                self.table.item(row, 3).setText(secondname)
                self.table.item(row, 4).setText(firstname)
                self.table.item(row, 5).setText(midname or "")
                self.table.item(row, 6).setText(phone_input.text() if phone else "")

                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить данные врача:\n{str(e)}")

        ok_btn.clicked.connect(update_doctor)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def delete_doctor(self):
        """Удаление выбранного врача"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите врача для удаления")
            return

        row = selected_items[0].row()
        doctor_id = int(self.table.item(row, 0).text())
        doctor_name = f"{self.table.item(row, 3).text()} {self.table.item(row, 4).text()}"

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить врача '{doctor_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute(
                    "DELETE FROM doctor WHERE doctorid = %s",
                    (doctor_id,))
                self.conn.commit()
                self.table.removeRow(row)
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить врача:\n{str(e)}")

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = DoctorsApp()
    window.show()
    sys.exit(app.exec())