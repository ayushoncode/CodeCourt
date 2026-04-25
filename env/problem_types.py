"""
Problem archetypes with seeded test generators plus edge-case mutation.
Three archetypes x three difficulty tiers = 9 canonical problem classes.
"""

import random
from typing import Any, Dict, List


def _make_rng(seed: int | None, offset: int) -> random.Random:
    base_seed = 42 if seed is None else seed
    return random.Random(base_seed + offset)


def _gen_array_tests(task_id: int, difficulty: int, seed: int | None = None) -> List[Dict]:
    rng = _make_rng(seed, difficulty * 100)
    tests = []

    if task_id == 0:
        for _ in range(5):
            n = rng.randint(3, 12 * difficulty)
            arr = [rng.randint(-10, 10) for _ in range(n)]
            best = arr[0]
            cur = arr[0]
            for x in arr[1:]:
                cur = max(x, cur + x)
                best = max(best, cur)
            tests.append({"input": f"{n}\n{' '.join(map(str, arr))}", "expected": str(best)})

    elif task_id == 1:
        for _ in range(5):
            n = rng.randint(3, 10 * difficulty)
            arr = [rng.randint(1, 20) for _ in range(n)]
            target = arr[0] + arr[rng.randint(1, n - 1)]
            found = None
            for i in range(n):
                for j in range(i + 1, n):
                    if arr[i] + arr[j] == target:
                        found = f"{i + 1} {j + 1}"
                        break
                if found:
                    break
            if found:
                tests.append({"input": f"{n} {target}\n{' '.join(map(str, arr))}", "expected": found})

    elif task_id == 2:
        for _ in range(5):
            n = rng.randint(3, 8 * difficulty)
            arr = [rng.randint(1, 15) for _ in range(n)]
            dp = [1] * n
            for i in range(1, n):
                for j in range(i):
                    if arr[j] < arr[i]:
                        dp[i] = max(dp[i], dp[j] + 1)
            tests.append({"input": f"{n}\n{' '.join(map(str, arr))}", "expected": str(max(dp))})

    return tests


def _gen_graph_tests(task_id: int, difficulty: int, seed: int | None = None) -> List[Dict]:
    import heapq

    rng = _make_rng(seed, 99 + difficulty * 100)
    tests = []

    if task_id == 0:
        for _ in range(4):
            n = rng.randint(3, 5 * difficulty)
            edges = []
            path = list(range(1, n + 1))
            for i in range(len(path) - 1):
                edges.append((path[i], path[i + 1], rng.randint(1, 10)))
            for _ in range(n):
                u = rng.randint(1, n)
                v = rng.randint(1, n)
                if u != v:
                    edges.append((u, v, rng.randint(1, 10)))

            adj = [[] for _ in range(n + 1)]
            for u, v, w in edges:
                adj[u].append((v, w))
                adj[v].append((u, w))
            dist = [float("inf")] * (n + 1)
            dist[1] = 0
            pq = [(0, 1)]
            while pq:
                d, u = heapq.heappop(pq)
                if d > dist[u]:
                    continue
                for v, w in adj[u]:
                    nd = dist[u] + w
                    if nd < dist[v]:
                        dist[v] = nd
                        heapq.heappush(pq, (dist[v], v))

            edge_lines = "\n".join(f"{u} {v} {w}" for u, v, w in edges)
            tests.append({
                "input": f"{n} {len(edges)}\n{edge_lines}",
                "expected": str(dist[n]) if dist[n] != float("inf") else "-1",
            })

    elif task_id == 1:
        for _ in range(4):
            n = rng.randint(3, 6 * difficulty)
            edges = []
            side_a = list(range(1, n // 2 + 1))
            side_b = list(range(n // 2 + 1, n + 1))
            for a in side_a:
                if side_b:
                    edges.append((a, rng.choice(side_b)))

            color = [-1] * (n + 1)
            adj = [[] for _ in range(n + 1)]
            for u, v in edges:
                adj[u].append(v)
                adj[v].append(u)

            from collections import deque

            is_bip = True
            for start in range(1, n + 1):
                if color[start] != -1:
                    continue
                color[start] = 0
                queue = deque([start])
                while queue:
                    node = queue.popleft()
                    for nxt in adj[node]:
                        if color[nxt] == -1:
                            color[nxt] = 1 - color[node]
                            queue.append(nxt)
                        elif color[nxt] == color[node]:
                            is_bip = False

            edge_lines = "\n".join(f"{u} {v}" for u, v in edges)
            tests.append({
                "input": f"{n} {len(edges)}\n{edge_lines}",
                "expected": "YES" if is_bip else "NO",
            })

    elif task_id == 2:
        for _ in range(4):
            n = rng.randint(4, 8 * difficulty)
            edges = []
            for _ in range(n // 2):
                u = rng.randint(1, n)
                v = rng.randint(1, n)
                if u != v:
                    edges.append((u, v))

            parent = list(range(n + 1))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            for u, v in edges:
                pu, pv = find(u), find(v)
                if pu != pv:
                    parent[pu] = pv

            edge_lines = "\n".join(f"{u} {v}" for u, v in edges) if edges else ""
            tests.append({
                "input": f"{n} {len(edges)}\n{edge_lines}".strip(),
                "expected": str(len(set(find(i) for i in range(1, n + 1)))),
            })

    return tests


def _gen_dp_tests(task_id: int, difficulty: int, seed: int | None = None) -> List[Dict]:
    rng = _make_rng(seed, 77 + difficulty * 100)
    tests = []

    if task_id == 0:
        coins = [1, 2, 5, 10]
        for _ in range(5):
            amount = rng.randint(5, 18 * difficulty)
            dp = [float("inf")] * (amount + 1)
            dp[0] = 0
            for idx in range(1, amount + 1):
                for coin in coins:
                    if coin <= idx and dp[idx - coin] + 1 < dp[idx]:
                        dp[idx] = dp[idx - coin] + 1
            tests.append({
                "input": f"{amount}\n{' '.join(map(str, coins))}",
                "expected": str(dp[amount]) if dp[amount] != float("inf") else "-1",
            })

    elif task_id == 1:
        for _ in range(5):
            n = rng.randint(2, 10 * difficulty)
            a, b = 1, 1
            for _ in range(2, n + 1):
                a, b = b, a + b
            tests.append({"input": str(n), "expected": str(b)})

    elif task_id == 2:
        for _ in range(5):
            la = rng.randint(3, 5 * difficulty)
            lb = rng.randint(3, 5 * difficulty)
            chars = "abcde"
            a = "".join(rng.choice(chars) for _ in range(la))
            b = "".join(rng.choice(chars) for _ in range(lb))
            dp = [[0] * (lb + 1) for _ in range(la + 1)]
            for i in range(1, la + 1):
                for j in range(1, lb + 1):
                    if a[i - 1] == b[j - 1]:
                        dp[i][j] = dp[i - 1][j - 1] + 1
                    else:
                        dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
            tests.append({"input": f"{a}\n{b}", "expected": str(dp[la][lb])})

    return tests


ARCHETYPES = {
    "array": {
        "name": "Array Algorithms",
        "tasks": [
            "maximum subarray sum",
            "two sum (find indices)",
            "longest increasing subsequence",
        ],
        "optimal_complexity": ["O(N)", "O(N)", "O(N log N)"],
        "descriptions": [
            (
                "Given an array of {n} integers (possibly negative), "
                "find the maximum sum of any contiguous subarray.\n"
                "Input: First line n, second line n space-separated integers.\n"
                "Output: Single integer - the maximum subarray sum."
            ),
            (
                "Given an array of {n} positive integers and a target k, "
                "find two distinct indices i < j such that arr[i] + arr[j] == k.\n"
                "Input: First line: n k. Second line: n integers.\n"
                "Output: Two 1-indexed integers i j. Guaranteed a solution exists."
            ),
            (
                "Given an array of {n} integers, find the length of the "
                "longest strictly increasing subsequence.\n"
                "Input: First line n, second line n integers.\n"
                "Output: Single integer."
            ),
        ],
        "generator": _gen_array_tests,
    },
    "graph": {
        "name": "Graph Traversal",
        "tasks": [
            "shortest path node 1 to node n",
            "bipartite graph check",
            "number of connected components",
        ],
        "optimal_complexity": ["O((V+E) log V)", "O(V+E)", "O(V+E)"],
        "descriptions": [
            (
                "Given a weighted undirected graph with {n} nodes and {m} edges, "
                "find the shortest path distance from node 1 to node n.\n"
                "Input: First line: n m. Then m lines: u v w.\n"
                "Output: Shortest distance, or -1 if unreachable."
            ),
            (
                "Given an undirected graph with {n} nodes and {m} edges, "
                "determine if it is bipartite.\n"
                "Input: First line: n m. Then m lines: u v.\n"
                "Output: YES or NO."
            ),
            (
                "Given an undirected graph with {n} nodes and {m} edges, "
                "count the number of connected components.\n"
                "Input: First line: n m. Then m lines: u v.\n"
                "Output: Single integer."
            ),
        ],
        "generator": _gen_graph_tests,
    },
    "dp": {
        "name": "Dynamic Programming",
        "tasks": [
            "minimum coins to make amount",
            "ways to climb n stairs",
            "longest common subsequence",
        ],
        "optimal_complexity": ["O(N*C)", "O(N)", "O(N*M)"],
        "descriptions": [
            (
                "Given a target amount and coin denominations [1,2,5,10], "
                "find the minimum number of coins to make the amount.\n"
                "Input: First line: amount. Second line: coin denominations.\n"
                "Output: Minimum coins, or -1 if impossible."
            ),
            (
                "You can climb 1 or 2 steps at a time. "
                "In how many distinct ways can you climb n stairs?\n"
                "Input: Single integer n.\n"
                "Output: Number of ways."
            ),
            (
                "Given two strings A and B, find the length of their "
                "longest common subsequence.\n"
                "Input: Two lines, each a string of lowercase letters.\n"
                "Output: Single integer."
            ),
        ],
        "generator": _gen_dp_tests,
    },
}


def _compute_expected(archetype: str, task_id: int, payload: dict[str, Any]) -> str:
    if archetype == "array" and task_id == 0:
        arr = payload["arr"]
        best = cur = arr[0]
        for value in arr[1:]:
            cur = max(value, cur + value)
            best = max(best, cur)
        return str(best)

    if archetype == "array" and task_id == 1:
        arr = payload["arr"]
        target = payload["target"]
        for i in range(len(arr)):
            for j in range(i + 1, len(arr)):
                if arr[i] + arr[j] == target:
                    return f"{i + 1} {j + 1}"
        return "1 1"

    if archetype == "array" and task_id == 2:
        arr = payload["arr"]
        tails: list[int] = []
        for value in arr:
            lo, hi = 0, len(tails)
            while lo < hi:
                mid = (lo + hi) // 2
                if tails[mid] < value:
                    lo = mid + 1
                else:
                    hi = mid
            if lo == len(tails):
                tails.append(value)
            else:
                tails[lo] = value
        return str(len(tails))

    if archetype == "graph" and task_id == 0:
        import heapq

        n = payload["n"]
        edges = payload["edges"]
        adj = [[] for _ in range(n + 1)]
        for u, v, w in edges:
            adj[u].append((v, w))
            adj[v].append((u, w))
        dist = [float("inf")] * (n + 1)
        dist[1] = 0
        pq = [(0, 1)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for v, w in adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return str(dist[n]) if dist[n] != float("inf") else "-1"

    if archetype == "graph" and task_id == 1:
        from collections import deque

        n = payload["n"]
        edges = payload["edges"]
        adj = [[] for _ in range(n + 1)]
        for u, v in edges:
            adj[u].append(v)
            adj[v].append(u)
        color = [-1] * (n + 1)
        for start in range(1, n + 1):
            if color[start] != -1:
                continue
            color[start] = 0
            queue = deque([start])
            while queue:
                node = queue.popleft()
                for nxt in adj[node]:
                    if color[nxt] == -1:
                        color[nxt] = 1 - color[node]
                        queue.append(nxt)
                    elif color[nxt] == color[node]:
                        return "NO"
        return "YES"

    if archetype == "graph" and task_id == 2:
        n = payload["n"]
        parent = list(range(n + 1))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for u, v in payload["edges"]:
            pu, pv = find(u), find(v)
            if pu != pv:
                parent[pu] = pv
        return str(len({find(i) for i in range(1, n + 1)}))

    if archetype == "dp" and task_id == 0:
        amount = payload["amount"]
        coins = payload["coins"]
        dp = [float("inf")] * (amount + 1)
        dp[0] = 0
        for idx in range(1, amount + 1):
            for coin in coins:
                if coin <= idx and dp[idx - coin] + 1 < dp[idx]:
                    dp[idx] = dp[idx - coin] + 1
        return str(dp[amount]) if dp[amount] != float("inf") else "-1"

    if archetype == "dp" and task_id == 1:
        n = payload["n"]
        if n <= 1:
            return "1"
        a, b = 1, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return str(b)

    if archetype == "dp" and task_id == 2:
        a = payload["a"]
        b = payload["b"]
        dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
        for i in range(1, len(a) + 1):
            for j in range(1, len(b) + 1):
                if a[i - 1] == b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        return str(dp[len(a)][len(b)])

    raise ValueError(f"Unsupported archetype/task combo: {archetype}/{task_id}")


def _format_case(archetype: str, task_id: int, payload: dict[str, Any]) -> Dict[str, str]:
    if archetype == "array" and task_id == 0:
        arr = payload["arr"]
        return {"input": f"{len(arr)}\n{' '.join(map(str, arr))}", "expected": _compute_expected(archetype, task_id, payload)}
    if archetype == "array" and task_id == 1:
        arr = payload["arr"]
        return {"input": f"{len(arr)} {payload['target']}\n{' '.join(map(str, arr))}", "expected": _compute_expected(archetype, task_id, payload)}
    if archetype == "array" and task_id == 2:
        arr = payload["arr"]
        return {"input": f"{len(arr)}\n{' '.join(map(str, arr))}", "expected": _compute_expected(archetype, task_id, payload)}
    if archetype == "graph" and task_id == 0:
        lines = "\n".join(f"{u} {v} {w}" for u, v, w in payload["edges"])
        return {"input": f"{payload['n']} {len(payload['edges'])}\n{lines}".strip(), "expected": _compute_expected(archetype, task_id, payload)}
    if archetype == "graph" and task_id in {1, 2}:
        lines = "\n".join(f"{u} {v}" for u, v in payload["edges"])
        return {"input": f"{payload['n']} {len(payload['edges'])}\n{lines}".strip(), "expected": _compute_expected(archetype, task_id, payload)}
    if archetype == "dp" and task_id == 0:
        return {"input": f"{payload['amount']}\n{' '.join(map(str, payload['coins']))}", "expected": _compute_expected(archetype, task_id, payload)}
    if archetype == "dp" and task_id == 1:
        return {"input": str(payload["n"]), "expected": _compute_expected(archetype, task_id, payload)}
    if archetype == "dp" and task_id == 2:
        return {"input": f"{payload['a']}\n{payload['b']}", "expected": _compute_expected(archetype, task_id, payload)}
    raise ValueError(f"Unsupported archetype/task combo: {archetype}/{task_id}")


def _build_adversarial_case(archetype: str, task_id: int, difficulty: int, rng: random.Random) -> Dict[str, str]:
    if archetype == "array" and task_id == 0:
        arr = [-(rng.randint(1, 4)) for _ in range(max(6, difficulty * 12))]
        arr[rng.randrange(len(arr))] = difficulty * 9
        return _format_case(archetype, task_id, {"arr": arr})

    if archetype == "array" and task_id == 1:
        arr = [difficulty * 3] * max(4, difficulty * 6)
        arr[-1] = difficulty * 5
        return _format_case(archetype, task_id, {"arr": arr, "target": arr[0] + arr[1]})

    if archetype == "array" and task_id == 2:
        arr = [5] * max(5, difficulty * 7)
        arr[-1] = 6
        return _format_case(archetype, task_id, {"arr": arr})

    if archetype == "graph" and task_id == 0:
        n = max(4, difficulty * 4)
        edges = [(i, i + 1, 20) for i in range(1, n)] + [(i, i + 1, 1) for i in range(1, n)]
        return _format_case(archetype, task_id, {"n": n, "edges": edges})

    if archetype == "graph" and task_id == 1:
        n = max(3, difficulty * 4 + 1)
        edges = [(1, 2), (2, 3), (3, 1)] + [(3, node) for node in range(4, n + 1)]
        return _format_case(archetype, task_id, {"n": n, "edges": edges})

    if archetype == "graph" and task_id == 2:
        n = max(5, difficulty * 5)
        edges = [(1, 2), (2, 3), (4, 5)]
        return _format_case(archetype, task_id, {"n": n, "edges": edges})

    if archetype == "dp" and task_id == 0:
        return _format_case(archetype, task_id, {"amount": difficulty * 11, "coins": [1, 2, 5, 10]})

    if archetype == "dp" and task_id == 1:
        return _format_case(archetype, task_id, {"n": difficulty * 10})

    if archetype == "dp" and task_id == 2:
        alphabet = "abcde"
        a = "".join(rng.choice(alphabet) for _ in range(max(4, difficulty * 4)))
        return _format_case(archetype, task_id, {"a": a, "b": a[::-1]})

    raise ValueError(f"Unsupported archetype/task combo: {archetype}/{task_id}")


def generate_test_cases(archetype: str, task_id: int, difficulty: int, seed: int | None = None) -> List[Dict]:
    """Generate seeded cases plus one adversarial hidden case."""
    arch = ARCHETYPES[archetype]
    tests = list(arch["generator"](task_id, difficulty, seed))
    tests.append(_build_adversarial_case(archetype, task_id, difficulty, _make_rng(seed, 1000 + task_id * 17)))
    return tests


def get_problem_description(archetype: str, task_id: int, difficulty: int) -> str:
    """Return formatted problem statement."""
    arch = ARCHETYPES[archetype]
    desc = arch["descriptions"][task_id]
    n_vals = {1: "small (n <= 100)", 2: "medium (n <= 1000)", 3: "large (n <= 100000)"}
    return desc.replace("{n}", n_vals.get(difficulty, "n")).replace("{m}", "varies")


def build_problem(archetype: str, task_id: int, difficulty: int, seed: int | None = None) -> Dict[str, Any]:
    """Build a complete problem dict ready for the environment."""
    arch = ARCHETYPES[archetype]
    test_cases = generate_test_cases(archetype, task_id, difficulty, seed=seed)
    public_test_count = min(2, len(test_cases))
    public_test_cases = test_cases[:public_test_count]
    hidden_test_cases = test_cases[public_test_count:] or test_cases[-1:]
    desc = get_problem_description(archetype, task_id, difficulty)

    return {
        "archetype": archetype,
        "task_id": task_id,
        "difficulty": difficulty,
        "title": f"{arch['name']} - {arch['tasks'][task_id]}",
        "description": desc,
        "input_format": desc,
        "output_format": "See description above.",
        "constraints": f"Difficulty tier {difficulty}/3",
        "test_cases": test_cases,
        "public_test_cases": public_test_cases,
        "hidden_test_cases": hidden_test_cases,
        "optimal_complexity": arch["optimal_complexity"][task_id],
        "variant_seed": seed,
    }
