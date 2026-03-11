import tkinter as tk
from tkinter import ttk
import numpy as np

CELL_SIZE = 15
GRID_ROWS = 40
GRID_COLS = 60
DEFAULT_INTERVAL = 100  # ms between generations


class LifeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Conway's Game of Life  |  生命游戏")
        self.root.resizable(False, False)

        self.grid = np.zeros((GRID_ROWS, GRID_COLS), dtype=np.int8)
        self.running = False
        self._job = None

        self._build_ui()
        self._draw_grid()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self):
        # ---- Canvas ----
        canvas_width = GRID_COLS * CELL_SIZE
        canvas_height = GRID_ROWS * CELL_SIZE

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg="#1e1e2e",
            highlightthickness=0,
        )
        self.canvas.pack(padx=8, pady=(8, 0))
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        # Draw static grid lines once
        for r in range(GRID_ROWS + 1):
            y = r * CELL_SIZE
            self.canvas.create_line(0, y, canvas_width, y, fill="#313244")
        for c in range(GRID_COLS + 1):
            x = c * CELL_SIZE
            self.canvas.create_line(x, 0, x, canvas_height, fill="#313244")

        # ---- Control bar ----
        bar = tk.Frame(self.root, bg="#181825", pady=6)
        bar.pack(fill=tk.X, padx=8, pady=6)

        btn_style = {"font": ("Helvetica", 11), "width": 8, "relief": tk.FLAT, "cursor": "hand2"}

        self.btn_start = tk.Button(
            bar, text="▶ 开始", bg="#a6e3a1", fg="#1e1e2e",
            command=self.start, **btn_style
        )
        self.btn_start.pack(side=tk.LEFT, padx=4)

        self.btn_pause = tk.Button(
            bar, text="⏸ 暂停", bg="#fab387", fg="#1e1e2e",
            command=self.pause, state=tk.DISABLED, **btn_style
        )
        self.btn_pause.pack(side=tk.LEFT, padx=4)

        self.btn_step = tk.Button(
            bar, text="⏭ 步进", bg="#89b4fa", fg="#1e1e2e",
            command=self.step, **btn_style
        )
        self.btn_step.pack(side=tk.LEFT, padx=4)

        self.btn_clear = tk.Button(
            bar, text="🗑 清空", bg="#f38ba8", fg="#1e1e2e",
            command=self.clear, **btn_style
        )
        self.btn_clear.pack(side=tk.LEFT, padx=4)

        self.btn_random = tk.Button(
            bar, text="🎲 随机", bg="#cba6f7", fg="#1e1e2e",
            command=self.randomize, **btn_style
        )
        self.btn_random.pack(side=tk.LEFT, padx=4)

        # Speed slider
        tk.Label(bar, text="速度:", bg="#181825", fg="#cdd6f4",
                 font=("Helvetica", 11)).pack(side=tk.LEFT, padx=(12, 2))

        self.speed_var = tk.IntVar(value=DEFAULT_INTERVAL)
        slider = ttk.Scale(
            bar, from_=20, to=1000,
            orient=tk.HORIZONTAL, length=120,
            variable=self.speed_var,
            command=self._on_speed_change,
        )
        slider.pack(side=tk.LEFT)

        # Generation counter
        self.gen_var = tk.StringVar(value="第 0 代")
        tk.Label(bar, textvariable=self.gen_var, bg="#181825", fg="#cdd6f4",
                 font=("Helvetica", 11), width=10).pack(side=tk.RIGHT, padx=8)

        self.generation = 0

    # --------------------------------------------------------------- Drawing -

    def _draw_grid(self):
        """Redraw only the cell layer; static grid lines are not touched."""
        self.canvas.delete("cell")
        live_cells = np.argwhere(self.grid)
        for r, c in live_cells:
            x1 = int(c) * CELL_SIZE + 1
            y1 = int(r) * CELL_SIZE + 1
            x2 = x1 + CELL_SIZE - 2
            y2 = y1 + CELL_SIZE - 2
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="#a6e3a1", outline="", tags="cell"
            )

    # --------------------------------------------------------------- Logic ---

    @staticmethod
    def _next_generation(grid):
        """Return the next generation grid using Conway's rules.

        Neighbour count is computed with 8 slice shifts into a pre-allocated
        array — avoids creating temporary arrays via np.roll.
        """
        rows, cols = grid.shape
        neighbours = np.zeros((rows, cols), dtype=np.int8)
        # Shift in all 8 directions using slice indexing
        neighbours[1:, 1:]   += grid[:-1, :-1]   # top-left
        neighbours[1:, :]    += grid[:-1, :]      # top
        neighbours[1:, :-1]  += grid[:-1, 1:]     # top-right
        neighbours[:, 1:]    += grid[:, :-1]       # left
        neighbours[:, :-1]   += grid[:, 1:]        # right
        neighbours[:-1, 1:]  += grid[1:, :-1]      # bottom-left
        neighbours[:-1, :]   += grid[1:, :]        # bottom
        neighbours[:-1, :-1] += grid[1:, 1:]       # bottom-right
        return ((neighbours == 3) | ((grid == 1) & (neighbours == 2))).astype(np.int8)

    # --------------------------------------------------------------- Actions -

    def step(self):
        self.grid = self._next_generation(self.grid)
        self.generation += 1
        self.gen_var.set(f"第 {self.generation} 代")
        self._draw_grid()

    def start(self):
        if self.running:
            return
        self.running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self._schedule_step()

    def pause(self):
        self.running = False
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None
        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED)

    def clear(self):
        self.pause()
        self.grid = np.zeros((GRID_ROWS, GRID_COLS), dtype=np.int8)
        self.generation = 0
        self.gen_var.set("第 0 代")
        self._draw_grid()

    def randomize(self):
        self.pause()
        self.grid = np.random.choice([0, 1], size=(GRID_ROWS, GRID_COLS),
                                     p=[0.7, 0.3]).astype(np.int8)
        self.generation = 0
        self.gen_var.set("第 0 代")
        self._draw_grid()

    def _schedule_step(self):
        interval = self.speed_var.get()
        self._job = self.root.after(interval, self._auto_step)

    def _auto_step(self):
        if self.running:
            self.step()
            self._schedule_step()

    def _on_speed_change(self, _=None):
        if self.running:
            if self._job:
                self.root.after_cancel(self._job)
            self._schedule_step()

    # ---------------------------------------------------------- Mouse events -

    def _toggle_cell(self, x, y):
        c = x // CELL_SIZE
        r = y // CELL_SIZE
        if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
            self.grid[r, c] = 1 - self.grid[r, c]
            self._draw_grid()

    def _on_click(self, event):
        self._toggle_cell(event.x, event.y)

    def _on_drag(self, event):
        c = event.x // CELL_SIZE
        r = event.y // CELL_SIZE
        if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
            self.grid[r, c] = 1
            self._draw_grid()


def main():
    root = tk.Tk()
    LifeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
