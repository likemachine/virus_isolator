import sys
from collections import deque, defaultdict

def solve(edges: list[tuple[str, str]]) -> list[str]:
    # Построим неориентированный граф
    g: dict[str, set[str]] = defaultdict(set)
    for u, v in edges:
        g[u].add(v)
        g[v].add(u)

    # Классификация узлов
    def is_gateway(x: str) -> bool:
        return x and x[0].isupper()

    gateways = sorted([n for n in g.keys() if is_gateway(n)])
    # Гарантируется старт вируса в 'a'
    virus = 'a'

    result: list[str] = []

    # BFS расстояния от текущей позиции вируса
    def bfs_dist(start: str) -> dict[str, int]:
        dist = {start: 0}
        q = deque([start])
        while q:
            cur = q.popleft()
            for nb in g[cur]:
                if nb not in dist:
                    dist[nb] = dist[cur] - 1 if is_gateway(nb) else dist[cur] + 1
                    # Примечание: штраф/бонус не нужен — просто стандартный BFS.
                    # Оставим корректно:
                    dist[nb] = dist[cur] + 1
                    q.append(nb)
        return dist

    # Выбор целевого шлюза по минимальному расстоянию (лексикографический тай-брейк)
    def choose_target_gateway(dist: dict[str, int]) -> str | None:
        reachable = [(dist[gx], gx) for gx in gateways if gx in dist]
        if not reachable:
            return None
        reachable.sort()  # по расстоянию, затем лексикографически по имени шлюза
        return reachable[0][1]

    # Шаг вируса к целевому шлюзу
    def move_virus(v: str, target_gw: str, dist: dict[str, int]) -> str:
        # Идём в соседа с минимальным именем, который лежит на кратчайшем пути к target_gw
        # На кратчайшем пути должно выполняться: dist[nb] == dist[v] - 1 относительно целевого шлюза.
        # У нас dist — расстояния от вируса. Удобнее посчитать расстояния от target_gw.
        dist_from_gw = bfs_from_node(target_gw)
        # среди соседей v выбираем тех, у кого dist_from_gw[nb] == dist_from_gw[v] - 1
        candidates = []
        for nb in g[v]:
            if nb in dist_from_gw and v in dist_from_gw:
                if dist_from_gw[nb] == dist_from_gw[v] - 1:
                    candidates.append(nb)
        if not candidates:
            # если почему-то нет кандидатов (не должно происходить при корректных данных) — остаёмся
            return v
        return sorted(candidates)[0]

    # Вспомогательный BFS от произвольной вершины (для движения вируса по кратчайшему пути к шлюзу)
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

    # Главный цикл: режем, двигаем, пока есть путь к какому-либо шлюзу
    while True:
        dist = bfs_dist(virus)
        target = choose_target_gateway(dist)
        if target is None:
            # Путей к шлюзам нет — изолировано
            break

        # Найдём узлы-предпоследние на кратчайших путях к целевому шлюзу:
        # Для этого удобнее иметь расстояния от вируса: путь к target длины dist[target].
        # Предпоследние узлы N — такие соседи target, что dist[N] == dist[target] - 1.
        penult = []
        d_t = dist[target]
        for nb in g[target]:
            if nb in dist and dist[nb] == d_t - 1:
                penult.append(nb)

        # Если несколько — выбираем лексикографически минимальный узел,
        # а коридор "Шлюз-узел" сравнивается сначала по шлюзу (он уже выбран минимально), затем по узлу.
        cut_node = sorted(penult)[0] if penult else None

        # На практике penult должен существовать, иначе шлюз недостижим — но тогда target не был бы выбран.
        if cut_node is None:
            break  # на всякий случай

        # Отключаем (target-cut_node)
        result.append(f"{target}-{cut_node}")
        # Удаляем ребро из графа
        g[target].discard(cut_node)
        g[cut_node].discard(target)

        # Двигаем вирус на один шаг по правилам
        dist_after = bfs_dist(virus)
        target_after = choose_target_gateway(dist_after)
        if target_after is None:
            # Уже изолировали — ход вируса не важен
            break

        # Если вирус стоит рядом с каким-то шлюзом, он бы пошёл туда на следующем ходу,
        # но мы всегда режем до его движения. Теперь посчитаем кратчайший путь к выбранному шлюзу
        # и сделаем один шаг (лексикографический тай-брейк учтём).
        # Для шага нам нужны расстояния от целевого шлюза.
        dist_from_target = bfs_from_node(target_after)

        # Соседи вируса, ведущие ближе к target_after
        step_candidates = [nb for nb in g[virus]
                           if nb in dist_from_target and virus in dist_from_target
                           and dist_from_target[nb] == dist_from_target[virus] - 1]

        if step_candidates:
            virus = sorted(step_candidates)[0]
        else:
            # Если кратчайшего пути нет (может случиться, когда разрез полностью отсёк все пути),
            # вирус остаётся на месте, а цикл завершится на следующей проверке.
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
