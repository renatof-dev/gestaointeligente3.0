from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from app.config import DATA_DIR

# Bases abertas e gratuitas (mesma API): alimentos, higiene/beleza e produtos em geral.
_SOURCES = (
    "https://world.openfoodfacts.org",
    "https://world.openbeautyfacts.org",
    "https://world.openproductsfacts.org",
)
_USER_AGENT = "GestaoInteligente/3.0 (PDV; contato local)"
_TIMEOUT = 8
_MAX_IMAGE_BYTES = 5 * 1024 * 1024
PRODUCT_IMAGES_DIR = DATA_DIR / "product_images"


@dataclass
class ProductLookupResult:
    found: bool
    name: str = ""
    brand: str = ""
    image_path: str = ""
    message: str = ""


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
        data = response.read(_MAX_IMAGE_BYTES + 1)
    if len(data) > _MAX_IMAGE_BYTES:
        raise ValueError("Imagem muito grande.")
    return data


def _image_candidates(base: str, code: str, product: dict) -> list[str]:
    urls: list[str] = []
    for key in ("image_front_url", "image_url", "image_front_small_url", "image_small_url"):
        if product.get(key):
            urls.append(product[key])
    # Fallback: monta a URL a partir do cadastro de imagens quando os campos prontos vêm vazios.
    images = product.get("images") or {}
    padded = code.zfill(13)
    folder = f"{padded[0:3]}/{padded[3:6]}/{padded[6:9]}/{padded[9:]}"
    for key, info in images.items():
        if not isinstance(info, dict):
            continue
        rev = info.get("rev")
        if key.startswith("front") and rev:
            urls.append(f"https://images.openfoodfacts.org/images/products/{folder}/{key}.{rev}.400.jpg")
        elif key.isdigit() and info.get("sizes"):
            urls.append(f"https://images.openfoodfacts.org/images/products/{folder}/{key}.400.jpg")
    return urls


def _download_image(code: str, urls: list[str]) -> str:
    for url in dict.fromkeys(urls):
        try:
            data = _get(url)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            continue
        if len(data) < 500:
            continue
        PRODUCT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        suffix = Path(url.split("?")[0]).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".jpg"
        target = PRODUCT_IMAGES_DIR / f"{code}{suffix}"
        target.write_bytes(data)
        return str(target)
    return ""


def lookup_product_by_barcode(barcode: str) -> ProductLookupResult:
    """Busca nome e foto do produto pelo codigo de barras e salva a imagem localmente."""
    code = re.sub(r"\D", "", barcode or "")
    if len(code) < 8:
        return ProductLookupResult(False, message="Informe um código de barras válido (EAN com 8 a 14 dígitos).")

    network_error = False
    name = brand = ""
    for base in _SOURCES:
        url = f"{base}/api/v2/product/{code}.json?fields=product_name,product_name_pt,brands,image_front_url,image_url,image_front_small_url,image_small_url,images"
        try:
            payload = json.loads(_get(url).decode("utf-8"))
        except urllib.error.HTTPError:
            continue
        except (urllib.error.URLError, TimeoutError, OSError):
            network_error = True
            continue
        except ValueError:
            continue
        product = payload.get("product") if payload.get("status") == 1 else None
        if not product:
            continue
        name = name or (product.get("product_name_pt") or product.get("product_name") or "").strip()
        brand = brand or (product.get("brands") or "").split(",")[0].strip()
        image_path = _download_image(code, _image_candidates(base, code, product))
        if image_path:
            return ProductLookupResult(True, name, brand, image_path)

    if name:
        return ProductLookupResult(True, name, brand, "", "Produto encontrado, mas sem foto nas bases públicas. Escolha a foto manualmente.")
    if network_error:
        return ProductLookupResult(False, message="Sem conexão com a internet. Tente novamente quando estiver online.")
    return ProductLookupResult(False, message="Produto não encontrado nas bases públicas. Escolha a foto manualmente.")