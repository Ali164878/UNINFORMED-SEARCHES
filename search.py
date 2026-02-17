import tkinter as tk
from tkinter import ttk
import heapq
import random
import time
from collections import deque

CELL_SIZE = 55
DELAY = 200
OBSTACLE_PROB = 0.05

COLOR = {
    "bg":       "#1e1e2e",
    "cell":     "#313244",
    "wall":     "#45475a",
    "dyn_wall": "#f38ba8",
    "start":    "#a6e3a1",
    "target":   "#fab387",
    "frontier": "#f9e2af",
    "explored": "#89b4fa",
    "path":     "#a6e3a1",
    "text":     "#cdd6f4",
    "grid_line":"#585b70",
}

MOVES = [
    (-1,  0),
    ( 0,  1),
    ( 1,  0),
    ( 1,  1),
    ( 0, -1),
    (-1, -1),
    (-1,  1),
    ( 1, -1),
]


def generate_grid(rows=8, cols=10, obstacle_ratio=0.20):
    grid = [['0'] * cols for _ in range(rows)]

    sx, sy = random.randint(0, rows - 1), random.randint(0, cols - 1)
    grid[sx][sy] = 's'

    while True:
        tx, ty = random.randint(0, rows - 1), random.randint(0, cols - 1)
        if (tx, ty) != (sx, sy):
            grid[tx][ty] = 't'
            break

    count, total_walls = 0, int(rows * cols * obstacle_ratio)
    while count < total_walls:
        x, y = random.randint(0, rows - 1), random.randint(0, cols - 1)
        if grid[x][y] == '0':
            grid[x][y] = '-1'
            count += 1

    return grid


class Pathfinder:
    @staticmethod
    def find_positions(grid):
        start = target = None
        for i, row in enumerate(grid):
            for j, cell in enumerate(row):
                if cell == 's':
                    start = (i, j)
                elif cell == 't':
                    target = (i, j)
        return start, target

    @staticmethod
    def neighbors(pos, grid):
        x, y = pos
        rows, cols = len(grid), len(grid[0])
        result = []
        for dx, dy in MOVES:
            nx, ny = x + dx, y + dy
            if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] not in ('-1', 'D'):
                result.append((nx, ny))
        return result

    @staticmethod
    def reconstruct(came_from, start, target):
        if target not in came_from:
            return []
        path, cur = [], target
        while cur and cur != start:
            path.append(cur)
            cur = came_from.get(cur)
        path.append(start)
        path.reverse()
        return path


class Visualizer:
    def __init__(self, root, grid):
        self.root  = root
        self.grid  = grid
        self.rows  = len(grid)
        self.cols  = len(grid[0])

        self._build_ui()
        self.draw()

    def _build_ui(self):
        ctrl = tk.Frame(self.root, bg=COLOR["bg"], pady=6)
        ctrl.pack(fill="x", padx=8)

        tk.Label(ctrl, text="Algorithm:", bg=COLOR["bg"], fg=COLOR["text"],
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=(0, 4))

        self.algo_var = tk.StringVar(value="BFS")
        ttk.Combobox(ctrl, textvariable=self.algo_var, width=16, state="readonly",
                     values=["BFS", "DFS", "UCS", "DLS", "IDDFS",
                             "Bidirectional"]).grid(row=0, column=1, padx=4)

        self.dyn_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(ctrl, text="Dynamic Obstacles",
                        variable=self.dyn_var).grid(row=0, column=2, padx=8)

        tk.Label(ctrl, text="Speed (ms):", bg=COLOR["bg"], fg=COLOR["text"],
                 font=("Segoe UI", 9)).grid(row=0, column=3, padx=(8, 2))
        self.speed_var = tk.IntVar(value=DELAY)
        tk.Scale(ctrl, from_=20, to=800, orient="horizontal",
                 variable=self.speed_var, length=100,
                 bg=COLOR["bg"], fg=COLOR["text"],
                 troughcolor="#585b70", highlightthickness=0
                 ).grid(row=0, column=4, padx=4)

        ttk.Button(ctrl, text="▶ Run",      command=self.run     ).grid(row=0, column=5, padx=4)
        ttk.Button(ctrl, text="↺ New Grid", command=self.new_grid).grid(row=0, column=6, padx=4)

        self.canvas = tk.Canvas(
            self.root,
            width=self.cols  * CELL_SIZE,
            height=self.rows * CELL_SIZE,
            bg=COLOR["bg"], highlightthickness=0
        )
        self.canvas.pack(padx=8, pady=(0, 4))

        leg = tk.Frame(self.root, bg=COLOR["bg"])
        leg.pack(fill="x", padx=8, pady=(0, 2))
        for label, color in [
            ("Start",    COLOR["start"]),
            ("Target",   COLOR["target"]),
            ("Wall",     COLOR["wall"]),
            ("Dyn.Wall", COLOR["dyn_wall"]),
            ("Frontier", COLOR["frontier"]),
            ("Explored", COLOR["explored"]),
            ("Path",     COLOR["path"]),
        ]:
            tk.Label(leg, bg=color, width=2).pack(side="left", padx=(6, 2))
            tk.Label(leg, text=label, bg=COLOR["bg"], fg=COLOR["text"],
                     font=("Segoe UI", 8)).pack(side="left")

        self.status_var = tk.StringVar(value="Select an algorithm and press Run.")
        tk.Label(self.root, textvariable=self.status_var,
                 bg="#11111b", fg=COLOR["text"],
                 font=("Segoe UI", 9), anchor="w").pack(fill="x")

    def draw(self, frontier=None, explored=None, path=None):
        frontier = frontier or set()
        explored = explored or set()
        path_set = set(path) if path else set()

        self.canvas.delete("all")
        for i in range(self.rows):
            for j in range(self.cols):
                x1, y1 = j * CELL_SIZE, i * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                val = self.grid[i][j]

                if val == '-1':
                    color = COLOR["wall"]
                elif val == 'D':
                    color = COLOR["dyn_wall"]
                elif val == 's':
                    color = COLOR["start"]
                elif val == 't':
                    color = COLOR["target"]
                elif (i, j) in path_set:
                    color = COLOR["path"]
                elif (i, j) in frontier:
                    color = COLOR["frontier"]
                elif (i, j) in explored:
                    color = COLOR["explored"]
                else:
                    color = COLOR["cell"]

                self.canvas.create_rectangle(x1, y1, x2, y2,
                                             fill=color,
                                             outline=COLOR["grid_line"], width=1)

                if val == 's':
                    lbl = "S"
                elif val == 't':
                    lbl = "T"
                elif val == '-1':
                    lbl = ""
                elif val == 'D':
                    lbl = "X"
                else:
                    lbl = f"{i},{j}"

                self.canvas.create_text(
                    x1 + CELL_SIZE // 2, y1 + CELL_SIZE // 2,
                    text=lbl, fill=COLOR["text"],
                    font=("Segoe UI", 8, "bold")
                )

        self.root.update()

    def spawn_obstacle(self):
        if not self.dyn_var.get():
            return
        if random.random() >= OBSTACLE_PROB:
            return
        empty = [
            (i, j)
            for i in range(self.rows)
            for j in range(self.cols)
            if self.grid[i][j] == '0'
        ]
        if empty:
            x, y = random.choice(empty)
            self.grid[x][y] = 'D'

    def _clear_dynamic(self):
        for i in range(self.rows):
            for j in range(self.cols):
                if self.grid[i][j] == 'D':
                    self.grid[i][j] = '0'

    def _sleep(self):
        time.sleep(self.speed_var.get() / 1000)

    def bfs(self, start, target):
        queue     = deque([start])
        came_from = {start: None}
        explored  = set()

        while queue:
            self.spawn_obstacle()
            cur = queue.popleft()
            explored.add(cur)

            if cur == target:
                return came_from, explored

            for nb in Pathfinder.neighbors(cur, self.grid):
                if nb not in came_from:
                    came_from[nb] = cur
                    queue.append(nb)

            self.draw(set(queue), explored)
            self._sleep()

        return came_from, explored

    def dfs(self, start, target, limit=None):
        stack     = [(start, 0, {start: None})]
        explored  = set()
        came_from = {}

        while stack:
            self.spawn_obstacle()
            cur, depth, path_so_far = stack.pop()
            if cur in explored:
                continue
            explored.add(cur)
            came_from = path_so_far

            if cur == target:
                return came_from, explored

            if limit is None or depth < limit:
                for nb in Pathfinder.neighbors(cur, self.grid):
                    if nb not in path_so_far:
                        new_path     = dict(path_so_far)
                        new_path[nb] = cur
                        stack.append((nb, depth + 1, new_path))

            self.draw({p for p, _, __ in stack}, explored)
            self._sleep()

        return came_from, explored

    def dls(self, start, target, limit=5):
        return self.dfs(start, target, limit=limit)

    def iddfs(self, start, target):
        came_from, explored = {}, set()
        for depth in range(1, 50):
            self.status_var.set(f"IDDFS – trying depth limit {depth} …")
            self.root.update()
            came_from, explored = self.dfs(start, target, limit=depth)
            if target in came_from:
                return came_from, explored
        return came_from, explored

    def ucs(self, start, target):
        heap      = [(0, start)]
        came_from = {start: None}
        cost      = {start: 0}
        explored  = set()

        while heap:
            self.spawn_obstacle()
            c, cur = heapq.heappop(heap)
            if cur in explored:
                continue
            explored.add(cur)

            if cur == target:
                return came_from, explored

            for nb in Pathfinder.neighbors(cur, self.grid):
                dx, dy    = abs(nb[0] - cur[0]), abs(nb[1] - cur[1])
                step_cost = 1.414 if dx and dy else 1.0
                new_cost  = cost[cur] + step_cost
                if nb not in cost or new_cost < cost[nb]:
                    cost[nb]      = new_cost
                    came_from[nb] = cur
                    heapq.heappush(heap, (new_cost, nb))

            self.draw({n for _, n in heap}, explored)
            self._sleep()

        return came_from, explored

    def bidirectional(self, start, target):
        fwd = {start: None}
        bwd = {target: None}
        fq, bq = deque([start]), deque([target])
        meet   = None

        while fq or bq:
            self.spawn_obstacle()

            if fq:
                cur = fq.popleft()
                for nb in Pathfinder.neighbors(cur, self.grid):
                    if nb not in fwd:
                        fwd[nb] = cur
                        fq.append(nb)
                    if nb in bwd:
                        meet = nb
                        break
                if meet:
                    break

            if bq and not meet:
                cur = bq.popleft()
                for nb in Pathfinder.neighbors(cur, self.grid):
                    if nb not in bwd:
                        bwd[nb] = cur
                        bq.append(nb)
                    if nb in fwd:
                        meet = nb
                        break
                if meet:
                    break

            self.draw(set(fq) | set(bq), set(fwd) | set(bwd))
            self._sleep()

        if meet is None:
            return {}, set(fwd) | set(bwd)

        fwd_path, bwd_path = [], []
        cur = meet
        while cur is not None:
            fwd_path.append(cur)
            cur = fwd.get(cur)
        fwd_path.reverse()

        cur = bwd.get(meet)
        while cur is not None:
            bwd_path.append(cur)
            cur = bwd.get(cur)

        full = fwd_path + bwd_path
        came_from = {full[0]: None}
        for k in range(1, len(full)):
            came_from[full[k]] = full[k - 1]
        return came_from, set(fwd) | set(bwd)

    def run(self):
        self._clear_dynamic()
        start, target = Pathfinder.find_positions(self.grid)
        algo = self.algo_var.get()

        self.status_var.set(f"Running {algo} …")
        self.root.update()

        dispatch = {
            "BFS":          lambda: self.bfs(start, target),
            "DFS":          lambda: self.dfs(start, target),
            "DLS":          lambda: self.dls(start, target, limit=5),
            "IDDFS":        lambda: self.iddfs(start, target),
            "UCS":          lambda: self.ucs(start, target),
            "Bidirectional":lambda: self.bidirectional(start, target),
        }
        came_from, explored = dispatch[algo]()

        path = Pathfinder.reconstruct(came_from, start, target)
        self.draw(path=path)

        path_len = len(path) - 1 if len(path) > 1 else 0
        if path:
            msg = (f"✔ {algo} done | "
                   f"Nodes explored: {len(explored)} | "
                   f"Path length: {path_len} steps")
        else:
            msg = f"✘ {algo}: no path found | Nodes explored: {len(explored)}"

        self.status_var.set(msg)

        print("=" * 50)
        print(f"Algorithm : {algo}")
        print(f"Explored  : {len(explored)} nodes")
        print(f"Path len  : {path_len} steps")
        print(f"Path      : {path}")

    def new_grid(self):
        self.grid = generate_grid(8, 10)
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.canvas.config(
            width=self.cols  * CELL_SIZE,
            height=self.rows * CELL_SIZE
        )
        self.status_var.set("New grid generated. Press Run to search.")
        self.draw()


if __name__ == "__main__":
    grid = generate_grid(8, 10)
    root = tk.Tk()
    root.title("GOOD PERFORMANCE TIME APP")
    root.configure(bg=COLOR["bg"])
    root.resizable(False, False)
    Visualizer(root, grid)
    root.mainloop()