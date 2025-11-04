import sys
from collections import deque, defaultdict

def is_gateway(node: str) -> bool:
    return node.isupper()

def build_graph(edges):
    g = defaultdict(set)
    for u, v in edges:
        g[u].add(v)
        g[v].add(u)
    return g

def bfs(start: str, graph):
    """Классический BFS: расстояния от start до всех достижимых узлов."""
    dist = {start: 0}
    q = deque([start])
    while q:
        u = q.popleft()
        for v in graph[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist

def bfs_from_gateway(gw: str, graph):
    """BFS от шлюза: расстояния до gw (удобно для восстановления пути c лекс. выбором шагов)."""
    dist = {gw: 0}
    q = deque([gw])
    while q:
        u = q.popleft()
        for v in graph[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist

def choose_target_gateway(cur: str, graph):
    """Выбрать ближайший шлюз (ties: лексикографически). Вернуть (gw, dist_to_gw) или (None, None)."""
    dist_from_cur = bfs(cur, graph)
    reachable_gws = [(d, gw) for gw in graph.keys() if is_gateway(gw) and gw in dist_from_cur]
    if not reachable_gws:
        return None, None
    reachable_gws.sort()  # по (длина, имя шлюза) — как и нужно
    best_dist, best_gw = reachable_gws[0]
    return best_gw, best_dist

def lexicographic_next_step_towards(cur: str, target_gw: str, graph):
    """Следующий шаг вируса по правилам (ties: лексикографически) к target_gw."""
    dist_to_gw = bfs_from_gateway(target_gw, graph)
    if cur not in dist_to_gw:
        return None  # пути нет
    d = dist_to_gw[cur]
    if d == 0:
        return None
    # среди соседей cur выбираем тех, у кого dist = d-1; ties: лексикографически
    candidates = [v for v in graph[cur] if v in dist_to_gw and dist_to_gw[v] == d - 1]
    if not candidates:
        return None
    candidates.sort()
    return candidates[0]

def compute_cut_edge(cur: str, target_gw: str, graph):
    """Определить ребро 'Шлюз-узел' на лексикографически минимальном кратчайшем пути от cur к target_gw."""
    dist_to_gw = bfs_from_gateway(target_gw, graph)
    if cur not in dist_to_gw:
        return None
    d = dist_to_gw[cur]
    # Если вирус уже рядом (d == 1), отключаем target_gw-cur
    # Иначе пройдём вперёд по пути вируса до узла на расстоянии 1 от шлюза.
    node = cur
    while dist_to_gw[node] > 1:
        # выбираем лексикографически минимального соседа, уменьшающего расстояние к шлюзу
        next_nodes = [v for v in graph[node] if v in dist_to_gw and dist_to_gw[v] == dist_to_gw[node] - 1]
        next_nodes.sort()
        node = next_nodes[0]
    # node — последний узел перед шлюзом; отключаем target_gw-node
    u = node
    v = target_gw
    # Формат "ШЛЮЗ-узел" (слева всегда шлюз)
    return f"{v}-{u}"

def cut_edge_in_graph(graph, cut: str):
    """Удалить ребро из графа (двунаправленное). Формат 'A-b' (A — шлюз)."""
    left, _, right = cut.partition('-')
    u, v = left, right
    if v in graph[u]:
        graph[u].remove(v)
    if u in graph[v]:
        graph[v].remove(u)

def virus_move(cur: str, graph):
    """Смоделировать ход вируса по правилам. Возвращает новый узел или cur, если путей нет."""
    gw, _ = choose_target_gateway(cur, graph)
    if gw is None:
        return cur  # нет путей — вирус остаётся (фактически конец)
    nxt = lexicographic_next_step_towards(cur, gw, graph)
    return nxt if nxt is not None else cur

def solve(edges: list[tuple[str, str]]) -> list[str]:
    """
    Решение задачи об изоляции вируса

    Args:
        edges: список коридоров в формате (узел1, узел2)

    Returns:
        список отключаемых коридоров в формате "Шлюз-узел"
    """
    graph = build_graph(edges)
    cur = 'a'  # старт вируса

    result = []

    # Пока существует путь от вируса к какому-либо шлюзу — продолжаем.
    while True:
        gw, _ = choose_target_gateway(cur, graph)
        if gw is None:
            break  # вирус изолирован, путей к шлюзам нет

        # Выбираем и отключаем корректное в лексикографическом смысле ребро "Шлюз-узел"
        cut = compute_cut_edge(cur, gw, graph)
        # Теоретически, если по каким-то причинам пути нет — останавливаемся
        if cut is None:
            break

        result.append(cut)
        cut_edge_in_graph(graph, cut)

        # Ход вируса
        new_cur = virus_move(cur, graph)
        # Если после отключения путей нет — вирус никуда не идёт (изолирован)
        if new_cur == cur and choose_target_gateway(cur, graph)[0] is None:
            break
        cur = new_cur

    return result


def main():
    edges = []
    for line in sys.stdin:
        line = line.strip()
        if line:
            node1, sep, node2 = line.partition('-')
            if sep:
                edges.append((node1, node2))

    result = solve(edges)
    for edge in result:
        print(edge)


if __name__ == "__main__":
    main()
