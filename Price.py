import sys
import psycopg2
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit,
    QHeaderView, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette, QIcon

class PriceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Медицинская информационная система - Цены")
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
            QLineEdit {{
                border: 1px solid #d1d8e0;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
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
        title_label = QLabel("Управление ценами")
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

        for btn in [self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.add_btn.clicked.connect(self.show_add_dialog)
        self.edit_btn.clicked.connect(self.show_edit_dialog)
        self.delete_btn.clicked.connect(self.delete_price)
        self.refresh_btn.clicked.connect(self.load_data)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.refresh_btn)

        # Таблица с данными
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "Цена"])
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
        header.setDefaultSectionSize(200)
        header.setMinimumSectionSize(150)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Настройка вертикальных заголовков
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)

        # Альтернативные цвета строк
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self.table.styleSheet() + """
            QTableWidget {
                alternate-background-color: #f5f5f5;
            }
        """)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

    def load_data(self):
        """Загрузка данных из таблицы price"""
        if not hasattr(self, 'cursor') or not self.cursor:
            print("Курсор не инициализирован")
            return

        try:
            self.cursor.execute("SELECT priceid, price FROM price ORDER BY priceid")
            data = self.cursor.fetchall()

            self.table.setRowCount(len(data))
            for row_idx, row in enumerate(data):
                # Заполняем оба столбца (ID и цена), даже если ID скрыт
                price_id = str(row[0])
                price_value = f"{row[1]:.2f}"  # Форматируем цену с двумя знаками после запятой

                # ID
                id_item = QTableWidgetItem(price_id)
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if row_idx % 2 == 0:
                    id_item.setForeground(QColor(53, 59, 72))
                else:
                    id_item.setForeground(QColor(47, 53, 66))
                self.table.setItem(row_idx, 0, id_item)

                # Цена
                price_item = QTableWidgetItem(price_value)
                price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if row_idx % 2 == 0:
                    price_item.setForeground(QColor(53, 59, 72))
                else:
                    price_item.setForeground(QColor(47, 53, 66))
                self.table.setItem(row_idx, 1, price_item)

            print(f"Загружено {len(data)} записей")

        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            QMessageBox.critical(
                self,
                "Ошибка загрузки",
                f"Не удалось загрузить данные из базы:\n{str(e)}"
            )

    def show_add_dialog(self):
        """Диалог добавления новой цены"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить цену")
        dialog.setFixedSize(400, 200)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        price_input = QLineEdit()
        price_input.setPlaceholderText("Введите цену (например, 500.00)")
        price_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d8e0;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4b7bec;
            }
        """)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Добавить")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: {self.med_light.name()};
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #20bf6b;
            }
        """)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: {self.med_light.name()};
                color: white;
            }
            QPushButton:hover {
                background-color: #eb3b5a;
            }
        """)

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Цена:", price_input)
        layout.addRow(btn_box)

        def add_price():
            price_text = price_input.text().strip()
            try:
                price = float(price_text)
                if price < 0:
                    QMessageBox.warning(dialog, "Ошибка", "Цена не может быть отрицательной")
                    return
            except ValueError:
                QMessageBox.warning(dialog, "Ошибка", "Введите корректное число для цены (например, 500.00)")
                return

            try:
                self.cursor.execute(
                    "INSERT INTO price (price) VALUES (%s) RETURNING priceid",
                    (price,))
                new_id = self.cursor.fetchone()[0]
                self.conn.commit()

                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)

                id_item = QTableWidgetItem(str(new_id))
                id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_pos, 0, id_item)

                price_item = QTableWidgetItem(f"{price:.2f}")
                price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_pos, 1, price_item)

                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить цену:\n{str(e)}")

        ok_btn.clicked.connect(add_price)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def show_edit_dialog(self):
        """Диалог редактирования цены"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите цену для редактирования")
            return

        row = selected_items[0].row()
        price_id = int(self.table.item(row, 0).text())
        current_price = float(self.table.item(row, 1).text())

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактировать цену")
        dialog.setFixedSize(400, 200)

        layout = QFormLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        price_input = QLineEdit(str(current_price))
        price_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #d1d8e0;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4b7bec;
            }
        """)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        ok_btn = QPushButton("Сохранить")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: {self.med_light.name()};
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3867d6;
            }
        """)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: {self.med_light.name()};
                color: white;
            }
            QPushButton:hover {
                background-color: #eb3b5a;
            }
        """)

        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)

        layout.addRow("Цена:", price_input)
        layout.addRow(btn_box)

        def update_price():
            price_text = price_input.text().strip()
            try:
                new_price = float(price_text)
                if new_price < 0:
                    QMessageBox.warning(dialog, "Ошибка", "Цена не может быть отрицательной")
                    return
            except ValueError:
                QMessageBox.warning(dialog, "Ошибка", "Введите корректное число для цены (например, 500.00)")
                return

            if new_price == current_price:
                dialog.close()
                return

            try:
                self.cursor.execute(
                    "UPDATE price SET price = %s WHERE priceid = %s",
                    (new_price, price_id))
                self.conn.commit()

                self.table.item(row, 1).setText(f"{new_price:.2f}")
                dialog.close()

            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(dialog, "Ошибка", f"Не удалось обновить цену:\n{str(e)}")

        ok_btn.clicked.connect(update_price)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()

    def delete_price(self):
        """Удаление выбранной цены"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите цену для удаления")
            return

        row = selected_items[0].row()
        price_id = int(self.table.item(row, 0).text())
        price_value = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Вы уверены, что хотите удалить цену '{price_value}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cursor.execute(
                    "DELETE FROM price WHERE priceid = %s",
                    (price_id,))
                self.conn.commit()
                self.table.removeRow(row)
            except Exception as e:
                self.conn.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить цену:\n{str(e)}")

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
    window = PriceApp()
    window.show()
    sys.exit(app.exec())