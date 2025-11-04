import sys
from collections import deque

# Вирус всегда стартует из узла 'a' (см. README)
START_NODE = "a"

def is_gateway(x: str) -> bool:
    # шлюзы — заглавные буквы по условию
    return x.isalpha() and x[0].isupper()

def add_edge(g, u, v):
    g.setdefault(u, set()).add(v)
    g.setdefault(v, set()).add(u)

def remove_edge(g, u, v):
    if u in g and v in g[u]:
        g[u].remove(v)
    if v in g and u in g[v]:
        g[v].remove(u)

def parse_edges(lines):
    g = {}
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


def canonical_graph(g):
    """Каноническое представление графа для мемоизации."""
    return tuple(sorted((node, tuple(sorted(neigh))) for node, neigh in g.items()))

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

def virus_can_reach_gateway(g, gateways, virus_pos):
    dist, _ = bfs_from(virus_pos, g)
    return any(gw in dist for gw in gateways)

def sorted_gateway_edges(g, gateways):
    for gw in sorted(gateways):
        neighbors = g.get(gw)
        if not neighbors:
            continue
        for node in sorted(neighbors):
            yield gw, node

def find_plan(g, gateways, virus_pos, memo):
    key = (virus_pos, canonical_graph(g))
    if key in memo:
        return memo[key]

    if not virus_can_reach_gateway(g, gateways, virus_pos):
        memo[key] = []
        return []

    best = None
    for gw, node in sorted_gateway_edges(g, gateways):
        remove_edge(g, gw, node)
        new_pos = step_move_virus(g, gateways, virus_pos)
        if not is_gateway(new_pos):
            plan_tail = find_plan(g, gateways, new_pos, memo)
            if plan_tail is not None:
                best = [f"{gw}-{node}"] + plan_tail
        add_edge(g, gw, node)
        if best is not None:
            break

    memo[key] = best
    return best

def solve(lines):
    g, gateways, normals = parse_edges(lines)
    g.setdefault(START_NODE, set())
    for gw in gateways:
        g.setdefault(gw, set())
    memo = {}
    plan = find_plan(g, gateways, START_NODE, memo)
    return plan or []

def main():
    data = [line.rstrip("\n") for line in sys.stdin]
    result = solve(data)
    sys.stdout.write("\n".join(result))

if __name__ == "__main__":
    main()
