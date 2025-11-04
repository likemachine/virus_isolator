import sys
from collections import deque, defaultdict
from functools import lru_cache


def canonical_edge(u: str, v: str) -> tuple[str, str]:
    """Каноническое представление неориентированного ребра."""
    a, b = sorted((u, v))
    return a, b

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
    reachable_gws = [(dist_from_cur[gw], gw) for gw in graph.keys() if is_gateway(gw) and gw in dist_from_cur]
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
    initial_edges = tuple(sorted(canonical_edge(u, v) for u, v in edges))

    @lru_cache(maxsize=None)
    def dfs(cur: str, edges_key: tuple[tuple[str, str], ...]):
        graph = build_graph(edges_key)
        target_gw, _ = choose_target_gateway(cur, graph)
        if target_gw is None:
            return ()

        available_cuts = []
        for node in graph:
            if not is_gateway(node):
                continue
            for nb in graph[node]:
                if is_gateway(nb):
                    continue
                available_cuts.append(f"{node}-{nb}")
        available_cuts = sorted(set(available_cuts))

        edges_set = set(edges_key)
        for cut in available_cuts:
            gw, _, regular = cut.partition('-')
            edge_repr = canonical_edge(gw, regular)
            if edge_repr not in edges_set:
                continue

            new_edges = list(edges_key)
            new_edges.remove(edge_repr)
            new_edges_key = tuple(sorted(new_edges))
            new_graph = build_graph(new_edges_key)

            new_target, _ = choose_target_gateway(cur, new_graph)
            if new_target is None:
                return (cut,)

            next_pos = virus_move(cur, new_graph)
            if next_pos is None:
                next_pos = cur
            if is_gateway(next_pos):
                continue  # вирус попал в шлюз — неправильный сценарий

            suffix = dfs(next_pos, new_edges_key)
            if suffix is not None:
                return (cut,) + suffix

        return None

    result = dfs('a', initial_edges)
    return list(result or [])


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
