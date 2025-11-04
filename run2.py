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
    # граф
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
    
    # если вирус = шлюз
    non_gate = [v for v in g if not is_gateway(v)]
    if non_gate:
        virus = min(non_gate)
    else:
        return []  # все узлы — шлюзы, нечего заражать

    result: list[str] = []

    # старт вируса — лексикографически минимальный строчный узел
    virus_candidates = [v for v in g if v and v[0].islower()]
    virus = min(virus_candidates) if virus_candidates else min(g.keys())

    result: list[str] = []

    while True:
        # расстояния от вируса
        dist_v = bfs_from_one(virus, g)

        # ближайшая длина к какому-либо шлюзу
        reachable = [(dist_v.get(G, INF), G) for G in gateways]
        reachable.sort()
        best_len = reachable[0][0]
        if best_len >= INF:
            break  # пути к шлюзам нет

        cut_candidates = []
        for dG, G in reachable:
            if dG != best_len:
                break
            for p in g[G]:
                if dist_v.get(p, INF) == dG - 1:
                    cut_candidates.append(f"{G}-{p}")

        cut = min(cut_candidates)
        G, _, p = cut.partition('-')

        if p in g[G]:
            g[G].remove(p)
        if G in g[p]:
            g[p].remove(G)
        result.append(cut)

        dist_any = bfs_from_many(gateways, g)
        if dist_any.get(virus, INF) >= INF:
            break

        next_steps = [nb for nb in g[virus] if dist_any.get(nb, INF) < dist_any.get(virus, INF)]
        if next_steps:
            virus = min(next_steps)
        else:
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
