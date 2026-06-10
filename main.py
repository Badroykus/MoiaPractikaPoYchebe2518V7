"""Десктоп-приложение для обработки изображений (практика, вариант 7)."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import cv2
from PIL import Image, ImageTk

from image_processor import (
    SUPPORTED_EXTENSIONS,
    draw_red_circle,
    extract_channel,
    load_image,
    negative_image,
    rotate_image,
)

WEBCAM_TROUBLESHOOTING = (
    "Не удалось подключиться к веб-камере.\n\n"
    "Возможные решения:\n"
    "1. Убедитесь, что веб-камера подключена и распознана системой.\n"
    "2. Закройте другие программы, использующие камеру (Zoom, Skype и т.д.).\n"
    "3. Проверьте разрешения на доступ к камере в настройках Windows.\n"
    "4. Переподключите USB-камеру или перезагрузите компьютер.\n"
    "5. Обновите драйверы камеры в «Диспетчере устройств».\n"
    "6. Попробуйте другой индекс камеры (0, 1, 2) в коде приложения."
)


class ImageApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Обработка изображений — вариант 7")
        self.geometry("900x700")
        self.minsize(640, 480)

        self._original_image: Image.Image | None = None
        self._current_image: Image.Image | None = None
        self._photo: ImageTk.PhotoImage | None = None

        self._build_menu()
        self._build_ui()
        self._set_status("Готово. Загрузите изображение или сделайте снимок с веб-камеры.")

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Загрузить изображение...", command=self._load_from_file)
        file_menu.add_command(label="Снимок с веб-камеры", command=self._capture_from_webcam)
        file_menu.add_separator()
        file_menu.add_command(label="Показать оригинал", command=self._show_original)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.destroy)
        menubar.add_cascade(label="Файл", menu=file_menu)

        channel_menu = tk.Menu(menubar, tearoff=0)
        channel_menu.add_command(label="Красный канал", command=lambda: self._show_channel("red"))
        channel_menu.add_command(label="Зелёный канал", command=lambda: self._show_channel("green"))
        channel_menu.add_command(label="Синий канал", command=lambda: self._show_channel("blue"))
        menubar.add_cascade(label="Каналы", menu=channel_menu)

        extra_menu = tk.Menu(menubar, tearoff=0)
        extra_menu.add_command(label="Негативное изображение", command=self._show_negative)
        extra_menu.add_command(label="Вращение изображения...", command=self._rotate_dialog)
        extra_menu.add_command(label="Нарисовать круг...", command=self._circle_dialog)
        menubar.add_cascade(label="Обработка", menu=extra_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self._show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.config(menu=menubar)

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self, padding=8)
        main_frame.pack(fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(toolbar, text="Загрузить", command=self._load_from_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Веб-камера", command=self._capture_from_webcam).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Оригинал", command=self._show_original).pack(side=tk.LEFT, padx=4)

        self._canvas = tk.Canvas(main_frame, bg="#2b2b2b", highlightthickness=1, highlightbackground="#555")
        self._canvas.pack(fill=tk.BOTH, expand=True)

        self._status_var = tk.StringVar()
        status_bar = ttk.Label(main_frame, textvariable=self._status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(8, 0))

    def _set_status(self, message: str) -> None:
        self._status_var.set(message)
        self.update_idletasks()

    def _require_image(self) -> Image.Image | None:
        if self._original_image is None:
            messagebox.showwarning(
                "Нет изображения",
                "Сначала загрузите изображение или сделайте снимок с веб-камеры.",
            )
            self._set_status("Ошибка: изображение не загружено.")
            return None
        return self._original_image

    def _set_image(self, image: Image.Image, status: str) -> None:
        self._current_image = image
        self._display_image(image)
        self._set_status(status)

    def _display_image(self, image: Image.Image) -> None:
        canvas_width = max(self._canvas.winfo_width(), 1)
        canvas_height = max(self._canvas.winfo_height(), 1)

        img_copy = image.copy()
        img_copy.thumbnail((canvas_width - 4, canvas_height - 4), Image.Resampling.LANCZOS)

        self._photo = ImageTk.PhotoImage(img_copy)
        self._canvas.delete("all")
        self._canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=self._photo,
            anchor=tk.CENTER,
        )

    def _load_from_file(self) -> None:
        filetypes = [
            ("Изображения PNG/JPG", "*.png *.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("Все файлы", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Выберите изображение", filetypes=filetypes)
        if not path:
            self._set_status("Загрузка отменена пользователем.")
            return

        try:
            image = load_image(path)
        except ValueError as exc:
            messagebox.showerror("Ошибка загрузки", str(exc))
            self._set_status(f"Ошибка загрузки: {exc}")
            return

        self._original_image = image
        self._set_image(image, f"Изображение загружено: {path} ({image.size[0]}x{image.size[1]})")

    def _capture_from_webcam(self) -> None:
        self._set_status("Подключение к веб-камере...")
        self.update_idletasks()

        cap = None
        for index in (0, 1, 2):
            candidate = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if candidate.isOpened():
                cap = candidate
                break
            candidate.release()

        if cap is None or not cap.isOpened():
            messagebox.showerror("Ошибка веб-камеры", WEBCAM_TROUBLESHOOTING)
            self._set_status("Ошибка: не удалось подключиться к веб-камере.")
            return

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            messagebox.showerror("Ошибка веб-камеры", WEBCAM_TROUBLESHOOTING)
            self._set_status("Ошибка: не удалось получить кадр с веб-камеры.")
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        self._original_image = image
        self._set_image(image, f"Снимок с веб-камеры получен ({image.size[0]}x{image.size[1]})")

    def _show_original(self) -> None:
        if self._require_image() is None:
            return
        self._set_image(self._original_image, "Отображён оригинал изображения.")

    def _show_channel(self, channel: str) -> None:
        source = self._require_image()
        if source is None:
            return

        names = {"red": "красный", "green": "зелёный", "blue": "синий"}
        try:
            result = extract_channel(source, channel)  # type: ignore[arg-type]
        except Exception as exc:
            messagebox.showerror("Ошибка", str(exc))
            self._set_status(f"Ошибка при выделении канала: {exc}")
            return

        self._set_image(result, f"Отображён {names[channel]} канал.")

    def _show_negative(self) -> None:
        source = self._require_image()
        if source is None:
            return

        result = negative_image(source)
        self._set_image(result, "Отображено негативное изображение.")

    def _rotate_dialog(self) -> None:
        if self._require_image() is None:
            return

        angle_str = simpledialog.askstring(
            "Вращение изображения",
            "Введите угол поворота в градусах\n(положительный — против часовой стрелки):",
            parent=self,
        )
        if angle_str is None:
            self._set_status("Вращение отменено пользователем.")
            return

        try:
            angle = float(angle_str.replace(",", "."))
        except ValueError:
            messagebox.showerror("Некорректный ввод", "Угол должен быть числом.")
            self._set_status("Ошибка: некорректное значение угла.")
            return

        result = rotate_image(self._original_image, angle)
        self._set_image(result, f"Изображение повёрнуто на {angle}°.")

    def _circle_dialog(self) -> None:
        source = self._require_image()
        if source is None:
            return

        x_str = simpledialog.askstring("Круг", "Координата X центра круга:", parent=self)
        if x_str is None:
            self._set_status("Рисование круга отменено.")
            return

        y_str = simpledialog.askstring("Круг", "Координата Y центра круга:", parent=self)
        if y_str is None:
            self._set_status("Рисование круга отменено.")
            return

        r_str = simpledialog.askstring("Круг", "Радиус круга:", parent=self)
        if r_str is None:
            self._set_status("Рисование круга отменено.")
            return

        try:
            center_x = int(x_str)
            center_y = int(y_str)
            radius = int(r_str)
        except ValueError:
            messagebox.showerror(
                "Некорректный ввод",
                "Координаты и радиус должны быть целыми числами.",
            )
            self._set_status("Ошибка: некорректные координаты или радиус.")
            return

        try:
            result = draw_red_circle(source, center_x, center_y, radius)
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc))
            self._set_status(f"Ошибка при рисовании круга: {exc}")
            return

        self._set_image(result, f"Красный круг нарисован: центр ({center_x}, {center_y}), радиус {radius}.")

    def _show_about(self) -> None:
        messagebox.showinfo(
            "О программе",
            "Приложение для обработки изображений\n"
            "Практическое задание, вариант 7\n\n"
            f"Поддерживаемые форматы: {', '.join(SUPPORTED_EXTENSIONS)}",
        )
        self._set_status("Открыта справка «О программе».")


def main() -> None:
    app = ImageApp()
    app.mainloop()


if __name__ == "__main__":
    main()
