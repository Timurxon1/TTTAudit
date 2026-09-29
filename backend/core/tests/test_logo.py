from pathlib import Path

from PIL import Image

IMG = Path(__file__).resolve().parents[1] / "static" / "core" / "img"


def test_logo_files_exist_and_are_transparent():
    for name in ("logo-mark.png", "logo-full.png", "logo-full-white.png", "favicon-32.png", "apple-touch-icon.png", "brand-logo.png", "brand-mark.png"):
        im = Image.open(IMG / name)
        assert im.mode == "RGBA", name
        assert im.getpixel((0, 0))[3] == 0, f"{name}: burchak shaffof emas"


def test_logo_sizes():
    assert Image.open(IMG / "favicon-32.png").size == (32, 32)
    assert Image.open(IMG / "apple-touch-icon.png").size == (180, 180)
    assert Image.open(IMG / "og-image.png").size == (1200, 630)
    assert Image.open(IMG / "logo-mark.png").size == (512, 512)
    assert Image.open(IMG / "brand-logo.png").mode == "RGBA"
    assert Image.open(IMG / "brand-mark.png").mode == "RGBA"
