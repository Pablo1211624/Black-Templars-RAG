
from pathlib import Path

import pymupdf



Raiz = Path(__file__).resolve().parents[2]

# Conserva aquí la misma ruta que ya funciona
# en tu InspectorColumna.py.
CarpetaPdfs = CarpetaPdfs = Raiz / "Data" / "Pdfs"

Archivo = CarpetaPdfs / (
    "eng_08-06_warhammer40000_faction_pack_space-marines"
    "-nd2ezs5yzn-wxe2nf2ckk.pdf"
)

Reporte = Path(__file__).with_name(
    "PdfFichaCatoSicariusReporte.txt"
)


def InspeccionarFicha():
    with pymupdf.open(Archivo) as Documento:
        Pagina = Documento[35]  # Página 30: LAND SPEEDER

        RutaImagen = Path(__file__).with_name("PdfFichaCatoSicarius.png")

        Imagen = Pagina.get_pixmap(matrix=pymupdf.Matrix(2, 2),alpha=False)

        Imagen.save(RutaImagen)

        TextoOriginal = Pagina.get_text(
            "text", sort=False
        )

        Bloques = Pagina.get_text(
            "blocks", sort=False
        )

        Lineas = []

        for Bloque in Bloques:
            X0, Y0, X1, Y1, Texto, Numero, Tipo = Bloque

            if Tipo != 0 or not Texto.strip():
                continue

            Lineas.append(
                f"Bloque {Numero} | "
                f"X={X0:.1f} Y={Y0:.1f}\n"
                f"{Texto}\n"
            )

        Contenido = (
            "=== DIMENSIONES ===\n"
            f"Ancho: {Pagina.rect.width:.2f}\n"
            f"Alto: {Pagina.rect.height:.2f}\n\n"
            "=== TEXTO ORIGINAL ===\n"
            + TextoOriginal
            + "\n=== BLOQUES CON COORDENADAS ===\n"
            + "\n".join(Lineas)
        )

        Reporte.write_text(
            Contenido,
            encoding="utf-8"
        )

    print(f"Reporte generado: {Reporte}")


if __name__ == "__main__":
    InspeccionarFicha()
