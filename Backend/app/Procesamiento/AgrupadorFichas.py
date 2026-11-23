
from pathlib import Path
import json

import pymupdf


Raiz = Path(__file__).resolve().parents[3]
CarpetaPdfs = Raiz / "Data" / "Pdfs"


def ObtenerTituloFicha(Pagina):
    """Identifica el encabezado de una datasheet."""

    Estructura = Pagina.get_text("dict")

    for Bloque in Estructura["blocks"]:
        for Linea in Bloque.get("lines", []):
            for Span in Linea["spans"]:
                Texto = Span["text"].strip()

                EsTitulo = (
                    14 <= Span["size"] <= 17
                    and "extrabold" in Span["font"].lower()
                    and Span["bbox"][1] < 30
                    and Span["bbox"][0] < Pagina.rect.width / 2
                )

                if EsTitulo and Texto:
                    return Texto

    return None


def VerificarContinuidad(PaginaActual, PaginaSiguiente):
    """Comprueba si dos páginas tienen el mismo título."""

    TituloActual = ObtenerTituloFicha(PaginaActual)
    TituloSiguiente = ObtenerTituloFicha(PaginaSiguiente)

    if not TituloActual or not TituloSiguiente:
        return False

    return (
        TituloActual.casefold()
        == TituloSiguiente.casefold()
    )


def AgruparPaginas(Registros):
    """Agrupa páginas consecutivas con el mismo título."""

    Grupos = []

    for Registro in Registros:
        Unidad = Registro["Unidad"]
        Numero = Registro["Pagina"]

        if Unidad is None:
            continue

        if Grupos:
            UltimoGrupo = Grupos[-1]

            MismoTitulo = (
                UltimoGrupo["Unidad"].casefold()
                == Unidad.casefold()
            )

            SonConsecutivas = (
                UltimoGrupo["Paginas"][-1] + 1 == Numero
            )

            if MismoTitulo and SonConsecutivas:
                UltimoGrupo["Paginas"].append(Numero)
                continue

        Grupos.append({
            "Unidad": Unidad,
            "Paginas": [Numero],
        })

    return Grupos


def AnalizarFichas(Documento):
    """Identifica y agrupa posibles fichas del PDF."""

    Registros = []
    PaginasSinTitulo = []

    for Numero, Pagina in enumerate(Documento, 1):

        # Las datasheets observadas son horizontales.
        if Pagina.rect.width <= Pagina.rect.height:
            continue

        Titulo = ObtenerTituloFicha(Pagina)

        Registros.append({
            "Pagina": Numero,
            "Unidad": Titulo,
        })

        if Titulo is None:
            PaginasSinTitulo.append(Numero)

    return {
        "Grupos": AgruparPaginas(Registros),
        "PaginasSinTitulo": PaginasSinTitulo,
    }




def Principal():
    Archivo = CarpetaPdfs / (
        "eng_08-06_warhammer40000_faction_pack_space-marines"
        "-nd2ezs5yzn-wxe2nf2ckk.pdf"
    )

    with pymupdf.open(Archivo) as Documento:
        Resultado = AnalizarFichas(Documento)

    Reporte = (
        Raiz / "Backend" / "preprocesos"
        / "PdfAgrupacionFichasReporte.json"
    )

    Reporte.write_text(
        json.dumps(
            Resultado,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8",
    )

    Grupos = Resultado["Grupos"]

    print(f"Fichas identificadas: {len(Grupos)}")
    print(
        "Paginas sin titulo identificado:",
        len(Resultado["PaginasSinTitulo"])
    )

    print("\nAgrupacion de Cato Sicarius:")

    for Grupo in Grupos:
        if Grupo["Unidad"] == "CATO SICARIUS":
            print(Grupo)

    print(f"\nReporte generado: {Reporte}")



if __name__ == "__main__":
    Principal()
