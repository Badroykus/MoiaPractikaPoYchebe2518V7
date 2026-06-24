""" Модуль обработки изображений """

from __future__ import annotations

from typing import Literal

from PIL import Image, ImageDraw, ImageOps

ChannelName = Literal["red", "green", "blue"]

SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg")


def load_image(path: str) -> Image.Image:
    """Загружает изображение формата PNG или JPG."""
    lower_path = path.lower()
    if not lower_path.endswith(SUPPORTED_EXTENSIONS):
        raise ValueError(
            "Неподдерживаемый формат файла. Допустимы только PNG и JPG."
        )

    try:
        image = Image.open(path)
        image.load()
    except OSError as exc:
        raise ValueError(f"Не удалось открыть изображение: {exc}") from exc

    if image.format not in ("PNG", "JPEG", "JPG"):
        raise ValueError(
            f"Неподдерживаемый формат: {image.format}. Допустимы только PNG и JPG."
        )

    return image.convert("RGB")


def extract_channel(image: Image.Image, channel: ChannelName) -> Image.Image:
    """Возвращает изображение с одним выбранным цветовым каналом."""
    r, g, b = image.split()
    zero = Image.new("L", image.size, 0)

    if channel == "red":
        return Image.merge("RGB", (r, zero, zero))
    if channel == "green":
        return Image.merge("RGB", (zero, g, zero))
    return Image.merge("RGB", (zero, zero, b))


def negative_image(image: Image.Image) -> Image.Image:
    """Возвращает негатив изображения."""
    return ImageOps.invert(image)


def rotate_image(image: Image.Image, angle: float) -> Image.Image:
    """Поворачивает изображение на заданный угол (в градусах)."""
    return image.rotate(angle, expand=True, fillcolor=(255, 255, 255))


def draw_red_circle(
    image: Image.Image,
    center_x: int,
    center_y: int,
    radius: int,
) -> Image.Image:
    """Рисует красный круг на копии изображения."""
    if radius <= 0:
        raise ValueError("Радиус круга должен быть положительным числом.")

    width, height = image.size
    if not (0 <= center_x < width and 0 <= center_y < height):
        raise ValueError(
            f"Координаты центра ({center_x}, {center_y}) выходят за границы "
            f"изображения ({width} x {height})."
        )

    result = image.copy()
    draw = ImageDraw.Draw(result)
    bbox = (
        center_x - radius,
        center_y - radius,
        center_x + radius,
        center_y + radius,
    )
    draw.ellipse(bbox, outline=(255, 0, 0), width=3)
    return result
