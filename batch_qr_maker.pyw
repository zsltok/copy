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
        self.geometry("320x420")

        self.modules = None          # qrcode 二维布尔矩阵
        self.quiet = 4               # 静区模块数

        # 状态变量
        self.topmost_var = tk.BooleanVar(value=True)
        self.fs_var = tk.BooleanVar(value=False)
        self.scale_var = tk.IntVar(value=10)       # 导出倍率
        self.display_var = tk.IntVar(value=6)      # 显示模块像素
        self.expanded = tk.BooleanVar(value=True)  # 面板展开状态

        # ---------- 主容器 ----------
        main = tk.Frame(self)
        main.pack(fill="both", expand=True)

        # ---------- 二维码区域（白底，可扩展） ----------
        self.qr_area = tk.Frame(main, bg="white", highlightthickness=1,
                                highlightbackground="#ccc")
        self.qr_area.pack(fill="both", expand=True)

        # Canvas 固定大小，始终居中
        self.canvas = tk.Canvas(self.qr_area, bg="white", highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")

        # 收起/展开按钮（右下角）
        self.toggle_btn = tk.Button(
            self.qr_area, text="▼", width=2, command=self.toggle_panel,
            bg="white", relief="flat", font=("Arial", 9), cursor="hand2"
        )
        self.toggle_btn.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)

        # ---------- 控制面板（下方） ----------
        self.panel = tk.Frame(main, padx=8, pady=5)
        self.build_panel()
        self.panel.pack(fill="x", side="bottom")

        # 初始化
        self.draw()
        self.fit_window()
        self.apply_top()

    # ---------- 构建面板 ----------
    def build_panel(self):
        # 批次号
        row1 = tk.Frame(self.panel)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="批次号：", font=("Microsoft YaHei UI", 10)).pack(side="left")
        self.entry = tk.Entry(row1, font=("Microsoft YaHei UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.entry.bind("<Return>", lambda e: self.gen())
        self.entry.focus_set()

        # 显示大小 + 导出倍率
        row2 = tk.Frame(self.panel)
        row2.pack(fill="x", pady=3)
        tk.Label(row2, text="显示大小：").pack(side="left")
        ttk.Spinbox(row2, from_=2, to=30, width=4,
                    textvariable=self.display_var,
                    command=self.on_size_change).pack(side="left")
        tk.Label(row2, text="导出倍率：").pack(side="left", padx=(12, 0))
        ttk.Spinbox(row2, from_=4, to=40, width=4,
                    textvariable=self.scale_var).pack(side="left")

        # 置顶 + 全屏
        row3 = tk.Frame(self.panel)
        row3.pack(fill="x", pady=2)
        tk.Checkbutton(row3, text="置顶", variable=self.topmost_var,
                       command=self.apply_top).pack(side="left")
        tk.Checkbutton(row3, text="全屏", variable=self.fs_var,
                       command=self.apply_fs).pack(side="left", padx=10)

        # 按钮
        row4 = tk.Frame(self.panel)
        row4.pack(fill="x", pady=(3, 0))
        tk.Button(row4, text="生成二维码", command=self.gen,
                  width=10).pack(side="left")
        tk.Button(row4, text="保存图片", command=self.save,
                  width=10).pack(side="left", padx=6)
        tk.Button(row4, text="清空", command=self.clear,
                  width=8).pack(side="left")

        # 状态栏
        self.status = tk.Label(self.panel, text="请输入批次号", anchor="w",
                               fg="#666", font=("", 9))
        self.status.pack(fill="x", pady=(4, 0))

    # ---------- 收起/展开 ----------
    def toggle_panel(self):
        if self.expanded.get():
            self.panel.pack_forget()
            self.toggle_btn.config(text="▲")
            self.expanded.set(False)
        else:
            self.panel.pack(fill="x", side="bottom", padx=8, pady=5)
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

    # ---------- 绘制 ----------
    def draw(self):
        self.canvas.delete("all")
        if not self.modules:
            self.canvas.config(width=200, height=200)
            return

        n = len(self.modules)
        total = n + 2 * self.quiet
        cell = max(2, int(self.display_var.get()))
        size = total * cell

        self.canvas.config(width=size, height=size)

        # 白底
        self.canvas.create_rectangle(0, 0, size, size,
                                     fill="white", outline="")
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

    # ---------- 窗口自适应 ----------
    def fit_window(self):
        self.update_idletasks()

        qr_size = self.canvas.winfo_reqwidth()
        panel_h = self.panel.winfo_reqheight() if self.expanded.get() else 0

        # 边框 + 缓冲
        hl = int(self.qr_area.cget("highlightthickness"))
        extra_w = hl * 2 + 4
        extra_h = hl * 2 + 4 + panel_h

        # 最小宽度保证面板能放下
        total_w = max(qr_size + extra_w, 240)
        total_h = qr_size + extra_h

        # 保持当前窗口位置
        geo = self.geometry()
        pos = ""
        if "+" in geo:
            pos = "+" + geo.split("+", 1)[1]

        self.geometry(f"{total_w}x{total_h}{pos}")
        self.minsize(total_w, total_h)

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
