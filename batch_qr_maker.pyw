# -*- coding: utf-8 -*-
"""
批次号二维码生成器
使用标准 qrcode 库，确保生成的二维码可被正常扫描。
目录模式打包命令：pyinstaller -w batch_qr_maker.pyw
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
        self.configure(bg="white")

        self.modules = None          # qrcode 二维布尔矩阵
        self.quiet = 4               # 静区模块数

        # 状态变量
        self.topmost_var = tk.BooleanVar(value=True)
        self.fs_var = tk.BooleanVar(value=False)
        self.scale_var = tk.IntVar(value=10)       # 导出倍率
        self.display_var = tk.IntVar(value=6)      # 显示模块像素
        self.expanded = tk.BooleanVar(value=True)  # 面板展开状态

        # ---------- Canvas（二维码画布） ----------
        self.canvas = tk.Canvas(
            self, bg="white", highlightthickness=0, bd=0
        )
        self.canvas.place(x=0, y=0)

        # 拖拽支持（无边框模式下按住二维码拖动）
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.on_drag)

        # ---------- 展开/收起按钮（白色融入背景） ----------
        self.toggle_btn = tk.Button(
            self, text="▼", width=1, command=self.toggle_panel,
            bg="white", relief="flat", font=("Arial", 7), cursor="hand2",
            highlightthickness=0, bd=0, padx=0, pady=0
        )

        # ---------- 控制面板 ----------
        self.panel = tk.Frame(self, padx=6, pady=4, bg=self.cget("bg"))
        self.build_panel()

        # 初始化
        self.draw()
        self.layout_and_fit()
        self.apply_top()

    # ---------- 构建面板 ----------
    def build_panel(self):
        row1 = tk.Frame(self.panel, bg=self.panel.cget("bg"))
        row1.pack(fill="x", pady=1)
        tk.Label(row1, text="批次号：", font=("Microsoft YaHei UI", 10),
                 bg=row1.cget("bg")).pack(side="left")
        self.entry = tk.Entry(row1, font=("Microsoft YaHei UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.entry.bind("<Return>", lambda e: self.gen())
        self.entry.focus_set()

        row2 = tk.Frame(self.panel, bg=self.panel.cget("bg"))
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="显示大小：", bg=row2.cget("bg")).pack(side="left")
        ttk.Spinbox(row2, from_=2, to=30, width=4,
                    textvariable=self.display_var,
                    command=self.on_size_change).pack(side="left")
        tk.Label(row2, text="导出倍率：", bg=row2.cget("bg")).pack(side="left", padx=(10, 0))
        ttk.Spinbox(row2, from_=4, to=40, width=4,
                    textvariable=self.scale_var).pack(side="left")

        row3 = tk.Frame(self.panel, bg=self.panel.cget("bg"))
        row3.pack(fill="x", pady=1)
        tk.Checkbutton(row3, text="置顶", variable=self.topmost_var,
                       command=self.apply_top, bg=row3.cget("bg")).pack(side="left")
        tk.Checkbutton(row3, text="全屏", variable=self.fs_var,
                       command=self.apply_fs, bg=row3.cget("bg")).pack(side="left", padx=8)

        row4 = tk.Frame(self.panel, bg=self.panel.cget("bg"))
        row4.pack(fill="x", pady=(2, 0))
        tk.Button(row4, text="生成二维码", command=self.gen,
                  width=10).pack(side="left")
        tk.Button(row4, text="保存图片", command=self.save,
                  width=10).pack(side="left", padx=6)
        tk.Button(row4, text="清空", command=self.clear,
                  width=8).pack(side="left")

        self.status = tk.Label(
            self.panel, text="请输入批次号", anchor="w",
            fg="#666", font=("", 9), bg=self.panel.cget("bg")
        )
        self.status.pack(fill="x", pady=(3, 0))

    # ---------- 收起/展开 ----------
    def toggle_panel(self):
        # 记录二维码当前屏幕位置，切换后恢复，防止跳动
        old_x = self.canvas.winfo_rootx()
        old_y = self.canvas.winfo_rooty()

        if self.expanded.get():
            self.panel.place_forget()
            self.overrideredirect(True)
            self.expanded.set(False)
            self.toggle_btn.config(text="▲")
        else:
            self.overrideredirect(False)
            self.expanded.set(True)
            self.toggle_btn.config(text="▼")

        self.after(30, lambda: self.restore_pos(old_x, old_y))

    def restore_pos(self, old_x, old_y):
        self.update_idletasks()
        new_x = self.canvas.winfo_rootx()
        new_y = self.canvas.winfo_rooty()
        dx = old_x - new_x
        dy = old_y - new_y
        if dx != 0 or dy != 0:
            self.geometry(f"+{self.winfo_x() + dx}+{self.winfo_y() + dy}")
        self.layout_and_fit()

    def on_size_change(self):
        self.draw()
        self.layout_and_fit()

    # ---------- 拖拽（无边框模式） ----------
    def start_drag(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def on_drag(self, event):
        self.geometry(
            f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}"
        )

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
            self.layout_and_fit()
        except Exception as e:
            messagebox.showerror("生成失败", str(e))

    # ---------- 绘制 ----------
    def draw(self):
        self.canvas.delete("all")
        if not self.modules:
            self.canvas.config(width=120, height=120)
            return

        n = len(self.modules)
        total = n + 2 * self.quiet
        cell = max(2, int(self.display_var.get()))
        size = total * cell

        self.canvas.config(width=size, height=size)

        # 白底
        self.canvas.create_rectangle(0, 0, size, size, fill="white", outline="")
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

    # ---------- 精确布局 + 锁定大小 ----------
    def layout_and_fit(self):
        self.update_idletasks()

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        bw = self.toggle_btn.winfo_reqwidth()
        bh = self.toggle_btn.winfo_reqheight()

        # Canvas 固定在 (0, 0)
        self.canvas.place(x=0, y=0)

        # 按钮往 Canvas 内偏移 4 像素，更紧贴二维码
        # 仍在静区范围内，不遮挡黑色模块
        offset = 4
        btn_x = max(0, cw - offset)
        btn_y = max(0, ch - offset)
        self.toggle_btn.place(x=btn_x, y=btn_y, anchor="nw")
        self.toggle_btn.lift()  # 强制置顶，永不消失

        if self.expanded.get():
            # 面板放在按钮下方
            panel_y = btn_y + bh
            self.panel.place(x=0, y=panel_y)
            self.panel.lift()
            pw = self.panel.winfo_reqwidth()
            ph = self.panel.winfo_reqheight()
            w = max(cw, pw)
            h = panel_y + ph
        else:
            self.panel.place_forget()
            w = max(cw, btn_x + bw)
            h = max(ch, btn_y + bh)

        # 保留当前屏幕位置
        geo = self.geometry()
        pos = ""
        if "+" in geo:
            pos = "+" + geo.split("+", 1)[1]

        self.geometry(f"{w}x{h}{pos}")
        # 完全锁定窗口大小，彻底杜绝用户拉大产生的白边
        self.minsize(w, h)
        self.maxsize(w, h)

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
        self.layout_and_fit()
        self.entry.focus_set()


if __name__ == "__main__":
    App().mainloop()
