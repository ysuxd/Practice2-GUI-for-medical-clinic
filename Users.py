import sys
import psycopg2
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit,
    QHeaderView, QDialog, QFormLayout, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette,QIcon

class UsersApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Медицинская информационная система - Пользователи")
        self.setGeometry(100, 100, 900, 650)

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
            QLineEdit, QCheckBox, QComboBox {{
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

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title_label = QLabel("Управление пользователями")
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
        self.delete_btn.clicked.connect(self.delete_user)
        self.refresh_btn.clicked.connect(self.load_data)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)

        # Таблица с данными
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Добавляем столбец для роли
        self.table.setHorizontalHeaderLabels(["ID", "Логин", "Пароль", "Заблокирован", "Роль"])
        self.table.setColumnHidden(0, True)  # Скрываем столбец ID

        # Настройка границ и внешнего вида таблицы
        self.table.setStyleSheet("""
                    QTableWidget {
                        border: 1px solid #c0c0c0;
                        gridline-color: #c0c0c0;
                    }
                    QHeaderView::section {
                        background-color: #006DB0;
                        color: white;
                        padding: 8px;
                        border: 1px solid #c0c0c0;
                        font-weight: bold;
                    }
                    QTableWidget::item {
                        border-right: 1px solid #c0c0c0;
                        border-bottom: 1px solid #c0c0c0;
                        padding: 8px;
                    }
                """)

        # Настройка размеров столбцов
        header = self.table.horizontalHeader()
        header.setDefaultSectionSize(200)  # Стандартная ширина столбца
        header.setMinimumSectionSize(150)  # Минимальная ширина

        # Режим растяжения для столбцов
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Логин
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Пароль
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Заблокирован
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Роль

        # Настройка вертикальных заголовков
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)  # Включаем отображение сетки

        # Альтернативные цвета строк
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
                    QTableWidget {
                        alternate-background-color: #f5f5f5;
                    }
                """)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

    def load_data(self):
        """Загрузка данных из таблицы users"""
        if not hasattr(self, 'cursor') or not self.cursor:
            print("Курсор не инициализирован")
            return

        try:
            self.cursor.execute("SELECT userid, login, password, isblocked, role FROM users ORDER BY userid")
            data = self.cursor.fetchall()

            self.table.setRowCount(len(data))
            for row_idx, row in enumerate(data):
                for col_idx, value in enumerate(row):
                    if col_idx == 3:  # isblocked (boolean)
                        value = "Да" if value else "Нет"
                    elif col_idx == 4:  # role
                        value = value if value else "Не указана"  # Отображаем "Не указана" для NULL
                    item = QTableWidgetItem(str(value))
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
            self.conn.rollback()
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить данные из базы:\n{str(e)}"
            )

    def show_add_dialog(self):
        """Диалог добавления нового пользователя"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить пользователя")
        dialog.setFixedSize(400, 300)  # Увеличиваем размер для нового поля

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        login_input = QLineEdit()
        login_input.setPlaceholderText("Введите логин")
        login_input.setMaxLength(50)  # Ограничение по длине как в БД

        password_input = QLineEdit()
        password_input.setPlaceholderText("Введите пароль")
        password_input.setMaxLength(50)  # Ограничение по длине как в БД
        password_input.setEchoMode(QLineEdit.EchoMode.Password)  # Скрываем ввод пароля

        isblocked_checkbox = QCheckBox("Заблокирован")

        role_combobox = QComboBox()
        role_combobox.addItems(["Администратор", "Сотрудник", "Пользователь"])

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Логин:", login_input)
        layout.addRow("Пароль:", password_input)
        layout.addRow("Статус:", isblocked_checkbox)
        layout.addRow("Роль:", role_combobox)
        layout.addRow(btn_box)

        def add_user():
            login = login_input.text().strip()
            password = password_input.text().strip()
            isblocked = isblocked_checkbox.isChecked()
            role = role_combobox.currentText()

            if not login or not password:
                QMessageBox.warning(dialog, "Ошибка", "Введите логин и пароль")
                return

            try:
                self.cursor.execute(
                    "INSERT INTO users (login, password, isblocked, role) VALUES (%s, %s, %s, %s) RETURNING userid",
                    (login, password, isblocked, role))
                new_id = self.cursor.fetchone()[0]
                self.conn.commit()

                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)

                id_item = QTableWidgetItem(str(new_id))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_pos, 0, id_item)

                login_item = QTableWidgetItem(login)
                login_item.setFlags(login_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_pos, 1, login_item)

                password_item = QTableWidgetItem(password)
                password_item.setFlags(password_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_pos, 2, password_item)

                isblocked_item = QTableWidgetItem("Да" if isblocked else "Нет")
                isblocked_item.setFlags(isblocked_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_pos, 3, isblocked_item)

                role_item = QTableWidgetItem(role)
                role_item.setFlags(role_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_pos, 4, role_item)

                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить пользователя:\n{str(e)}")

        ok_btn.clicked.connect(add_user)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def show_edit_dialog(self):
        """Диалог редактирования пользователя"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для редактирования")
            return

        row = selected_items[0].row()
        user_id = int(self.table.item(row, 0).text())
        current_login = self.table.item(row, 1).text()
        current_password = self.table.item(row, 2).text()
        current_isblocked = self.table.item(row, 3).text() == "Да"
        current_role = self.table.item(row, 4).text()
        if current_role == "Не указана":
            current_role = "Пользователь"  # Значение по умолчанию для NULL

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать пользователя")
        dialog.setFixedSize(400, 300)  # Увеличиваем размер для нового поля

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        login_input = QLineEdit(current_login)
        login_input.setMaxLength(50)  # Ограничение по длине как в БД

        password_input = QLineEdit(current_password)
        password_input.setMaxLength(50)  # Ограничение по длине как в БД
        password_input.setEchoMode(QLineEdit.EchoMode.Password)  # Скрываем ввод пароля

        isblocked_checkbox = QCheckBox("Заблокирован")
        isblocked_checkbox.setChecked(current_isblocked)

        role_combobox = QComboBox()
        role_combobox.addItems(["Администратор", "Сотрудник", "Пользователь"])
        role_combobox.setCurrentText(current_role)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Логин:", login_input)
        layout.addRow("Пароль:", password_input)
        layout.addRow("Статус:", isblocked_checkbox)
        layout.addRow("Роль:", role_combobox)
        layout.addRow(btn_box)

        def update_user():
            new_login = login_input.text().strip()
            new_password = password_input.text().strip()
            new_isblocked = isblocked_checkbox.isChecked()
            new_role = role_combobox.currentText()

            if not new_login or not new_password:
                QMessageBox.warning(dialog, "Ошибка", "Введите логин и пароль")
                return

            try:
                self.cursor.execute(
                    "UPDATE users SET login = %s, password = %s, isblocked = %s, role = %s WHERE userid = %s",
                    (new_login, new_password, new_isblocked, new_role, user_id))
                self.conn.commit()

                # Обновляем таблицу
                self.table.item(row, 1).setText(new_login)
                self.table.item(row, 2).setText(new_password)
                self.table.item(row, 3).setText("Да" if new_isblocked else "Нет")
                self.table.item(row, 4).setText(new_role)
                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить пользователя:\n{str(e)}")

        ok_btn.clicked.connect(update_user)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def delete_user(self):
        """Удаление выбранного пользователя"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите пользователя для удаления")
            return

        row = selected_items[0].row()
        user_id = int(self.table.item(row, 0).text())
        user_login = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить пользователя '{user_login}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute(
                    "DELETE FROM users WHERE userid = %s",
                    (user_id,))
                self.conn.commit()
                self.table.removeRow(row)
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить пользователя:\n{str(e)}")

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
    window = UsersApp()
    window.show()
    sys.exit(app.exec())