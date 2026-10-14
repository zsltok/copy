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
        self.geometry("200x200")

        self.modules = None          # qrcode 二维布尔矩阵
        self.quiet = 4               # 静区模块数

        # 状态变量
        self.topmost_var = tk.BooleanVar(value=True)
        self.fs_var = tk.BooleanVar(value=False)
        self.scale_var = tk.IntVar(value=10)       # 导出倍率
        self.display_var = tk.IntVar(value=6)      # 显示模块像素
        self.expanded = tk.BooleanVar(value=True)  # 面板展开状态

        # ---------- 二维码 Canvas（无边框无内边距） ----------
        self.canvas = tk.Canvas(
            self, bg="white", highlightthickness=0, bd=0
        )
        self.canvas.pack()

        # 展开/收起按钮（浮在二维码右下角）
        self.toggle_btn = tk.Button(
            self, text="▼", width=2, command=self.toggle_panel,
            bg="#f0f0f0", relief="flat", font=("Arial", 8), cursor="hand2"
        )
        self.toggle_btn.place(
            in_=self.canvas, relx=1.0, rely=1.0, anchor="se", x=-1, y=-1
        )

        # ---------- 控制面板 ----------
        self.panel = tk.Frame(self, padx=6, pady=4)
        self.build_panel()
        self.panel.pack(fill="x")

        # 初始化
        self.draw()
        self.fit_window()
        self.apply_top()

    # ---------- 构建面板 ----------
    def build_panel(self):
        # 批次号
        row1 = tk.Frame(self.panel)
        row1.pack(fill="x", pady=1)
        tk.Label(row1, text="批次号：", font=("Microsoft YaHei UI", 10)).pack(side="left")
        self.entry = tk.Entry(row1, font=("Microsoft YaHei UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.entry.bind("<Return>", lambda e: self.gen())
        self.entry.focus_set()

        # 显示大小 + 导出倍率
        row2 = tk.Frame(self.panel)
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="显示大小：").pack(side="left")
        ttk.Spinbox(row2, from_=2, to=30, width=4,
                    textvariable=self.display_var,
                    command=self.on_size_change).pack(side="left")
        tk.Label(row2, text="导出倍率：").pack(side="left", padx=(10, 0))
        ttk.Spinbox(row2, from_=4, to=40, width=4,
                    textvariable=self.scale_var).pack(side="left")

        # 置顶 + 全屏
        row3 = tk.Frame(self.panel)
        row3.pack(fill="x", pady=1)
        tk.Checkbutton(row3, text="置顶", variable=self.topmost_var,
                       command=self.apply_top).pack(side="left")
        tk.Checkbutton(row3, text="全屏", variable=self.fs_var,
                       command=self.apply_fs).pack(side="left", padx=8)

        # 按钮
        row4 = tk.Frame(self.panel)
        row4.pack(fill="x", pady=(2, 0))
        tk.Button(row4, text="生成二维码", command=self.gen,
                  width=10).pack(side="left")
        tk.Button(row4, text="保存图片", command=self.save,
                  width=10).pack(side="left", padx=6)
        tk.Button(row4, text="清空", command=self.clear,
                  width=8).pack(side="left")

        # 状态栏
        self.status = tk.Label(
            self.panel, text="请输入批次号", anchor="w",
            fg="#666", font=("", 9)
        )
        self.status.pack(fill="x", pady=(3, 0))

    # ---------- 收起/展开 ----------
    def toggle_panel(self):
        if self.expanded.get():
            self.panel.pack_forget()
            self.toggle_btn.config(text="▲")
            self.expanded.set(False)
        else:
            self.panel.pack(fill="x", padx=6, pady=4, side="bottom")
            self.toggle_btn.config(text="▼")
            self.expanded.set(True)
        self.after(10, self.fit_window)

    def on_size_change(self):
        self.draw()
        self.fit_window()

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
                text=f"{len(s)} 字符 | 版本 V{qr.version} | "
                     f"{len(self.modules)}×{len(self.modules)}"
            )
            self.fit_window()
        except Exception as e:
            messagebox.showerror("生成失败", str(e))

    # ---------- 绘制（精确大小，无多余留白） ----------
    def draw(self):
        self.canvas.delete("all")
        if not self.modules:
            self.canvas.config(width=120, height=120)
            return

        n = len(self.modules)
        total = n + 2 * self.quiet
        cell = max(2, int(self.display_var.get()))
        size = total * cell

        # Canvas 精确等于二维码像素，一分不多
        self.canvas.config(width=size, height=size)

        # 白底（与 Canvas 背景色一致，保险）
        self.canvas.create_rectangle(
            0, 0, size, size, fill="white", outline=""
        )
        # 黑块
        for r, row in enumerate(self.modules):
            for c, val in enumerate(row):
                if val:
                    x = (c + self.quiet) * cell
                    y = (r + self.quiet) * cell
                    self.canvas.create_rectangle(
                        x, y, x + cell, y + cell,
                        fill="black", outline=""
                    )

    # ---------- 窗口精确贴合内容 ----------
    def fit_window(self):
        self.update_idletasks()
        # 取窗口当前所有可见控件的推荐大小，无额外留白
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()

        # 保留当前窗口位置
        geo = self.geometry()
        pos = ""
        if "+" in geo:
            pos = "+" + geo.split("+", 1)[1]

        self.geometry(f"{w}x{h}{pos}")
        # 取消最小限制，允许完全贴合
        self.minsize(1, 1)

    # ---------- 保存 ----------
    def save(self):
        if not self.modules:
            return
        s = self.entry.get().strip() or "qr"
        safe = "".join(
            ch if ch.isalnum() or ch in "-_" else "_" for ch in s
        )[:60]
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
                                px[
                                    (c + self.quiet) * scale + dx,
                                    (r + self.quiet) * scale + dy,
                                ] = 0
            img.save(fn)
            self.status.config(text=f"已保存：{fn}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    # ---------- 清空 ----------
    def clear(self):
        self.entry.delete(0, "end")
        self.modules = None
        self.draw()
        self.status.config(text="已清空，请输入批次号。")
        self.fit_window()
        self.entry.focus_set()


if __name__ == "__main__":
    App().mainloop()
