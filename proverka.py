Ky = lambda n1: 10 * ((n1 / 10) ** (1 / 9))
Kv = lambda n1: (n1 / 10) ** (2 / 3)
Ky_v = lambda n1: max(Ky(n1), Kv(n1))
Km = lambda j: [1, 1.7, 2.5, 3][j - 1]


def T(delta_a, N, n1, j):
    print(Km(j))
    min_t = 30.5 * ((N * Ky_v(n1)) / (n1 * Km(j))) ** (1 / 3)
    print(min_t)
    t_min = delta_a / 80
    t_max = delta_a / 30
    print(t_min, t_max)

    # Подбор подходящих значений из ГОСТ
    t_candidates = [12.7, 15.875, 19.05, 25.4, 31.75, 38.1, 44.45, 50.8]
    valid_t = [t for t in t_candidates if t_min <= t <= t_max]
    print(valid_t)
    for t in valid_t:
        if t >= min_t:
            print(t)
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

# Пример с тестовыми значениями
delta_a = 2000
N = 200
n1 = 2780
z2 = 10
j = 1
tp = 12.7

# Выполнение расчета
try:
    t = T(delta_a, N, n1, j)
    z1 = Z1(n1, t)
    result_zc = zc(delta_a, tp, z1, z2)
    result_lamb = lamb(result_zc, z1, z2, t)
    result_delta = delta(z2, z1, t)
    final_result = a(result_lamb, result_delta)

    print(f"Рассчитанный шаг цепи: {t}")
    print(f"Число зубьев ведущей звездочки (Z1): {z1}")
    print(f"Результат zc: {result_zc}")
    print(f"Результат lamb: {result_lamb}")
    print(f"Результат delta: {result_delta}")
    print(f"Итоговый результат: {final_result}")

except ValueError as e:
    print(f"Ошибка: {e}")
