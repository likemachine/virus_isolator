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
    # вирус проходит по ребру, инцидентному шлюзу, только если оно не удалено
    if _is_gateway(u) or _is_gateway(v):
        return _normalize_gw_edge(u, v) in available_edges
    return True

def _virus_is_isolated(virus: str, g: dict[str, set[str]], available_edges: set[str]) -> bool:
    q = deque([virus])
    seen = {virus}
    while q:
        v = q.popleft()
        for nb in g[v]:
            if not _can_traverse(v, nb, available_edges):
                continue
            if nb not in seen:
                if _is_gateway(nb):
                    return False
                seen.add(nb)
                q.append(nb)
    return True

def _neighbors_for_state(v: str, g: dict[str, set[str]], available_edges: set[str]) -> list[str]:
    res = []
    for nb in g[v]:
        if _can_traverse(v, nb, available_edges):
            res.append(nb)
    return res

def _collect_gateway_edges(g, gateways):
    ge = set()
    for G in gateways:
        for p in g[G]:
            ge.add(f"{G}-{p}")
    return ge

def _defender_has_winning_strategy(virus: str,
                                   g: dict[str, set[str]],
                                   gateway_edges: set[str]) -> bool:
    # В нашей модели защитник делает разрез, затем ходит вирус.
    # Оракул проверяет: из данной позиции (перед ходом вируса) существует
    # стратегия защитника, гарантирующая, что вирус не достигнет шлюза никогда.
    @lru_cache(maxsize=None)
    def win(virus_node: str, available_frozen: frozenset) -> bool:
        available = set(available_frozen)

        # уже изолирован? победа защитника
        if _virus_is_isolated(virus_node, g, available):
            return True

        # вирус ХОДИТ ПЕРВЫМ: если может шагнуть сразу в шлюз -> проигрыш защитника
        moves = _neighbors_for_state(virus_node, g, available)
        for nb in moves:
            if _is_gateway(nb):
                return False

        # для КАЖДОГО возможного хода вируса должен существовать разрез,
        # после которого позиция снова выигрышна для защитника
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

# ====== ВСПОМОГАТЕЛЬНОЕ: применить разрез на копии графа ======

def _apply_cut_on_copy(g: dict[str, set[str]], cut: str):
    G, _, p = cut.partition('-')
    new_g = {k: set(vs) for k, vs in g.items()}
    if p in new_g.get(G, set()):
        new_g[G].remove(p)
    if G in new_g.get(p, set()):
        new_g[p].remove(G)
    return new_g

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

    # точная проверка: вообще существует ли выигрышная стратегия?
    gateway_edges = _collect_gateway_edges(g, gateways)
    if not _defender_has_winning_strategy(virus, g, gateway_edges):
        return []

    result: list[str] = []

    while True:
        # расстояния от вируса и от шлюзов
        dist_v = bfs_from_one(virus, g)
        reachable = sorted((dist_v.get(G, INF), G) for G in gateways)
        best_len = reachable[0][0]
        if best_len >= INF:
            break  # пути к шлюзам нет (уже изолирован)

        # вирус уже на шлюзе -> проигрыш (по условию вывод пустой)
        if best_len == 0:
            return []

        # если вирус соседствует со шлюзом — режем это ребро (формат G-virus),
        # но только если такой разрез сохраняет выигрышность позиции
        if best_len == 1:
            # все допустимые кандидаты этого типа
            raw_candidates = [f"{G}-{virus}" for G in g[virus] if is_gateway(G)]
        else:
            # Собираем все допустимые разрывы "G-p" на кратчайшей дистанции
            raw_candidates = []
            for dG, G in reachable:
                if dG != best_len:
                    break
                for p in g[G]:
                    if dist_v.get(p, INF) == dG - 1:
                        raw_candidates.append(f"{G}-{p}")

        # among raw_candidates — выбираем только те, после которых ПОЗИЦИЯ остаётся ВЫИГРЫШНОЙ
        safe_candidates = []
        for cut in raw_candidates:
            g_after = _apply_cut_on_copy(g, cut)
            gw_edges_after = _collect_gateway_edges(g_after, gateways)
            if _defender_has_winning_strategy(virus, g_after, gw_edges_after):
                safe_candidates.append(cut)

        if not safe_candidates:
            # ни один разрез не сохраняет выигрыш — значит, мы по факту в проигрышной ветке
            return []

        # приоритет: максимальная "опасность" предузла (сколько у p соседей-шлюзов), затем лексикографически
        def danger_key(cut: str):
            G, _, p = cut.partition('-')
            gw_deg = sum(1 for nb in g[p] if is_gateway(nb))
            return (-gw_deg, cut)

        cut = min(safe_candidates, key=danger_key)

        # применяем разрез на реальном графе
        G, _, p = cut.partition('-')
        if p in g[G]:
            g[G].remove(p)
        if G in g[p]:
            g[p].remove(G)
        result.append(cut)

        # после разреза: если вирус уже недостижим — закончить
        dist_any_after = bfs_from_many(gateways, g)
        if dist_any_after.get(virus, INF) >= INF:
            break

        # шаг вируса к ближайшему шлюзу
        next_steps = [nb for nb in g[virus] if dist_any_after.get(nb, INF) < dist_any_after.get(virus, INF)]
        if next_steps:
            virus = min(next_steps)
        else:
            # не двинулся — продолжаем резать
            pass

    return result


def main():
    edges = []
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        # строго один дефис
        parts = line.split('-')
        if len(parts) != 2:
            continue  # игнорируем кривые строки
        a, b = parts[0].strip(), parts[1].strip()
        if not a or not b:
            continue
        edges.append((a, b))

    for e in solve(edges):
        print(e)

if __name__ == "__main__":
    main()
