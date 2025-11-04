import sys
from collections import deque, defaultdict

# Вирус всегда стартует из узла 'a' (см. README)
START_NODE = "a"

def is_gateway(x: str) -> bool:
    # шлюзы — заглавные буквы по условию
    return x.isalpha() and x[0].isupper()

def add_edge(g, u, v):
    g[u].add(v)
    g[v].add(u)

def remove_edge(g, u, v):
    if v in g[u]: g[u].remove(v)
    if u in g[v]: g[v].remove(u)

def parse_edges(lines):
    g = defaultdict(set)
    gateways = set()
    normals = set()

    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        u, v = raw.split("-")
        add_edge(g, u, v)
        if is_gateway(u):
            gateways.add(u)
        else:
            normals.add(u)
        if is_gateway(v):
            gateways.add(v)
        else:
            normals.add(v)
    return g, gateways, normals

def bfs_from(start, g):
    """Обычный BFS c лексикографическим порядком обхода соседей.
    Возвращает dist и parent для восстановления одного (лексикографически детерминированного) кратчайшего пути.
    """
    dist = {start: 0}
    parent = {start: None}
    q = deque([start])

    while q:
        u = q.popleft()
        # важен детерминизм: соседи в лекс. порядке
        for v in sorted(g[u]):
            if v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = u
                q.append(v)
    return dist, parent

def reachable_gateways(dist, gateways):
    return sorted([gw for gw in gateways if gw in dist], key=lambda x: (dist[x], x))

def reconstruct_path(parent, target):
    path = []
    cur = target
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    path.reverse()
    return path  # от старта до target

def lex_min_edge(edges):
    # edges — итерируемое из ("Gateway","node")
    return min(edges, key=lambda e: (e[0], e[1]))

def step_choose_cut(g, gateways, virus_pos):
    """Выбираем ребро для отключения на текущем ходу.
       1) Если вирус соседствует с каким-либо шлюзом — рубим лекс. минимальное "Шлюз-узел".
       2) Иначе — выбираем ближайший шлюз (BFS), при равенстве — лекс. мин по имени шлюза,
          и рубим ребро (Шлюз — его сосед по кратчайшему пути).
    """
    # 1) Если рядом есть шлюзы — сразу режем одно из таких ребер
    adj_gate_edges = [(gw, virus_pos) for gw in g[virus_pos] if is_gateway(gw)]
    if adj_gate_edges:
        gw, node = lex_min_edge(adj_gate_edges)
        return gw, node

    # 2) Иначе — ищем ближайший шлюз
    dist, parent = bfs_from(virus_pos, g)
    candidates = [gw for gw in gateways if gw in dist]
    if not candidates:
        return None  # путей до шлюзов нет — мы уже выиграли

    # сортировка по (дистанция, имя шлюза)
    target_gw = min(candidates, key=lambda gw: (dist[gw], gw))

    # путь от вируса до шлюза; его предпоследний узел — сосед шлюза
    path = reconstruct_path(parent, target_gw)
    assert len(path) >= 2, "Если шлюз достижим, путь должен иметь хотя бы 2 узла"
    neighbor_before_gateway = path[-2]
    return target_gw, neighbor_before_gateway

def step_move_virus(g, gateways, current_pos):
    """Симулируем один ход вируса:
       - он выбирает ближайший шлюз; при равенстве — лекс. мин по имени
       - делает шаг по одному из кратчайших путей; при равенстве — в лекс. мин следующий узел
    """
    dist, parent = bfs_from(current_pos, g)
    # reachable gateways
    rgs = reachable_gateways(dist, gateways)
    if not rgs:
        return current_pos  # двигаться некуда — все шлюзы недостижимы
    target_gw = rgs[0]  # уже с учетом (min dist, лекс. порядок)
    # Если расстояние == 1, следующий шаг — непосредственно в шлюз
    if dist[target_gw] == 1:
        return target_gw  # вирус «вошел» в шлюз (проигрыш, но по условию такого не случится при корректном планe)
    # Иначе восстановим путь и сдвинем на первый шаг
    path = reconstruct_path(parent, target_gw)
    # path: [current_pos, next_node, ..., target_gw]
    return path[1] if len(path) >= 2 else current_pos

def solve(lines):
    g, gateways, normals = parse_edges(lines)
    virus_pos = START_NODE
    out = []

    # Итерируем, пока есть путь от вируса к какому-либо шлюзу
    while True:
        dist, _ = bfs_from(virus_pos, g)
        if not any(gw in dist for gw in gateways):
            break  # шлюзы недостижимы — готово

        cut = step_choose_cut(g, gateways, virus_pos)
        if cut is None:
            break  # уже отрезаны

        gw, node = cut
        # фиксируем действие
        out.append(f"{gw}-{node}")
        # применяем действие к графу
        remove_edge(g, gw, node)

        # после отключения — ход вируса
        new_pos = step_move_virus(g, gateways, virus_pos)

        # Если вирус «вошел» в шлюз, теоретически это провал; входные гарантии обещают, что такого не будет
        # Но на всякий случай — прерываем.
        if is_gateway(new_pos):
            # Можно выбросить исключение или просто завершить — оставим завершение.
            break

        virus_pos = new_pos

    return out

def main():
    data = [line.rstrip("\n") for line in sys.stdin]
    result = solve(data)
    sys.stdout.write("\n".join(result))

if __name__ == "__main__":
    main()
