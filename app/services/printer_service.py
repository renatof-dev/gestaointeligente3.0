from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import unicodedata

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


def normalize_receipt_text(text: str) -> str:
    replacements = {
        "—": "-",
        "–": "-",
        "−": "-",
        "…": "...",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "×": "x",
    }
    for source, replacement in replacements.items():
        text = text.replace(source, replacement)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(character for character in decomposed if not unicodedata.combining(character))


@dataclass
class PrintResult:
    ok: bool
    message: str


class PrinterService:
    def __init__(self) -> None:
        self._win32print = None
        self._try_import_win32print()

    def _try_import_win32print(self) -> None:
        try:
            import win32print  # type: ignore

            self._win32print = win32print
        except Exception:
            self._win32print = None

    def print_receipt_text(
        self,
        text: str,
        printer_name: str | None = None,
        logo_path: str | None = None,
        paper_type: str = "80mm",
    ) -> PrintResult:
        if not text.strip():
            return PrintResult(False, "Cupom vazio para impressao.")

        if not self._win32print:
            return PrintResult(
                False,
                "Modulo de impressao nao encontrado. Instale o pacote pywin32 no ambiente Python.",
            )

        try:
            win32print = self._win32print
            target_printer = printer_name or win32print.GetDefaultPrinter()
            if not target_printer:
                return PrintResult(False, "Nenhuma impressora padrao encontrada no Windows.")

            logo_data = self._logo_raster_data(logo_path, paper_type) if logo_path else b""
            normalized = normalize_receipt_text(text).replace("\n", "\r\n")
            text_data = normalized.encode("cp850", errors="replace")
            # Avanca o papel ate o rodape passar da cabeca de impressao e corta (GS V 66 n).
            feed_and_cut = b"\r\n" + b"\x1b\x64\x05" + b"\x1d\x56\x42\x00"
            data = (b"\x1b@" + logo_data if logo_data else b"") + text_data + feed_and_cut

            handle = win32print.OpenPrinter(target_printer)
            try:
                job = win32print.StartDocPrinter(
                    handle,
                    1,
                    ("Cupom Gestao Inteligente", None, "RAW"),
                )
                try:
                    win32print.StartPagePrinter(handle)
                    win32print.WritePrinter(handle, data)
                    win32print.EndPagePrinter(handle)
                finally:
                    win32print.EndDocPrinter(handle)
            finally:
                win32print.ClosePrinter(handle)

            return PrintResult(True, f"Cupom enviado para impressora: {target_printer}")
        except Exception as exc:
            return PrintResult(False, f"Falha na impressao: {exc}")

    @staticmethod
    def _logo_raster_data(logo_path: str | None, paper_type: str) -> bytes:
        if not logo_path or Image is None:
            return b""
        path = Path(logo_path)
        if not path.is_file():
            return b""
        try:
            max_width = 576 if "80" in paper_type else 384
            max_height = 160 if "80" in paper_type else 128
            with Image.open(path) as source:
                source = source.convert("RGBA")
                background = Image.new("RGBA", source.size, (255, 255, 255, 255))
                image = Image.alpha_composite(background, source).convert("L")
                scale = min(max_width / image.width, max_height / image.height, 1.0)
                if scale < 1.0:
                    target_size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
                    image = image.resize(target_size, Image.Resampling.LANCZOS)

                width_bytes = (image.width + 7) // 8
                padded_width = width_bytes * 8
                if padded_width != image.width:
                    padded = Image.new("L", (padded_width, image.height), 255)
                    padded.paste(image, (0, 0))
                    image = padded

                pixels = image.load()
                bitmap = bytearray()
                for y in range(image.height):
                    for byte_x in range(width_bytes):
                        value = 0
                        for bit in range(8):
                            if pixels[byte_x * 8 + bit, y] < 160:
                                value |= 1 << (7 - bit)
                        bitmap.append(value)

                width_low = width_bytes & 0xFF
                width_high = (width_bytes >> 8) & 0xFF
                height_low = image.height & 0xFF
                height_high = (image.height >> 8) & 0xFF
                raster_header = bytes((0x1D, 0x76, 0x30, 0x00, width_low, width_high, height_low, height_high))
                return b"\x1b\x61\x01" + raster_header + bytes(bitmap) + b"\n\x1b\x61\x00"
        except Exception:
            return b""
