import sys
from collections import deque, defaultdict
from functools import lru_cache

INF = 10**9

def bfs_from_many(starts, g):
    dist = {v: INF for v in g}
    q = deque()
    for s in starts:
        if s in g and dist[s] == INF:
            dist[s] = 0
            q.append(s)
    while q:
        v = q.popleft()
        for nb in g[v]:
            if dist[nb] == INF:
                dist[nb] = dist[v] + 1
                q.append(nb)
    return dist

def bfs_from_one(start, g):
    dist = {start: 0}
    q = deque([start])
    while q:
        v = q.popleft()
        for nb in g[v]:
            if nb not in dist:
                dist[nb] = dist[v] + 1
                q.append(nb)
    return dist

# ====== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ТОЧНОЙ ПРОВЕРКИ СТРАТЕГИИ ======

def _is_gateway(x: str) -> bool:
    return bool(x) and x[0].isupper()

def _normalize_gw_edge(u: str, v: str) -> str:
    # нормализуем ребро, инцидентное шлюзу, в формат "G-p"
    if _is_gateway(u):
        return f"{u}-{v}"
    else:
        return f"{v}-{u}"

def _can_traverse(u: str, v: str, available_edges: set[str]) -> bool:
    if _is_gateway(u) or _is_gateway(v):
        return _normalize_gw_edge(u, v) in available_edges
    return True

def _virus_is_isolated(virus: str, g: dict[str, set[str]], available_edges: set[str]) -> bool:
    # BFS с учётом уже отрезанных gateway-рёбер
    q = deque([virus])
    seen = {virus}
    while q:
        v = q.popleft()
        for nb in g[v]:
            if not _can_traverse(v, nb, available_edges):
                continue
            if nb not in seen:
                # если дойдём до шлюза — вирус НЕ изолирован
                if _is_gateway(nb):
                    return False
                seen.add(nb)
                q.append(nb)
    # ни один шлюз не достижим
    return True

def _neighbors_for_state(v: str, g: dict[str, set[str]], available_edges: set[str]) -> list[str]:
    # возможные ходы вируса (по одному ребру), учитывая уже отрезанные gateway-рёбра
    res = []
    for nb in g[v]:
        if _can_traverse(v, nb, available_edges):
            res.append(nb)
    return res

def _defender_has_winning_strategy(virus: str,
                                   g: dict[str, set[str]],
                                   gateway_edges: set[str]) -> bool:
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def win(virus_node: str, available_frozen: frozenset) -> bool:
        available = set(available_frozen)

        if _virus_is_isolated(virus_node, g, available):
            return True

        moves = _neighbors_for_state(virus_node, g, available)
        for nb in moves:
            if _is_gateway(nb):
                return False

        for nb in moves:
            found_cut = False
            for e in available:
                new_av = set(available)
                new_av.remove(e)
                if win(nb, frozenset(new_av)):
                    found_cut = True
                    break
            if not found_cut:
                return False

        return True

    return win(virus, frozenset(gateway_edges))

# ===================================================================

def solve(edges: list[tuple[str, str]]) -> list[str]:
    # строим граф
    g: dict[str, set[str]] = defaultdict(set)
    for u, v in edges:
        g[u].add(v)
        g[v].add(u)

    if not g:
        return []

    is_gateway = lambda x: x and x[0].isupper()

    gateways = sorted([v for v in g if is_gateway(v)])
    if not gateways:
        return []

    # старт — минимальный НЕ-шлюзовой узел; если все — шлюзы, возвращаем пусто
    non_gate = [v for v in g if not is_gateway(v)]
    if non_gate:
        virus = min(non_gate)
    else:
        return []

    # точная проверка существования выигрышной стратегии
    gateway_edges = set()
    for G in gateways:
        for p in g[G]:
            gateway_edges.add(f"{G}-{p}")  # формат G-p

    if not _defender_has_winning_strategy(virus, g, gateway_edges):
        # нет победной стратегии → по условию возвращаем пустой список (никаких ходов)
        return []

    result: list[str] = []

    while True:
        # расстояния от вируса и от любых шлюзов
        dist_v = bfs_from_one(virus, g)
        dist_any = bfs_from_many(gateways, g)

        # ближайшая длина до какого-либо шлюза
        reachable = [(dist_v.get(G, INF), G) for G in gateways]
        reachable.sort()
        best_len = reachable[0][0]
        if best_len >= INF:
            break  # пути к шлюзам нет

        # если вирус соседствует со шлюзом — режем это ребро (формат G-virus)
        if best_len == 1:
            cut_candidates = [f"{G}-{virus}" for G in g[virus] if is_gateway(G)]
            cut = min(cut_candidates)  # не пуст по определению
            G, _, p = cut.partition('-')
            if p in g[G]: g[G].remove(p)
            if G in g[p]: g[p].remove(G)
            result.append(cut)
        else:
            # соберём все допустимые разрывы "G-p" на кратчайшей дистанции
            cut_candidates = []
            for dG, G in reachable:
                if dG != best_len:
                    break
                for p in g[G]:
                    if dist_v.get(p, INF) == dG - 1:
                        cut_candidates.append((G, p))

            if not cut_candidates:
                break

            # приоритет узлам-предшественникам с большим числом соседей-шлюзов
            enriched = []
            for G, p in cut_candidates:
                gw_deg = sum(1 for nb in g[p] if is_gateway(nb))
                cut_str = f"{G}-{p}"
                enriched.append((-gw_deg, cut_str, G, p))  # max gw_deg, затем лексикографический cut_str
            enriched.sort()
            _, cut_str, G, p = enriched[0]

            # разрезаем
            if p in g[G]: g[G].remove(p)
            if G in g[p]: g[p].remove(G)
            result.append(cut_str)

        # проверяем достижимость вируса от шлюзов после разреза
        dist_any_after = bfs_from_many(gateways, g)
        if dist_any_after.get(virus, INF) >= INF:
            break

        # шаг вируса к ближайшему шлюзу (если возможен)
        next_steps = [nb for nb in g[virus] if dist_any_after.get(nb, INF) < dist_any_after.get(virus, INF)]
        if next_steps:
            virus = min(next_steps)

    return result


def main():
    edges = []
    for line in sys.stdin:
        line = line.strip()
        if line:
            a, sep, b = line.partition('-')
            if sep:
                edges.append((a, b))
    for e in solve(edges):
        print(e)

if __name__ == "__main__":
    main()
