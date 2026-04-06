import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import os

from totp_generator import generate_otp, get_time_remaining, validate_secret
from config_manager import save_config, load_config
from launcher_interact import enter_otp_and_login


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FFXIV OTP 自動登入")
        self.root.geometry("420x420")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self.secret = ""
        self.launcher_title = "FINAL FANTASY XIV 繁體中文版"
        self.launcher_path = r"C:\Program Files\USERJOY GAMES\FINAL FANTASY XIV TC\boot"
        self.delay = 0.3
        self.show_secret = False

        self._load_saved_config()
        self._build_ui()
        self._update_otp_display()

    def _load_saved_config(self):
        config = load_config()
        if config:
            self.secret = config["secret"]
            self.launcher_title = config["launcher_window_title"]
            self.launcher_path = config.get("launcher_path", "")
            self.delay = config["delay_before_type"]

    def _build_ui(self):
        # === Secret Section ===
        frame_secret = ttk.LabelFrame(self.root, text="TOTP 密鑰設定", padding=10)
        frame_secret.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(frame_secret, text="支援 Base32 密鑰或 otpauth:// 網址").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        self.secret_var = tk.StringVar(value=self.secret)
        self.entry_secret = ttk.Entry(frame_secret, textvariable=self.secret_var, width=30, show="*")
        self.entry_secret.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        self.btn_toggle = ttk.Button(frame_secret, text="顯示", width=5, command=self._toggle_secret)
        self.btn_toggle.grid(row=1, column=2, pady=(4, 0))

        frame_secret.columnconfigure(1, weight=1)

        ttk.Button(frame_secret, text="儲存設定", command=self._save_secret).grid(
            row=2, column=0, columnspan=3, pady=(8, 0)
        )

        # === OTP Display Section ===
        frame_otp = ttk.LabelFrame(self.root, text="目前驗證碼", padding=10)
        frame_otp.pack(fill="x", padx=10, pady=5)

        self.otp_var = tk.StringVar(value="------")
        ttk.Label(frame_otp, textvariable=self.otp_var, font=("Consolas", 28, "bold")).pack()

        self.time_var = tk.StringVar(value="")
        ttk.Label(frame_otp, textvariable=self.time_var, font=("", 10)).pack()

        btn_frame = ttk.Frame(frame_otp)
        btn_frame.pack(pady=(8, 0))
        ttk.Button(btn_frame, text="複製驗證碼", command=self._copy_otp).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="自動登入", command=self._auto_login).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="啟動遊戲", command=self._launch_game).pack(side="left", padx=5)

        # === Settings Section ===
        frame_settings = ttk.LabelFrame(self.root, text="進階設定", padding=10)
        frame_settings.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_settings, text="啟動器路徑:").grid(row=0, column=0, sticky="w")
        path_frame = ttk.Frame(frame_settings)
        path_frame.grid(row=0, column=1, sticky="ew", padx=5)
        self.path_var = tk.StringVar(value=self.launcher_path)
        ttk.Entry(path_frame, textvariable=self.path_var, width=22).pack(side="left", fill="x", expand=True)
        ttk.Button(path_frame, text="瀏覽", width=4, command=self._browse_launcher).pack(side="left", padx=(4, 0))

        ttk.Label(frame_settings, text="視窗標題:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.title_var = tk.StringVar(value=self.launcher_title)
        ttk.Entry(frame_settings, textvariable=self.title_var, width=30).grid(row=1, column=1, sticky="w", padx=5, pady=(4, 0))

        ttk.Label(frame_settings, text="延遲秒數:").grid(row=2, column=0, sticky="w", pady=(4, 0))
        self.delay_var = tk.DoubleVar(value=self.delay)
        ttk.Spinbox(frame_settings, from_=0.1, to=3.0, increment=0.1,
                     textvariable=self.delay_var, width=5).grid(
            row=2, column=1, sticky="w", padx=5, pady=(4, 0)
        )

        frame_settings.columnconfigure(1, weight=1)


    def _browse_launcher(self):
        current = self.path_var.get().strip()
        initial_dir = current if os.path.isdir(current) else os.path.dirname(current) if current else ""
        path = filedialog.askopenfilename(
            title="選擇 FFXIV 啟動器",
            initialdir=initial_dir or r"C:\Program Files\USERJOY GAMES\FINAL FANTASY XIV TC\boot",
            filetypes=[("執行檔", "*.exe"), ("所有檔案", "*.*")]
        )
        if path:
            self.path_var.set(path)

    def _launch_game(self):
        path = self.path_var.get().strip()
        if not path:
            self.time_var.set("請先設定啟動器路徑")
            return
        if not os.path.isfile(path):
            self.time_var.set("啟動器路徑不存在")
            return
        try:
            subprocess.Popen([path], cwd=os.path.dirname(path))
            self.time_var.set("啟動器已開啟")
        except Exception as e:
            self.time_var.set(f"啟動失敗: {e}")

    def _toggle_secret(self):
        self.show_secret = not self.show_secret
        self.entry_secret.config(show="" if self.show_secret else "*")
        self.btn_toggle.config(text="隱藏" if self.show_secret else "顯示")

    def _save_secret(self):
        secret = self.secret_var.get().strip()
        if not secret:
            messagebox.showwarning("警告", "請輸入 TOTP 密鑰")
            return
        if not validate_secret(secret):
            messagebox.showerror("錯誤", "無效的 Base32 密鑰，請確認格式正確")
            return

        self.secret = secret
        self.launcher_title = self.title_var.get().strip() or "FINAL FANTASY XIV 繁體中文版"
        self.launcher_path = self.path_var.get().strip()
        self.delay = self.delay_var.get()

        save_config(self.secret, self.launcher_title, self.delay, self.launcher_path)
        self.time_var.set("設定已儲存")

    def _update_otp_display(self):
        if self.secret and validate_secret(self.secret):
            otp = generate_otp(self.secret)
            self.otp_var.set(f"{otp[:3]} {otp[3:]}")
            remaining = get_time_remaining()
            self.time_var.set(f"剩餘 {remaining} 秒")
        else:
            self.otp_var.set("------")
            self.time_var.set("請先設定密鑰")

        self.root.after(1000, self._update_otp_display)

    def _copy_otp(self):
        if not self.secret:
            self.time_var.set("請先設定密鑰")
            return
        otp = generate_otp(self.secret)
        self.root.clipboard_clear()
        self.root.clipboard_append(otp)
        self.time_var.set(f"已複製驗證碼: {otp}")

    def _auto_login(self):
        if not self.secret:
            self.time_var.set("請先設定密鑰")
            return
        self._do_auto_login()

    def _do_auto_login(self):
        otp = generate_otp(self.secret)
        launcher_title = self.title_var.get().strip() or "FINAL FANTASY XIV 繁體中文版"
        delay = self.delay_var.get()

        self.time_var.set("正在自動登入...")

        def run():
            result = enter_otp_and_login(otp, launcher_title, delay=delay)
            self.root.after(0, lambda: self.time_var.set(result))

        threading.Thread(target=run, daemon=True).start()


def run():
    root = tk.Tk()
    App(root)
    root.mainloop()
