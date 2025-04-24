import sys
import psycopg2
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit,
    QHeaderView, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette, QIcon  # Added QIcon for the window icon

class DiagnosisApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Медицинская информационная система - Диагнозы")
        self.setGeometry(100, 100, 900, 650)

        # Set the window icon (replace "path/to/icon.png" with your actual icon path)
        self.setWindowIcon(QIcon('icon.jpg'))

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
            QLineEdit {{
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
        title_label = QLabel("Управление диагнозами")
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
        self.delete_btn.clicked.connect(self.delete_diagnosis)
        self.refresh_btn.clicked.connect(self.load_data)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)

        # Таблица с данными
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "Название диагноза"])
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

        # Режим растяжения для столбца с названием
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

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
        """Загрузка данных из таблицы diagnosis"""
        if not hasattr(self, 'cursor') or not self.cursor:
            print("Курсор не инициализирован")
            return

        try:
            self.cursor.execute("SELECT diagnosisid, diagnosisname FROM diagnosis ORDER BY diagnosisid")
            data = self.cursor.fetchall()

            self.table.setRowCount(len(data))
            for row_idx, row in enumerate(data):
                # Заполняем оба столбца (ID и название), даже если ID не виден
                for col_idx, value in enumerate(row):
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
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить данные из базы:\n{str(e)}"
            )

    def show_add_dialog(self):
        """Диалог добавления нового диагноза"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить диагноз")
        dialog.setFixedSize(400, 200)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Введите название диагноза")
        name_input.setMaxLength(100)  # Ограничение по длине как в БД

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Название диагноза:", name_input)
        layout.addRow(btn_box)

        def add_diagnosis():
            name = name_input.text().strip()
            if not name:
                QMessageBox.warning(dialog, "Ошибка", "Введите название диагноза")
                return

            try:
                self.cursor.execute(
                    "INSERT INTO diagnosis (diagnosisname) VALUES (%s) RETURNING diagnosisid",
                    (name,))
                new_id = self.cursor.fetchone()[0]
                self.conn.commit()

                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)

                id_item = QTableWidgetItem(str(new_id))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_pos, 0, id_item)

                name_item = QTableWidgetItem(name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_pos, 1, name_item)

                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить диагноз:\n{str(e)}")

        ok_btn.clicked.connect(add_diagnosis)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def show_edit_dialog(self):
        """Диалог редактирования диагноза"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите диагноз для редактирования")
            return

        row = selected_items[0].row()
        diagnosis_id = int(self.table.item(row, 0).text())
        current_name = self.table.item(row, 1).text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать диагноз")
        dialog.setFixedSize(400, 200)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        name_input = QLineEdit(current_name)
        name_input.setMaxLength(100)  # Ограничение по длине как в БД

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Название диагноза:", name_input)
        layout.addRow(btn_box)

        def update_diagnosis():
            new_name = name_input.text().strip()
            if not new_name:
                QMessageBox.warning(dialog, "Ошибка", "Введите название диагноза")
                return

            if new_name == current_name:
                dialog.close()
                return

            try:
                self.cursor.execute(
                    "UPDATE diagnosis SET diagnosisname = %s WHERE diagnosisid = %s",
                    (new_name, diagnosis_id))
                self.conn.commit()

                # Обновляем таблицу
                self.table.item(row, 1).setText(new_name)
                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить диагноз:\n{str(e)}")

        ok_btn.clicked.connect(update_diagnosis)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def delete_diagnosis(self):
        """Удаление выбранного диагноза"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите диагноз для удаления")
            return

        row = selected_items[0].row()
        diagnosis_id = int(self.table.item(row, 0).text())
        diagnosis_name = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить диагноз '{diagnosis_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute(
                    "DELETE FROM diagnosis WHERE diagnosisid = %s",
                    (diagnosis_id,))
                self.conn.commit()
                self.table.removeRow(row)
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить диагноз:\n{str(e)}")

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
    window = DiagnosisApp()
    window.show()
    sys.exit(app.exec())