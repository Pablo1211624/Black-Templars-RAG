
import json
from pathlib import Path

import pymupdf


Raiz = Path(__file__).resolve().parents[2]
CarpetaPdfs = Raiz / "Data" / "Pdfs"
Reporte = Path(__file__).with_name("PdfEstructuraReporte.json")

Documentos = sorted(
    Archivo.name
    for Archivo in CarpetaPdfs.glob("*.pdf")
)

def InspeccionarPagina(Pagina, Numero):
    """Obtiene muestras de texto, fuentes y posiciones."""

    Fragmentos = []

    for Bloque in Pagina.get_text("dict")["blocks"]:
        for Linea in Bloque.get("lines", []):
            for Span in Linea["spans"]:
                Texto = " ".join(Span["text"].split())

                if len(Texto) < 4:
                    continue

                Fragmentos.append({
                    "Texto": Texto[:100],
                    "TamanoFuente": round(Span["size"], 2),
                    "Fuente": Span["font"],
                    "X": round(Span["bbox"][0], 2),
                    "Y": round(Span["bbox"][1], 2),
                })

    # Los textos grandes son candidatos a encabezados.
    Fragmentos.sort(
        key=lambda Elemento: (
            -Elemento["TamanoFuente"],
            Elemento["Y"],
            Elemento["X"],
        )
    )

    return {
        "Pagina": Numero,
        "Ancho": round(Pagina.rect.width, 2),
        "Alto": round(Pagina.rect.height, 2),
        "Candidatos": Fragmentos[:12],
    }


def InspeccionarDocumento(Ruta):
    """Inspecciona páginas representativas del documento."""

    with pymupdf.open(Ruta) as Pdf:
        Total = len(Pdf)

        PaginasMuestra = sorted({
            Numero
            for Numero in [
                1, 2, 3, 4, 5, 8, 30,
                36, 62, Total // 2, Total
            ]
            if 1 <= Numero <= Total
        })

        return {
            "Documento": Ruta.name,
            "TotalPaginas": Total,
            "PaginasInspeccionadas": [
                InspeccionarPagina(Pdf[Numero - 1], Numero)
                for Numero in PaginasMuestra
            ],
        }


def Principal():
    Resultados = []

    for Nombre in Documentos:
        Ruta = CarpetaPdfs / Nombre

        if not Ruta.is_file():
            raise FileNotFoundError(
                f"No se encontro el documento: {Ruta}"
            )

        Resultado = InspeccionarDocumento(Ruta)
        Resultados.append(Resultado)

        print(f"\nDocumento: {Nombre}")
        print(
            "Paginas muestreadas:",
            len(Resultado["PaginasInspeccionadas"])
        )

    Reporte.write_text(
        json.dumps(Resultados, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nReporte generado: {Reporte}")


if __name__ == "__main__":
    Principal()
