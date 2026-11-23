
from pathlib import Path

import pymupdf


Raiz = Path(__file__).resolve().parents[2]
CarpetaPdfs = Raiz / "Data" / "Pdfs"

Archivo = CarpetaPdfs / (
    "eng_08-06_warhammer40000_faction_pack_space-marines"
    "-nd2ezs5yzn-wxe2nf2ckk.pdf"
)

Reporte = Path(__file__).with_name("PdfColumnasSpaceMarinesReporte.txt")


def ExtraerRegiones(Pagina):
    """Extrae encabezado y columnas por separado."""

    Ancho = Pagina.rect.width
    Alto = Pagina.rect.height
    Mitad = Ancho / 2

    # El límite 215 corresponde únicamente al diseño
    # observado en la página 3 de Black Templars.
    LimiteEncabezado = 215

    RegionEncabezado = pymupdf.Rect(
        0, 0, Ancho, LimiteEncabezado
    )

    RegionIzquierda = pymupdf.Rect(
        0, LimiteEncabezado, Mitad, Alto
    )

    RegionDerecha = pymupdf.Rect(
        Mitad, LimiteEncabezado, Ancho, Alto
    )

    Encabezado = Pagina.get_text(
        "text", clip=RegionEncabezado, sort=False
    )

    Izquierda = Pagina.get_text(
        "text", clip=RegionIzquierda, sort=False
    )

    Derecha = Pagina.get_text(
        "text", clip=RegionDerecha, sort=False
    )

    return Encabezado, Izquierda, Derecha


def Principal():
    with pymupdf.open(Archivo) as Documento:
        Pagina = Documento[1]

        Encabezado, Izquierda, Derecha = (
            ExtraerRegiones(Pagina)
        )

    Contenido = (
        "=== ENCABEZADO ===\n"
        + Encabezado
        + "\n=== COLUMNA IZQUIERDA ===\n"
        + Izquierda
        + "\n=== COLUMNA DERECHA ===\n"
        + Derecha
    )

    Reporte.write_text(
        Contenido,
        encoding="utf-8"
    )

    print(f"Reporte generado: {Reporte}")


if __name__ == "__main__":
    Principal()
