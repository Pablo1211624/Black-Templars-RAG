
import json
import re
from collections import Counter
from pathlib import Path

import pymupdf


Raiz = Path(__file__).resolve().parents[3]
CarpetaPdfs = Raiz / "Data" / "Pdfs"
RutaReporte = (
    Raiz / "Backend" / "preprocesos"
    / "PdfClasificacionReporte.json"
)


def ClasificarTexto(Texto: str) -> str:
    """Clasifica una página según su contenido textual."""

    Texto = " ".join(Texto.upper().split())

    if len(Texto) < 50:
        return "PocoTexto"

    if (
        "RANGED WEAPONS" in Texto
        or "MELEE WEAPONS" in Texto
    ):
        return "FichaConArmas"

    if (
        "UNIT COMPOSITION" in Texto
        and "KEYWORDS" in Texto
    ):
        return "FichaSinTablaArmas"

    if (
        "DETACHMENT RULES" in Texto
        or "DETACHMENT RULE" in Texto
    ):
        return "Destacamento"

    if "BASE SIZE" in Texto and "UNIT" in Texto:
        return "TablaReferencias"

    if re.search(r"\b\d+\s*PTS\b", Texto):
        return "TablaPuntos"

    if "FAQ" in Texto:
        return "PreguntasFrecuentes"

    return "TextoGeneral"


def ClasificarDocumentos() -> list:
    """Recorre todos los PDF y clasifica sus páginas."""

    if not CarpetaPdfs.is_dir():
        raise FileNotFoundError(
            f"No existe la carpeta: {CarpetaPdfs}"
        )

    Resultados = []

    for Ruta in sorted(CarpetaPdfs.glob("*.pdf")):
        Paginas = []

        with pymupdf.open(Ruta) as Documento:
            for Numero, Pagina in enumerate(Documento, 1):
                Texto = Pagina.get_text("text")

                Paginas.append({
                    "Pagina": Numero,
                    "Tipo": ClasificarTexto(Texto),
                })

        Conteo = Counter(
            Pagina["Tipo"] for Pagina in Paginas
        )

        Resultados.append({
            "Documento": Ruta.name,
            "TotalPaginas": len(Paginas),
            "Conteo": dict(Conteo),
            "Paginas": Paginas,
        })

        print(f"\nDocumento: {Ruta.name}")
        print(f"Total paginas: {len(Paginas)}")

        for Tipo, Cantidad in Conteo.items():
            print(f"  {Tipo}: {Cantidad}")

    return Resultados


def Principal():
    Resultados = ClasificarDocumentos()

    RutaReporte.parent.mkdir(
        parents=True, exist_ok=True
    )

    RutaReporte.write_text(
        json.dumps(
            Resultados,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8",
    )

    print(f"\nReporte generado: {RutaReporte}")


if __name__ == "__main__":
    Principal()
