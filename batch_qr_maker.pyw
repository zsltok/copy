# -*- coding: utf-8 -*-
"""batch_qr_maker.pyw - Batch QR Code Generator
Requires Python 3.7+ (tkinter built-in). No third-party packages needed.
To build exe: pip install pyinstaller && pyinstaller -F -w batch_qr_maker.pyw
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import zlib, struct, os, sys

# ---------------- QR Code from scratch (byte mode, M correction, versions 1-9) ----------------
_EXP = [0]*512
_LOG = [0]*256
_x = 1
for _i in range(255):
    _EXP[_i] = _x
    _LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i-255]

def _gf_mul(a, b):
    return 0 if a == 0 or b == 0 else _EXP[_LOG[a] + _LOG[b]]

def _poly_mul(p, q):
    r = [0]*(len(p)+len(q)-1)
    for j, b in enumerate(q):
        if b:
            for i, a in enumerate(p):
                if a:
                    r[i+j] ^= _gf_mul(a, b)
    return r

def _rs_gen(n):
    g = [1]
    for i in range(n):
        g = _poly_mul(g, [1, _EXP[i]])
    return g

def _rs_ecc(data, n):
    gen = _rs_gen(n)
    res = list(data) + [0]*n
    for i in range(len(data)):
        coef = res[i]
        if coef:
            for j, gv in enumerate(gen):
                res[i+j] ^= _gf_mul(gv, coef)
    return res[-n:]

_BLOCKS_M = {
    1: [(16, 10)], 2: [(28, 16)], 3: [(44, 26)], 4: [(64, 36)], 5: [(86, 48)],
    6: [(54, 32), (54, 32)], 7: [(62, 36), (62, 36)], 8: [(77, 44), (77, 44)], 9: [(91, 55), (91, 55)]
}
_DATA_CAP = {v: sum(d for d, e in _BLOCKS_M[v]) for v in _BLOCKS_M}
_ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
          7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46]}
_MASKS = [
    lambda r, c: (r + c) % 2 == 0,
    lambda r, c: r % 2 == 0,
    lambda r, c: c % 3 == 0,
    lambda r, c: (r + c) % 3 == 0,
    lambda r, c: (r // 2 + c // 3) % 2 == 0,
    lambda r, c: ((r * c) % 2 + (r * c) % 3) == 0,
    lambda r, c: (((r * c) % 2 + (r * c) % 3) % 2) == 0,
    lambda r, c: (((r + c) % 2 + (r * c) % 3) % 2) == 0,
]

def _format_bits(mask):
    data = (0b00 << 3) | mask
    rem = data
    for _ in range(10):
        rem = (rem << 1) ^ (0x537 if (rem >> 9) & 1 else 0)
        rem &= 0x3FF
    return ((data << 10) | rem) ^ 0x5412

def _make_qr(text):
    data = text.encode("utf-8")
    if len(data) > _DATA_CAP[9] - 2:
        raise ValueError(f"Text too long: max {_DATA_CAP[9]-2} bytes (got {len(data)})")
    v = 1
    while _DATA_CAP[v] - 2 < len(data):
        v += 1
    cap = _DATA_CAP[v]
    bits = []
    def app(val, n):
        for i in range(n - 1, -1, -1):
            bits.append((val >> i) & 1)
    app(0b0100, 4)
    app(len(data), 8)
    for b in data:
        app(b, 8)
    maxbits = cap * 8
    app(0, min(4, maxbits - len(bits)))
    while len(bits) % 8:
        bits.append(0)
    pads = [0xEC, 0x11]
    pi = 0
    while len(bits) < maxbits:
        app(pads[pi % 2], 8)
        pi += 1
    cw = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    blocks = []
    off = 0
    for dlen, elen in _BLOCKS_M[v]:
        d = cw[off:off + dlen]
        off += dlen
        blocks.append((d, _rs_ecc(d, elen)))
    inter = []
    for i in range(max(dlen for dlen, elen in _BLOCKS_M[v])):
        for d, e in blocks:
            if i < len(d):
                inter.append(d[i])
    for i in range(max(elen for dlen, elen in _BLOCKS_M[v])):
        for d, e in blocks:
            if i < len(e):
                inter.append(e[i])
    size = 17 + 4 * v
    mod = [[False] * size for _ in range(size)]
    func = [[False] * size for _ in range(size)]
    def setm(r, c, val, isfunc=True):
        if 0 <= r < size and 0 <= c < size:
            mod[r][c] = bool(val)
            if isfunc:
                func[r][c] = True
    def finder(r, c):
        for dr in range(-4, 5):
            for dc in range(-4, 5):
                rr, cc = r + dr, c + dc
                if 0 <= rr < size and 0 <= cc < size:
                    func[rr][cc] = True
                    a, b = abs(dr), abs(dc)
                    if max(a, b) <= 3:
                        mod[rr][cc] = (max(a, b) == 3) or (max(a, b) <= 1)
                    else:
                        mod[rr][cc] = False
    finder(3, 3); finder(3, size - 4); finder(size - 4, 3)
    for i in range(8, size - 8):
        mod[6][i] = i % 2 == 0; func[6][i] = True
        mod[i][6] = i % 2 == 0; func[i][6] = True
    pos = _ALIGN[v]
    for r in pos:
        for c in pos:
            if (r == 6 and c == 6) or (r == 6 and c == size - 7) or (r == size - 7 and c == 6):
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    rr, cc = r + dr, c + dc
                    func[rr][cc] = True
                    mod[rr][cc] = max(abs(dr), abs(dc)) != 1
    def reserve_format():
        for i in range(0, 6): func[8][i] = True; mod[8][i] = False
        func[8][7] = True; mod[8][7] = False
        func[8][8] = True; mod[8][8] = False
        func[7][8] = True; mod[7][8] = False
        for i in range(9, 15): func[14 - i][8] = True; mod[14 - i][8] = False
        for i in range(0, 8): func[size - 1 - i][8] = True; mod[size - 1 - i][8] = False
        for i in range(8, 15): func[8][size - 15 + i] = True; mod[8][size - 15 + i] = False
        func[size - 8][8] = True; mod[size - 8][8] = True
    reserve_format()
    stream = []
    for b in inter:
        for i in range(7, -1, -1):
            stream.append((b >> i) & 1)
    def place(mask_cond):
        m = [row[:] for row in mod]
        si = 0; row = size - 1; inc = -1; col = size - 1
        while col > 0:
            if col == 6: col -= 1
            for _ in range(2):
                while True:
                    c = col if _ == 0 else col - 1
                    if not func[row][c]:
                        bit = stream[si] if si < len(stream) else 0
                        si += 1
                        if mask_cond(row, c): bit ^= 1
                        m[row][c] = bool(bit)
                    row += inc
                    if row < 0 or row >= size:
                        row -= inc; inc = -inc; break
            col -= 2
        return m
    def draw_format(m, mask):
        bits = _format_bits(mask)
        def bit(i): return ((bits >> (14 - i)) & 1) == 1
        def setf(r, c, val): m[r][c] = bool(val)
        for i in range(0, 6): setf(8, i, bit(i))
        setf(8, 7, bit(6)); setf(8, 8, bit(7)); setf(7, 8, bit(8))
        for i in range(9, 15): setf(14 - i, 8, bit(i))
        for i in range(0, 8): setf(size - 1 - i, 8, bit(i))
        for i in range(8, 15): setf(8, size - 15 + i, bit(i))
        setf(size - 8, 8, True)
    def penalty(m):
        p = 0
        for rows in (m, [[m[r][c] for r in range(size)] for c in range(size)]):
            for row in rows:
                run = 1
                for i in range(1, size):
                    if row[i] == row[i - 1]: run += 1
                    else:
                        if run >= 5: p += 3 + (run - 5)
                        run = 1
                if run >= 5: p += 3 + (run - 5)
        for r in range(size - 1):
            for c in range(size - 1):
                if m[r][c] == m[r][c + 1] == m[r + 1][c] == m[r + 1][c + 1]: p += 3
        pat1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
        pat2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]
        for rows in (m, [[m[r][c] for r in range(size)] for c in range(size)]):
            for row in rows:
                for i in range(size - 10):
                    seg = [1 if x else 0 for x in row[i:i + 11]]
                    if seg == pat1 or seg == pat2: p += 40
        dark = sum(1 for r in range(size) for c in range(size) if m[r][c])
        total = size * size
        p += (abs(dark * 20 - total * 10) // total) * 10
        return p
    best = None; bestmask = 0; bestscore = 10 ** 9
    base = place(lambda r, c: False)
    for mask in range(8):
        m = [row[:] for row in base]
        for r in range(size):
            for c in range(size):
                if not func[r][c] and _MASKS[mask](r, c):
                    m[r][c] = not m[r][c]
        draw_format(m, mask)
        sc = penalty(m)
        if sc < bestscore:
            bestscore = sc; best = m; bestmask = mask
    return best

def _png_write(path, mat, scale=8, quiet=4):
    size = len(mat); n = size + quiet * 2
    rows = []
    for r in range(n):
        row = bytearray([0])
        for c in range(n):
            bit = (quiet <= r < quiet + size and quiet <= c < quiet + size and mat[r - quiet][c - quiet])
            row += b"\x00" * scale if bit else b"\xff" * scale
        for _ in range(scale):
            rows.append(bytes(row))
    raw = b"".join(rows)
    w = h = n * scale
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Batch QR Generator")
        self.geometry("520x640")
        self.mat = None
        self.topmost_var = tk.BooleanVar(value=True)
        self.fs_var = tk.BooleanVar(value=False)
        self.scale_var = tk.IntVar(value=8)
        top = tk.Frame(self); top.pack(fill="x", padx=10, pady=8)
        tk.Label(top, text="Batch No:", font=("Microsoft YaHei UI", 11)).pack(side="left")
        self.entry = tk.Entry(top, font=("Microsoft YaHei UI", 12)); self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.gen()); self.entry.focus_set()
        opt = tk.Frame(self); opt.pack(fill="x", padx=10)
        tk.Checkbutton(opt, text="Topmost", variable=self.topmost_var, command=self.apply_top).pack(side="left")
        tk.Checkbutton(opt, text="Fullscreen", variable=self.fs_var, command=self.apply_fs).pack(side="left", padx=12)
        tk.Label(opt, text="Export scale:").pack(side="left", padx=(18, 4))
        ttk.Spinbox(opt, from_=4, to=24, width=5, textvariable=self.scale_var).pack(side="left")
        btns = tk.Frame(self); btns.pack(fill="x", padx=10, pady=6)
        tk.Button(btns, text="Generate", command=self.gen, width=12).pack(side="left")
        tk.Button(btns, text="Save PNG", command=self.save, width=12).pack(side="left", padx=8)
        tk.Button(btns, text="Clear", command=self.clear, width=8).pack(side="left")
        self.canvas = tk.Canvas(self, bg="white", highlightthickness=1, highlightbackground="#999")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.status = tk.Label(self, text="Enter batch number and press Enter. Topmost is ON by default.", anchor="w")
        self.status.pack(fill="x", padx=10, pady=(0, 6))
        self.apply_top()
    def apply_top(self): self.attributes("-topmost", bool(self.topmost_var.get()))
    def apply_fs(self):
        self.attributes("-fullscreen", bool(self.fs_var.get()))
        self.attributes("-topmost", bool(self.topmost_var.get()))
    def gen(self):
        s = self.entry.get().strip()
        if not s: messagebox.showwarning("Tip", "Please enter a batch number"); return
        try:
            self.mat = _make_qr(s); self.draw()
            self.status.config(text=f"Generated: {len(s)} chars, matrix {len(self.mat)}x{len(self.mat)}")
        except Exception as e: messagebox.showerror("Error", str(e))
    def draw(self):
        self.canvas.delete("all")
        if not self.mat: return
        self.update_idletasks()
        w = max(self.canvas.winfo_width(), 200); h = max(self.canvas.winfo_height(), 200)
        n = len(self.mat); quiet = 4; total = n + 2 * quiet
        cell = max(1, min(w, h) // total); ox = (w - cell * total) // 2; oy = (h - cell * total) // 2
        self.canvas.create_rectangle(ox, oy, ox + cell * total, oy + cell * total, fill="white", outline="")
        for r, row in enumerate(self.mat):
            for c, val in enumerate(row):
                if val:
                    x = ox + (c + quiet) * cell; y = oy + (r + quiet) * cell
                    self.canvas.create_rectangle(x, y, x + cell, y + cell, fill="black", outline="")
    def save(self):
        if not self.mat: return
        s = self.entry.get().strip() or "qr"
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:60]
        fn = filedialog.asksaveasfilename(defaultextension=".png", initialfile=f"{safe}.png", filetypes=[("PNG", "*.png")])
        if fn: _png_write(fn, self.mat, int(self.scale_var.get())); self.status.config(text=f"Saved: {fn}")
    def clear(self):
        self.entry.delete(0, "end"); self.mat = None; self.canvas.delete("all"); self.entry.focus_set()

if __name__ == "__main__":
    App().mainloop()
