import sys

from PyQt5.QtWidgets import *
import  uuid
from sqlalchemy.orm import DeclarativeBase
from models import Unit, Detail, init_db
import request as rq
from sqlalchemy.ext.asyncio import AsyncAttrs


# Функции расчёта
Ky = lambda n1: 10 * ((n1 / 10) ** (1 / 9))
Kv = lambda n1: (n1 / 10) ** (2 / 3)
Ky_v = lambda n1: max(Ky(n1), Kv(n1))
Km = lambda j: [1, 1.7, 2.5, 3][j - 1]


def T(delta_a, N, n1, j):
    min_t = 30.5 * ((N * Ky_v(n1)) / (n1 * Km(j))) ** (1 / 3)
    t_min = delta_a / 80
    t_max = delta_a / 30

    # Подбор подходящих значений из ГОСТ
    t_candidates = [12.7, 15.875, 19.05, 25.4, 31.75, 38.1, 44.45, 50.8]
    valid_t = [t for t in t_candidates if t_min <= t <= t_max]
    for t in valid_t:
        if t >= min_t:
            return t

    raise ValueError("Нет подходящего значения шага цепи в пределах ГОСТ!")


def Z1(n1, t):
    table = {
        12.7: [2780, 2900, 3000],
        15.875: [2000, 2070, 2150],
        19.05: [1520, 1580, 1640],
        25.4: [1000, 1030, 1070],
        31.75: [725, 750, 780],
        38.1: [540, 560, 580],
        44.45: [430, 445, 460],
        50.8: [350, 365, 375],
    }

    row = table.get(t)
    if not row:
        raise ValueError(f"Шаг t={t} не найден в таблице")

    if n1 < row[0]:
        return 20
    elif n1 < row[1]:
        return 25
    else:
        return 30


zc = lambda delta_a, tp, z1, z2: ((2 * delta_a) / tp) + ((z1 + z2) / 2) + (((z2 - z1) ** 2) * tp) / (40 * delta_a)
lamb = lambda zc, z1, z2, t: zc * t - (t * (z1 + z2) / 2)
delta = lambda z2, z1, t: (z2 - z1) * t / 6.28
a = lambda x, y: (x + ((x**2) - 8 * (y**2)) ** 0.5) / 4


class Base(AsyncAttrs, DeclarativeBase):
    pass

class QLabelBuddy(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Проектировочный расчет цепных передач")
        self.setFixedWidth(500)

        # Метки и поля для ввода
        self.label1 = QLabel('&a`', self)
        self.label2 = QLabel('&N ', self)
        self.label3 = QLabel('&z2', self)
        self.label4 = QLabel('&n1 ', self)
        self.label5 = QLabel('&j ', self)
        self.label6 = QLabel('&tp ', self)

        self.LineEdit1 = QLineEdit(self)
        self.LineEdit2 = QLineEdit(self)
        self.LineEdit3 = QLineEdit(self)
        self.LineEdit4 = QLineEdit(self)
        self.LineEdit5 = QLineEdit(self)
        self.LineEdit6 = QLineEdit(self)

        self.label1.setBuddy(self.LineEdit1)
        self.label2.setBuddy(self.LineEdit2)
        self.label3.setBuddy(self.LineEdit3)
        self.label4.setBuddy(self.LineEdit4)
        self.label5.setBuddy(self.LineEdit5)
        self.label6.setBuddy(self.LineEdit6)

        # Подсказки для ввода
        self.label11 = QLabel('', self)
        self.label21 = QLabel('', self)
        self.label31 = QLabel('', self)
        self.label41 = QLabel('', self)
        self.label51 = QLabel('', self)
        self.label61 = QLabel('', self)

        # Расположение элементов
        mainLayout = QGridLayout(self)
        mainLayout.addWidget(self.label1, 0, 0)
        mainLayout.addWidget(self.label2, 1, 0)
        mainLayout.addWidget(self.label3, 2, 0)
        mainLayout.addWidget(self.label4, 3, 0)
        mainLayout.addWidget(self.label5, 4, 0)
        mainLayout.addWidget(self.label6, 5, 0)
        mainLayout.addWidget(self.LineEdit1, 0, 1)
        mainLayout.addWidget(self.LineEdit2, 1, 1)
        mainLayout.addWidget(self.LineEdit3, 2, 1)
        mainLayout.addWidget(self.LineEdit4, 3, 1)
        mainLayout.addWidget(self.LineEdit5, 4, 1)
        mainLayout.addWidget(self.LineEdit6, 5, 1)
        mainLayout.addWidget(self.label11, 0, 2)
        mainLayout.addWidget(self.label21, 1, 2)
        mainLayout.addWidget(self.label31, 2, 2)
        mainLayout.addWidget(self.label41, 3, 2)
        mainLayout.addWidget(self.label51, 4, 2)
        mainLayout.addWidget(self.label61, 5, 2)

        # Кнопка расчёта
        self.btn = QPushButton('&Рассчитать')
        self.btn.setEnabled(False)
        mainLayout.addWidget(self.btn, 6, 1)

        # Поле для вывода результата
        self.output = QLabel("Ответ:")
        mainLayout.addWidget(self.output, 6, 2)

        self.label71 = QLabel('шаг цепи t =', self)
        self.label72 = QLabel('число зубьев ведущей звёздочки z1 = ', self)
        mainLayout.addWidget(self.label71, 7, 0)
        mainLayout.addWidget(self.label72, 7, 2)

        # Сигналы для полей ввода
        self.LineEdit1.textEdited.connect(self.my_slot_function1)
        self.LineEdit2.textEdited.connect(self.my_slot_function2)
        self.LineEdit3.textEdited.connect(self.my_slot_function3)
        self.LineEdit4.textEdited.connect(self.my_slot_function4)
        self.LineEdit5.textEdited.connect(self.my_slot_function5)
        self.LineEdit6.textEdited.connect(self.my_slot_function6)

        # Сигнал для кнопки
        self.btn.clicked.connect(self.buttonClicked)

    def buton(self):
        # Активировать кнопку только если все поля корректно заполнены
        if (
            not self.label11.text()
            and not self.label21.text()
            and not self.label31.text()
            and not self.label41.text()
            and not self.label51.text()
            and not self.label61.text()
        ):
            self.btn.setEnabled(True)
        else:
            self.btn.setEnabled(False)

    def validate_input(self, text, label):
        try:
            float(text)  # Проверка, является ли текст числом
            label.setText('')  # Если число, очищаем ошибку
        except ValueError:
            label.setText('Написано не число')

    def my_slot_function1(self, text):
        self.validate_input(text, self.label11)
        self.buton()

    def my_slot_function2(self, text):
        self.validate_input(text, self.label21)
        self.buton()

    def my_slot_function3(self, text):
        self.validate_input(text, self.label31)
        self.buton()

    def my_slot_function4(self, text):
        self.validate_input(text, self.label41)
        self.buton()

    def my_slot_function5(self, text):
        self.validate_input(text, self.label51)
        self.buton()

    def my_slot_function6(self, text):
        self.validate_input(text, self.label61)
        self.buton()

    def buttonClicked(self):
        global Ky, Kv,Ky_v,Km,delta
        try:
            #unit = Unit()
            #detail = Detail()
            delta_a = float(self.LineEdit1.text())
            N = float(self.LineEdit2.text())
            z2 = float(self.LineEdit3.text())
            n1 = float(self.LineEdit4.text())
            j = int(self.LineEdit5.text())
            tp = float(self.LineEdit6.text())
            # Выполнение расчётов
            t = T(delta_a, N, n1, j)
            z1 = Z1(n1, t)
            a_value = a(
                lamb(zc(delta_a, tp, z1, z2), z1, z2, t),
                delta(z2, z1, t),
            )
            # detail.a = a
            # detail.z2 = z2
            # detail.t = t
            # detail.z1 = z1
            # detail.n1 = n1
            # detail.j = j
            # unit.zc = zc
            # unit.a = lamb
            # unit.Ky = Ky
            # unit.Kv = Kv
            # unit.Ky_v = Ky_v
            # unit.Km = Km
            # unit.N = N
            # unit.delta = delta
            unit_guid = str(uuid.uuid4())
            unit = Unit(
                unit_id=unit_guid,  # или оставьте None, чтобы использовался default
                zc=zc(delta_a, tp, z1, z2),  # Вычисление значения
                a=lamb(zc(delta_a, tp, z1, z2), z1, z2, t),  # Вычисление значения
                Ky=Ky(n1),
                Kv=Kv(n1),
                Ky_v=Ky_v(n1),
                Km=Km(j),
                N=N,
                delta=delta(z2, z1, t)
            )
            # unit.Unit_id = str(uuid.uuid4())
            detail = Detail(
                detail_id=str(uuid.uuid4()),  # Уникальный идентификатор
                a=a_value,  # Межцентровое расстояние
                z1=z1,  # Число зубьев ведущей звёздочки
                z2=z2,  # Число зубьев ведомой звёздочки
                n1=n1,  # Скорость вращения ведущей звёздочки
                j=j,  # Количество рядов звеньев цепи
                unit_id=unit.Unit_id  # Внешний ключ для связи с Unit
            )
            # detail.Detail_id = str(uuid.uuid4())
            # detail.Unit_id = unit.Unit_id
            rq.set_unit(unit)
            rq.set_detail(detail)

            # Обновление меток с результатами
            self.label71.setText(f'шаг цепи t = {t}')
            self.label72.setText(f'число зубьев z1 = {z1}')
            self.output.setText(f'Ответ: {a_value}')

        except ValueError as e:
            # Отображение сообщения об ошибке
            QMessageBox.warning(self, "Ошибка", str(e))
        except Exception as e:
            # Отображение сообщения о других непредвиденных ошибках
            QMessageBox.critical(self, "Непредвиденная ошибка", str(e))

# # Функции расчёта
# Ky = lambda n1: 10 * ((n1 / 10) ** (1 / 9))
# Kv = lambda n1: (n1 / 10) ** (2 / 3)
# Ky_v = lambda n1: max(Ky(n1), Kv(n1))
# Km = lambda j: [1, 1.7, 2.5, 3][j - 1]
#
#
# def T(delta_a, N, n1, j):
#     min_t = 30.5 * ((N * Ky_v(n1)) / (n1 * Km(j))) ** (1 / 3)
#     t_min = delta_a / 80
#     t_max = delta_a / 30
#
#     # Подбор подходящих значений из ГОСТ
#     t_candidates = [12.7, 15.875, 19.05, 25.4, 31.75, 38.1, 44.45, 50.8]
#     valid_t = [t for t in t_candidates if t_min <= t <= t_max]
#     for t in valid_t:
#         if t >= min_t:
#             return t
#
#     raise ValueError("Нет подходящего значения шага цепи в пределах ГОСТ!")
#
#
# def Z1(n1, t):
#     table = {
#         12.7: [2780, 2900, 3000],
#         15.875: [2000, 2070, 2150],
#         19.05: [1520, 1580, 1640],
#         25.4: [1000, 1030, 1070],
#         31.75: [725, 750, 780],
#         38.1: [540, 560, 580],
#         44.45: [430, 445, 460],
#         50.8: [350, 365, 375],
#     }
#
#     row = table.get(t)
#     if not row:
#         raise ValueError(f"Шаг t={t} не найден в таблице")
#
#     if n1 < row[0]:
#         return 20
#     elif n1 < row[1]:
#         return 25
#     else:
#         return 30
#
#
# zc = lambda delta_a, tp, z1, z2: ((2 * delta_a) / tp) + ((z1 + z2) / 2) + (((z2 - z1) ** 2) * tp) / (40 * delta_a)
# lamb = lambda zc, z1, z2, t: zc * t - (t * (z1 + z2) / 2)
# delta = lambda z2, z1, t: (z2 - z1) * t / 6.28
# a = lambda x, y: (x + ((x**2) - 8 * (y**2)) ** 0.5) / 4

def main():
    init_db()
    app = QApplication(sys.argv)  # Создание экземпляра приложения
    main = QLabelBuddy()  # Создание главного окна
    main.show()  # Показ окна
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()