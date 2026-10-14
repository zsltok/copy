# -*- coding: utf-8 -*-
"""
批次号二维码生成器
使用标准 qrcode 库，确保生成的二维码可被正常扫描。
打包命令：pyinstaller -F -w batch_qr_maker.pyw
"""
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import qrcode
from PIL import Image


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("批次号二维码生成器")
        self.geometry("420x520")
        self.minsize(320, 420)
        self.modules = None          # qrcode 生成的二维布尔矩阵
        self.quiet = 4               # 静区模块数

        # 状态变量
        self.topmost_var = tk.BooleanVar(value=True)
        self.fs_var = tk.BooleanVar(value=False)
        self.scale_var = tk.IntVar(value=10)      # 导出倍率
        self.display_var = tk.IntVar(value=6)     # 显示模块像素（控制大小）

        # 配置网格权重，让画布可随窗口缩放
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # ---------- 二维码画布（上方，自适应） ----------
        canvas_frame = tk.Frame(self, bg="white", highlightthickness=1,
                                highlightbackground="#999")
        canvas_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda e: self.draw())

        # ---------- 控制面板（下方） ----------
        panel = tk.Frame(self)
        panel.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # 批次号输入
        row1 = tk.Frame(panel)
        row1.pack(fill="x", pady=(4, 2))
        tk.Label(row1, text="批次号：", font=("Microsoft YaHei UI", 10)).pack(side="left")
        self.entry = tk.Entry(row1, font=("Microsoft YaHei UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.entry.bind("<Return>", lambda e: self.gen())
        self.entry.focus_set()

        # 大小 + 导出倍率
        row2 = tk.Frame(panel)
        row2.pack(fill="x", pady=4)
        tk.Label(row2, text="显示大小：").pack(side="left")
        self.size_spin = ttk.Spinbox(row2, from_=3, to=20, width=4,
                                     textvariable=self.display_var,
                                     command=self.draw)
        self.size_spin.pack(side="left")
        tk.Label(row2, text="导出倍率：").pack(side="left", padx=(12, 0))
        ttk.Spinbox(row2, from_=4, to=40, width=4,
                    textvariable=self.scale_var).pack(side="left")

        # 选项
        row3 = tk.Frame(panel)
        row3.pack(fill="x", pady=2)
        tk.Checkbutton(row3, text="置顶", variable=self.topmost_var,
                       command=self.apply_top).pack(side="left")
        tk.Checkbutton(row3, text="全屏", variable=self.fs_var,
                       command=self.apply_fs).pack(side="left", padx=10)

        # 按钮
        row4 = tk.Frame(panel)
        row4.pack(fill="x", pady=(4, 2))
        tk.Button(row4, text="生成二维码", command=self.gen,
                  width=11).pack(side="left")
        tk.Button(row4, text="保存图片", command=self.save,
                  width=11).pack(side="left", padx=8)
        tk.Button(row4, text="清空", command=self.clear,
                  width=8).pack(side="left")

        # 状态栏
        self.status = tk.Label(panel, text="输入批次号后按回车生成；默认置顶。",
                               anchor="w", fg="#555")
        self.status.pack(fill="x", pady=(4, 0))

        self.apply_top()

    # ---------- 窗口行为 ----------
    def apply_top(self):
        self.attributes("-topmost", bool(self.topmost_var.get()))

    def apply_fs(self):
        self.attributes("-fullscreen", bool(self.fs_var.get()))
        self.attributes("-topmost", bool(self.topmost_var.get()))

    # ---------- 生成 ----------
    def gen(self):
        s = self.entry.get().strip()
        if not s:
            messagebox.showwarning("提示", "请输入批次号")
            return
        try:
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=1,
                border=self.quiet,
            )
            qr.add_data(s)
            qr.make(fit=True)
            self.modules = qr.modules
            self.draw()
            self.status.config(
                text=f"已生成：{len(s)} 个字符，版本 V{qr.version}，"
                     f"矩阵 {len(self.modules)}×{len(self.modules)}"
            )
        except Exception as e:
            messagebox.showerror("生成失败", str(e))

    # ---------- 绘制（自适应画布） ----------
    def draw(self, event=None):
        self.canvas.delete("all")
        if not self.modules:
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return

        n = len(self.modules)
        total = n + 2 * self.quiet

        # 用户指定的模块像素，但不超过画布可容纳的最大值
        user_cell = max(3, int(self.display_var.get()))
        max_cell = min(cw, ch) // total
        cell = min(user_cell, max_cell)
        if cell < 1:
            cell = 1

        ox = (cw - cell * total) // 2
        oy = (ch - cell * total) // 2

        # 白底
        self.canvas.create_rectangle(ox, oy, ox + cell * total,
                                     oy + cell * total, fill="white", outline="")
        # 黑块
        for r, row in enumerate(self.modules):
            for c, val in enumerate(row):
                if val:
                    x = ox + (c + self.quiet) * cell
                    y = oy + (r + self.quiet) * cell
                    self.canvas.create_rectangle(x, y, x + cell, y + cell,
                                                 fill="black", outline="")

    # ---------- 保存 ----------
    def save(self):
        if not self.modules:
            return
        s = self.entry.get().strip() or "qr"
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in s)[:60]
        fn = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile=f"{safe}.png",
            filetypes=[("PNG", "*.png")]
        )
        if not fn:
            return
        try:
            scale = max(1, int(self.scale_var.get()))
            n = len(self.modules)
            total_px = (n + 2 * self.quiet) * scale
            img = Image.new("1", (total_px, total_px), 1)
            px = img.load()
            for r, row in enumerate(self.modules):
                for c, val in enumerate(row):
                    if val:
                        for dy in range(scale):
                            for dx in range(scale):
                                px[(c + self.quiet) * scale + dx,
                                   (r + self.quiet) * scale + dy] = 0
            img.save(fn)
            self.status.config(text=f"已保存：{fn}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    # ---------- 清空 ----------
    def clear(self):
        self.entry.delete(0, "end")
        self.modules = None
        self.canvas.delete("all")
        self.status.config(text="已清空，请输入批次号。")
        self.entry.focus_set()


if __name__ == "__main__":
    App().mainloop()
