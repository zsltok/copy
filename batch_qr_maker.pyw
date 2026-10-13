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
        self.geometry("560x680")
        self.modules = None          # qrcode 生成的二维布尔矩阵
        self.box_size = 10           # 每个模块的显示像素
        self.quiet = 4               # 静区模块数

        # 状态变量
        self.topmost_var = tk.BooleanVar(value=True)
        self.fs_var = tk.BooleanVar(value=False)
        self.scale_var = tk.IntVar(value=10)

        # ---------- 输入区 ----------
        top = tk.Frame(self)
        top.pack(fill="x", padx=12, pady=10)
        tk.Label(top, text="批次号：", font=("Microsoft YaHei UI", 11)).pack(side="left")
        self.entry = tk.Entry(top, font=("Microsoft YaHei UI", 12))
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.gen())
        self.entry.focus_set()

        # ---------- 选项区 ----------
        opt = tk.Frame(self)
        opt.pack(fill="x", padx=12)
        tk.Checkbutton(opt, text="置顶", variable=self.topmost_var,
                       command=self.apply_top).pack(side="left")
        tk.Checkbutton(opt, text="全屏", variable=self.fs_var,
                       command=self.apply_fs).pack(side="left", padx=12)
        tk.Label(opt, text="导出倍率：").pack(side="left", padx=(20, 4))
        ttk.Spinbox(opt, from_=4, to=40, width=5, textvariable=self.scale_var).pack(side="left")

        # ---------- 按钮区 ----------
        btns = tk.Frame(self)
        btns.pack(fill="x", padx=12, pady=8)
        tk.Button(btns, text="生成二维码", command=self.gen,
                  width=12).pack(side="left")
        tk.Button(btns, text="保存图片", command=self.save,
                  width=12).pack(side="left", padx=10)
        tk.Button(btns, text="清空", command=self.clear,
                  width=8).pack(side="left")

        # ---------- 画布 ----------
        self.canvas = tk.Canvas(self, bg="white", highlightthickness=1,
                                highlightbackground="#999")
        self.canvas.pack(fill="both", expand=True, padx=12, pady=10)

        # ---------- 状态栏 ----------
        self.status = tk.Label(self, text="输入批次号后按回车或点击生成；默认窗口置顶。",
                               anchor="w")
        self.status.pack(fill="x", padx=12, pady=(0, 8))

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
                version=None,                       # 自动选择版本
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=1,                         # 后面自己画，这里设为 1
                border=self.quiet,
            )
            qr.add_data(s)
            qr.make(fit=True)
            self.modules = qr.modules               # 二维布尔列表
            self.draw()
            self.status.config(
                text=f"已生成：{len(s)} 个字符，版本 V{qr.version}，"
                     f"矩阵 {len(self.modules)}×{len(self.modules)}"
            )
        except Exception as e:
            messagebox.showerror("生成失败", str(e))

    # ---------- 绘制 ----------
    def draw(self):
        self.canvas.delete("all")
        if not self.modules:
            return
        self.update_idletasks()
        cw = max(self.canvas.winfo_width(), 200)
        ch = max(self.canvas.winfo_height(), 200)

        n = len(self.modules)
        total = n + 2 * self.quiet
        cell = max(1, min(cw, ch) // total)
        ox = (cw - cell * total) // 2
        oy = (ch - cell * total) // 2

        # 白底
        self.canvas.create_rectangle(ox, oy, ox + cell * total,
                                     oy + cell * total, fill="white", outline="")
        # 画黑块
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
            scale = int(self.scale_var.get())
            n = len(self.modules)
            total_px = (n + 2 * self.quiet) * scale
            img = Image.new("1", (total_px, total_px), 1)   # 1-bit, 白底
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
