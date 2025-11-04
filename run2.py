import sys
from collections import deque, defaultdict

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
            # не пусто по определению, берем лексикографически минимальное
            cut = min(cut_candidates)
            G, _, p = cut.partition('-')
            if p in g[G]: g[G].remove(p)
            if G in g[p]: g[p].remove(G)
            result.append(cut)
        else:
            # Соберём ВСЕ допустимые разрывы вида "G-p" которые лежат на кратчайшей дистанции best_len
            cut_candidates = []
            for dG, G in reachable:
                if dG != best_len:
                    break
                for p in g[G]:
                    if dist_v.get(p, INF) == dG - 1:
                        # допустимый разрыв: G-p
                        cut_candidates.append((G, p))

            # safety: если вдруг пусто — выходим
            if not cut_candidates:
                break

            # Для каждого кандидата вычисляем, сколько у p соседей-шлюзов осталось
            # (эта метрика показывает, насколько опасен узел p)
            enriched = []
            for G, p in cut_candidates:
                gw_deg = sum(1 for nb in g[p] if is_gateway(nb))
                cut_str = f"{G}-{p}"
                # хотим выбирать сначала по максимальному gw_deg, затем по лексикографическому cut_str
                enriched.append(( -gw_deg, cut_str, G, p ))  # минус — потому что min/select по ключом
            # выбираем лучший: минимальный кортеж => максимальный gw_deg и минимальный лексикографически cut_str
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
        else:
            # вирус не движется — цикл продолжится (следующий разрез)
            pass

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
