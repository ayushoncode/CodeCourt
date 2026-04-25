"""
All LLM prompts for Setter and Solver agents.
Kept separate so they can be iterated on without touching agent logic.
"""

SETTER_SYSTEM = """You are the Setter agent in CodeCourt, an adversarial competitive programming arena.

Your job:
1. You receive a problem template (archetype + difficulty tier).
2. You must write a CLEAN, CORRECT Python solution to the problem.
3. Your goal: generate a solution that the Solver agent will FAIL on.
   - Use tight constraints that require optimal algorithms
   - Think about edge cases: empty arrays, disconnected graphs, integer overflow risks
   - Do NOT make the problem unsolvable

CRITICAL RULES:
- Your code MUST solve the problem correctly (you must pass your own test cases)
- Output ONLY valid Python code. No explanation. No markdown fences. Just code.
- Your code reads from stdin and writes to stdout.
- If you can't solve it, output a simple brute-force solution — never output broken code.
"""

SETTER_USER_TEMPLATE = """Problem archetype: {archetype}
Task: {task}
Difficulty: {difficulty}/3

Problem statement:
{description}

Sample test case input:
{sample_input}

Expected output:
{sample_output}

Write a Python solution that solves this problem correctly.
Output only the Python code, nothing else."""


SOLVER_SYSTEM = """You are the Solver agent in CodeCourt, an adversarial competitive programming arena.

Your job:
1. You receive a competitive programming problem statement.
2. Write the most efficient Python solution possible.
3. Your goal: pass ALL test cases within time and memory limits.

CRITICAL RULES:
- Time limit: 2 seconds. Memory limit: 256MB.
- Avoid O(N^2) or worse for large inputs — use optimal algorithms.
- Output ONLY valid Python code. No explanation. No markdown fences. Just code.
- Your code reads from stdin and writes to stdout.
- Import sys and use sys.stdin for faster input when needed.
"""

SOLVER_USER_TEMPLATE = """Problem:
{description}

Write an efficient Python solution.
Output only the Python code, nothing else."""


# Reference solutions for each archetype/task (used in baseline comparisons)
REFERENCE_SOLUTIONS = {
    ("array", 0): """\
import sys
input = sys.stdin.readline
n = int(input())
arr = list(map(int, input().split()))
best = cur = arr[0]
for x in arr[1:]:
    cur = max(x, cur + x)
    best = max(best, cur)
print(best)
""",
    ("array", 1): """\
import sys
input = sys.stdin.readline
line1 = input().split()
n, target = int(line1[0]), int(line1[1])
arr = list(map(int, input().split()))
seen = {}
for i, x in enumerate(arr):
    if target - x in seen:
        print(seen[target-x]+1, i+1)
        break
    seen[x] = i
""",
    ("array", 2): """\
import sys
from bisect import bisect_left, insort
input = sys.stdin.readline
n = int(input())
arr = list(map(int, input().split()))
tails = []
for x in arr:
    pos = bisect_left(tails, x)
    if pos == len(tails):
        tails.append(x)
    else:
        tails[pos] = x
print(len(tails))
""",
    ("graph", 0): """\
import sys, heapq
input = sys.stdin.readline
n, m = map(int, input().split())
adj = [[] for _ in range(n+1)]
for _ in range(m):
    u, v, w = map(int, input().split())
    adj[u].append((v,w)); adj[v].append((u,w))
dist = [float('inf')]*(n+1); dist[1]=0
pq = [(0,1)]
while pq:
    d,u = heapq.heappop(pq)
    if d>dist[u]: continue
    for v,w in adj[u]:
        if dist[u]+w<dist[v]:
            dist[v]=dist[u]+w; heapq.heappush(pq,(dist[v],v))
print(dist[n] if dist[n]!=float('inf') else -1)
""",
    ("graph", 1): """\
import sys
from collections import deque
input = sys.stdin.readline
n, m = map(int, input().split())
adj = [[] for _ in range(n+1)]
for _ in range(m):
    u, v = map(int, input().split())
    adj[u].append(v); adj[v].append(u)
color = [-1]*(n+1); bip = True
for s in range(1,n+1):
    if color[s]==-1:
        color[s]=0; q=deque([s])
        while q:
            u=q.popleft()
            for v in adj[u]:
                if color[v]==-1: color[v]=1-color[u]; q.append(v)
                elif color[v]==color[u]: bip=False
print("YES" if bip else "NO")
""",
    ("graph", 2): """\
import sys
input = sys.stdin.readline
n, m = map(int, input().split())
parent = list(range(n+1))
def find(x):
    while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
    return x
for _ in range(m):
    u,v = map(int, input().split())
    pu,pv=find(u),find(v)
    if pu!=pv: parent[pu]=pv
print(len(set(find(i) for i in range(1,n+1))))
""",
    ("dp", 0): """\
import sys
input = sys.stdin.readline
amount = int(input())
coins = list(map(int, input().split()))
dp = [float('inf')]*(amount+1); dp[0]=0
for i in range(1,amount+1):
    for c in coins:
        if c<=i and dp[i-c]+1<dp[i]: dp[i]=dp[i-c]+1
print(dp[amount] if dp[amount]!=float('inf') else -1)
""",
    ("dp", 1): """\
n = int(input())
dp = [0]*(n+1); dp[0]=1; dp[1]=1
for i in range(2,n+1): dp[i]=dp[i-1]+dp[i-2]
print(dp[n])
""",
    ("dp", 2): """\
a = input().strip(); b = input().strip()
la, lb = len(a), len(b)
dp = [[0]*(lb+1) for _ in range(la+1)]
for i in range(1,la+1):
    for j in range(1,lb+1):
        if a[i-1]==b[j-1]: dp[i][j]=dp[i-1][j-1]+1
        else: dp[i][j]=max(dp[i-1][j],dp[i][j-1])
print(dp[la][lb])
""",
}


# Brute-force (bad) solutions — used to show untrained baseline behavior
BRUTE_FORCE_SOLUTIONS = {
    ("array", 0): """\
n = int(input())
arr = list(map(int, input().split()))
best = float('-inf')
for i in range(n):
    for j in range(i, n):
        best = max(best, sum(arr[i:j+1]))
print(best)
""",
    ("dp", 0): """\
from functools import lru_cache
amount = int(input())
coins = list(map(int, input().split()))
@lru_cache(maxsize=None)
def dp(rem):
    if rem == 0: return 0
    if rem < 0: return float('inf')
    return 1 + min(dp(rem - c) for c in coins)
result = dp(amount)
print(result if result != float('inf') else -1)
""",
    ("array", 1): """\
line1 = input().split()
n, target = int(line1[0]), int(line1[1])
arr = list(map(int, input().split()))
for i in range(n):
    for j in range(i + 1, n):
        if arr[i] + arr[j] == target:
            print(i + 1, j + 1)
            raise SystemExit
print(1, 1)
""",
    ("array", 2): """\
n = int(input())
arr = list(map(int, input().split()))
best = 1 if arr else 0
for i in range(n):
    length = 1
    prev = arr[i]
    for j in range(i + 1, n):
        if arr[j] > prev:
            length += 1
            prev = arr[j]
    if length > best:
        best = length
print(best)
""",
    ("graph", 0): """\
n, m = map(int, input().split())
best = {}
for _ in range(m):
    u, v, w = map(int, input().split())
    if u == 1:
        best[v] = min(best.get(v, 10**18), w)
    if v == 1:
        best[u] = min(best.get(u, 10**18), w)
print(best.get(n, -1))
""",
    ("graph", 1): """\
n, m = map(int, input().split())
deg = [0] * (n + 1)
for _ in range(m):
    u, v = map(int, input().split())
    deg[u] += 1
    deg[v] += 1
print("YES" if m <= n else "NO")
""",
    ("graph", 2): """\
n, m = map(int, input().split())
seen = set()
for _ in range(m):
    u, v = map(int, input().split())
    seen.add(u)
    seen.add(v)
isolated = n - len(seen)
print(max(1, isolated))
""",
    ("dp", 1): """\
n = int(input())
if n <= 2:
    print(n)
else:
    print(2 ** (n - 2))
""",
    ("dp", 2): """\
a = input().strip()
b = input().strip()
matches = 0
for ch in a:
    if ch in b:
        matches += 1
print(min(matches, len(b)))
""",
}
