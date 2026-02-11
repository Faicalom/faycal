import os
import queue
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, W, filedialog, messagebox, ttk
import tkinter as tk


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
DEFAULT_EXE = r"D:\Real-ESRGAN-master\realesrgan-ncnn-vulkan.exe"
DEFAULT_MODELS_DIR = r"D:\Real-ESRGAN-master\models"
DEFAULT_INPUT_DIR = r"D:\Real-ESRGAN-master\يدوي\input"
DEFAULT_OUTPUT_DIR = r"D:\Real-ESRGAN-master\يدوي\results"
MODELS = ("realesrgan-x4plus", "realesrgan-x4plus-anime")
SCALES = ("Auto", "2", "4")


@dataclass
class AppConfig:
    exe_path: Path
    models_dir: Path
    input_path: Path
    output_dir: Path
    model_name: str
    scale_value: str


class RealESRGANGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Real-ESRGAN Batch GUI")
        self.root.geometry("900x620")

        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.stop_event = threading.Event()

        self._build_ui()
        self._poll_logs()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=BOTH, expand=True)

        self.exe_var = tk.StringVar(value=DEFAULT_EXE)
        self.models_var = tk.StringVar(value=DEFAULT_MODELS_DIR)
        self.input_var = tk.StringVar(value=DEFAULT_INPUT_DIR)
        self.output_var = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        self.model_var = tk.StringVar(value=MODELS[0])
        self.scale_var = tk.StringVar(value=SCALES[0])

        self._path_row(frame, 0, "Real-ESRGAN EXE", self.exe_var, self._choose_exe)
        self._path_row(frame, 1, "Models folder", self.models_var, self._choose_models_dir)
        self._path_row(frame, 2, "Input (image/folder)", self.input_var, self._choose_input)
        self._path_row(frame, 3, "Output folder", self.output_var, self._choose_output)

        model_label = ttk.Label(frame, text="Model")
        model_label.grid(row=4, column=0, sticky=W, pady=(8, 4))
        model_combo = ttk.Combobox(frame, textvariable=self.model_var, values=MODELS, state="readonly")
        model_combo.grid(row=4, column=1, sticky="ew", pady=(8, 4), padx=(8, 0))

        scale_label = ttk.Label(frame, text="Scale")
        scale_label.grid(row=4, column=2, sticky=W, pady=(8, 4), padx=(16, 0))
        scale_combo = ttk.Combobox(frame, textvariable=self.scale_var, values=SCALES, state="readonly", width=10)
        scale_combo.grid(row=4, column=3, sticky=W, pady=(8, 4), padx=(8, 0))

        progress_frame = ttk.Frame(frame)
        progress_frame.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(12, 8))
        progress_frame.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(progress_frame, mode="determinate", maximum=100)
        self.progress.grid(row=0, column=0, sticky="ew")

        self.progress_label = ttk.Label(progress_frame, text="جاهز")
        self.progress_label.grid(row=1, column=0, sticky=W, pady=(4, 0))

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(4, 10))

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_processing)
        self.start_button.pack(side=LEFT)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_processing, state="disabled")
        self.stop_button.pack(side=LEFT, padx=(8, 0))

        clear_button = ttk.Button(button_frame, text="Clear Log", command=self._clear_log)
        clear_button.pack(side=RIGHT)

        log_label = ttk.Label(frame, text="Log")
        log_label.grid(row=7, column=0, sticky=W)

        self.log_text = tk.Text(frame, height=18, wrap="word")
        self.log_text.grid(row=8, column=0, columnspan=4, sticky="nsew", pady=(4, 0))

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=8, column=4, sticky="ns", pady=(4, 0))
        self.log_text.configure(yscrollcommand=scrollbar.set)

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)
        frame.rowconfigure(8, weight=1)

    def _path_row(self, parent: ttk.Frame, row: int, title: str, variable: tk.StringVar, callback) -> None:
        label = ttk.Label(parent, text=title)
        label.grid(row=row, column=0, sticky=W, pady=4)

        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(8, 8), pady=4)

        button = ttk.Button(parent, text="Browse", command=callback)
        button.grid(row=row, column=3, sticky="ew", pady=4)

    def _choose_exe(self) -> None:
        path = filedialog.askopenfilename(title="Choose realesrgan-ncnn-vulkan.exe", filetypes=[("Executable", "*.exe")])
        if path:
            self.exe_var.set(path)

    def _choose_models_dir(self) -> None:
        path = filedialog.askdirectory(title="Choose models folder")
        if path:
            self.models_var.set(path)

    def _choose_input(self) -> None:
        choice = messagebox.askyesno("Input", "اختيار مجلد؟\nYes = Folder, No = Single image")
        if choice:
            path = filedialog.askdirectory(title="Choose input folder")
        else:
            path = filedialog.askopenfilename(title="Choose input image", filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tif *.tiff")])
        if path:
            self.input_var.set(path)

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(title="Choose output folder")
        if path:
            self.output_var.set(path)

    def _clear_log(self) -> None:
        self.log_text.delete("1.0", END)

    def _log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")

    def _poll_logs(self) -> None:
        while not self.log_queue.empty():
            line = self.log_queue.get_nowait()
            self.log_text.insert(END, line + "\n")
            self.log_text.see(END)
        self.root.after(120, self._poll_logs)

    def _collect_images(self, input_path: Path) -> list[Path]:
        if input_path.is_file():
            return [input_path] if input_path.suffix.lower() in IMAGE_EXTENSIONS else []

        images = []
        for item in sorted(input_path.iterdir()):
            if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
                images.append(item)
        return images

    def _supports_scale_arg(self, exe_path: Path) -> bool:
        try:
            result = subprocess.run(
                [str(exe_path), "-h"],
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="ignore",
            )
            help_text = (result.stdout or "") + "\n" + (result.stderr or "")
            return "-s" in help_text
        except OSError:
            return False

    def _validate(self) -> AppConfig | None:
        exe_path = Path(self.exe_var.get().strip())
        models_dir = Path(self.models_var.get().strip())
        input_path = Path(self.input_var.get().strip())
        output_dir = Path(self.output_var.get().strip())

        if not exe_path.exists() or not exe_path.is_file():
            messagebox.showerror("Error", "مسار ملف exe غير صحيح")
            return None

        if not input_path.exists():
            messagebox.showerror("Error", "مسار الإدخال غير موجود")
            return None

        if not models_dir.exists():
            self._log("تنبيه: مجلد models غير موجود. سيتم تشغيل الأداة بدون -m.")

        output_dir.mkdir(parents=True, exist_ok=True)

        return AppConfig(
            exe_path=exe_path,
            models_dir=models_dir,
            input_path=input_path,
            output_dir=output_dir,
            model_name=self.model_var.get(),
            scale_value=self.scale_var.get(),
        )

    def start_processing(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("Info", "المعالجة تعمل حالياً")
            return

        config = self._validate()
        if config is None:
            return

        self.stop_event.clear()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.progress.configure(value=0)
        self.progress_label.configure(text="جارٍ التحضير...")

        self.worker_thread = threading.Thread(target=self._process_images, args=(config,), daemon=True)
        self.worker_thread.start()

    def stop_processing(self) -> None:
        self.stop_event.set()
        self._log("تم طلب الإيقاف من المستخدم.")

    def _set_ui_idle(self) -> None:
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def _process_images(self, config: AppConfig) -> None:
        log_path = config.output_dir / "log.txt"
        images = self._collect_images(config.input_path)

        if not images:
            self._log("لم يتم العثور على صور للمعالجة.")
            self.progress_label.configure(text="لا توجد صور")
            self._set_ui_idle()
            return

        scale_supported = self._supports_scale_arg(config.exe_path)
        if config.scale_value != "Auto" and not scale_supported:
            self._log("خيار -s غير مدعوم في هذا الإصدار. سيتم استخدام Scale الافتراضي للموديل.")

        total = len(images)
        success = 0

        with log_path.open("a", encoding="utf-8") as file_log:
            file_log.write("\n" + "=" * 70 + "\n")
            file_log.write(f"Run at: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            file_log.write(f"Model: {config.model_name} | Scale: {config.scale_value}\n")
            file_log.write(f"Input: {config.input_path}\nOutput: {config.output_dir}\n")

            for idx, source in enumerate(images, start=1):
                if self.stop_event.is_set():
                    self._log("تم إيقاف العملية.")
                    break

                target = config.output_dir / f"{source.stem}_upscaled{source.suffix}"
                cmd = [
                    str(config.exe_path),
                    "-i",
                    str(source),
                    "-o",
                    str(target),
                    "-n",
                    config.model_name,
                ]

                if config.models_dir.exists():
                    cmd.extend(["-m", str(config.models_dir)])

                if config.scale_value != "Auto" and scale_supported:
                    cmd.extend(["-s", config.scale_value])

                self._log(f"[{idx}/{total}] Processing: {source.name}")
                file_log.write(f"\n[{idx}/{total}] INPUT: {source}\n")
                file_log.write("CMD: " + " ".join(cmd) + "\n")

                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                        encoding="utf-8",
                        errors="ignore",
                    )
                except OSError as exc:
                    stderr = str(exc)
                    result_code = -1
                else:
                    stderr = result.stderr.strip()
                    result_code = result.returncode

                if result_code == 0:
                    success += 1
                    self._log(f"✅ Done: {target.name}")
                    file_log.write("STATUS: SUCCESS\n")
                else:
                    self._log(f"❌ Failed: {source.name}")
                    if stderr:
                        self._log(f"   {stderr}")
                    file_log.write("STATUS: FAILED\n")
                    if stderr:
                        file_log.write("ERROR: " + stderr + "\n")

                progress_value = int((idx / total) * 100)
                self.progress.configure(value=progress_value)
                self.progress_label.configure(text=f"{idx}/{total} processed")

            file_log.write(f"\nSummary: {success}/{total} succeeded\n")

        self._log(f"انتهت المعالجة: {success}/{total} نجاح")
        self.progress_label.configure(text=f"Finished: {success}/{total}")
        self._set_ui_idle()


def main() -> None:
    root = tk.Tk()
    app = RealESRGANGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
