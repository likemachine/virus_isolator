import sys
from collections import deque, defaultdict

def solve(edges: list[tuple[str, str]]) -> list[str]:
    # строим неориентированный граф
    g: dict[str, set[str]] = defaultdict(set)
    for u, v in edges:
        g[u].add(v)
        g[v].add(u)

    # классификация узлов
    def is_gateway(x: str) -> bool:
        return x and x[0].isupper()

    gateways = sorted([n for n in g.keys() if is_gateway(n)])
    # гарантируется старт вируса в 'a'
    virus = 'a'

    result: list[str] = []

    # bfs расстояния от текущей позиции вируса
    def bfs_dist(start: str) -> dict[str, int]:
        dist = {start: 0}
        q = deque([start])
        while q:
            cur = q.popleft()
            for nb in g[cur]:
                if nb not in dist:
                    dist[nb] = dist[cur] - 1 if is_gateway(nb) else dist[cur] + 1
                    dist[nb] = dist[cur] + 1
                    q.append(nb)
        return dist

    # выбор целевого шлюза по минимальному расстоянию
    def choose_target_gateway(dist: dict[str, int]) -> str | None:
        reachable = [(dist[gx], gx) for gx in gateways if gx in dist]
        if not reachable:
            return None
        reachable.sort()  # по расстоянию, затем лексикографически по имени шлюза
        return reachable[0][1]

    # шаг вируса к целевому шлюзу
    def move_virus(v: str, target_gw: str, dist: dict[str, int]) -> str:
        dist_from_gw = bfs_from_node(target_gw)
        candidates = []
        for nb in g[v]:
            if nb in dist_from_gw and v in dist_from_gw:
                if dist_from_gw[nb] == dist_from_gw[v] - 1:
                    candidates.append(nb)
        if not candidates:
            return v
        return sorted(candidates)[0]

    # вспомогательный bfs
    def bfs_from_node(start: str) -> dict[str, int]:
        dist = {start: 0}
        q = deque([start])
        while q:
            cur = q.popleft()
            for nb in g[cur]:
                if nb not in dist:
                    dist[nb] = dist[cur] + 1
                    q.append(nb)
        return dist

    while True:
        dist = bfs_dist(virus)
        target = choose_target_gateway(dist)
        if target is None:
            break
        
        penult = []
        d_t = dist[target]
        for nb in g[target]:
            if nb in dist and dist[nb] == d_t - 1:
                penult.append(nb)

        cut_node = sorted(penult)[0] if penult else None

        if cut_node is None:
            break

        result.append(f"{target}-{cut_node}")
        g[target].discard(cut_node)
        g[cut_node].discard(target)

        dist_after = bfs_dist(virus)
        target_after = choose_target_gateway(dist_after)
        if target_after is None:
            break

        dist_from_target = bfs_from_node(target_after)

        step_candidates = [nb for nb in g[virus]
                           if nb in dist_from_target and virus in dist_from_target
                           and dist_from_target[nb] == dist_from_target[virus] - 1]

        if step_candidates:
            virus = sorted(step_candidates)[0]
        else:
            pass

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
