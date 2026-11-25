
from pathlib import Path
import json

import pymupdf


Raiz = Path(__file__).resolve().parents[3]
CarpetaPdfs = Raiz / "Data" / "Pdfs"




def ObtenerTituloFicha(Pagina):
    """Reconstruye títulos completos a partir de sus fragmentos."""

    Estructura = Pagina.get_text("dict")
    Fragmentos = []

    for Bloque in Estructura["blocks"]:
        for Linea in Bloque.get("lines", []):
            for Span in Linea["spans"]:
                if Span["text"].strip():
                    Fragmentos.append(Span)

    # Identificar el encabezado principal.
    Titulos = [
        Span
        for Span in Fragmentos
        if (
            14 <= Span["size"] <= 17
            and "extrabold" in Span["font"].lower()
            and Span["bbox"][1] < 30
            and Span["bbox"][0] < Pagina.rect.width / 2
        )
    ]

    if not Titulos:
        return None

    Principal = min(
        Titulos,
        key=lambda Span: (
            Span["bbox"][1],
            Span["bbox"][0],
        )
    )

    Partes = [Principal]

    # Fuentes utilizadas para complementar los títulos.
    Complementos = [
        Span
        for Span in Fragmentos
        if (
            Span is not Principal
            and 8 <= Span["size"] <= 11
            and (
                "italic" in Span["font"].lower()
                or "semilight" in Span["font"].lower()
            )
            and abs(
                Span["bbox"][1] - Principal["bbox"][1]
            ) <= 10
            and Span["bbox"][0] > Principal["bbox"][0]
            and Span["bbox"][2] < Pagina.rect.width / 2
        )
    ]

    Complementos.sort(
        key=lambda Span: Span["bbox"][0]
    )

    # Reconstruir el título de izquierda a derecha.
    LimiteDerecho = Principal["bbox"][2]

    for Span in Complementos:
        Inicio = Span["bbox"][0]
        Final = Span["bbox"][2]

        Separacion = Inicio - LimiteDerecho

        if Separacion < -5:
            continue

        if Separacion > 25:
            break

        Partes.append(Span)
        LimiteDerecho = max(LimiteDerecho, Final)

    return " ".join(
        Span["text"].strip()
        for Span in Partes
    )



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


def ClasificarGrupo(Unidad: str, Texto: str) -> str:
    """Clasifica un grupo según su contenido."""

    Nombre = Unidad.upper()
    Contenido = Texto.upper()

    EsReglaFaccion = (
    "UNIT OPTIONS" in Contenido
    and "DATASHEETS CAN BE INCLUDED" in Contenido
    and "REPLACE INSTANCES" in Contenido
    )

    if EsReglaFaccion:
        return "ReglasFaccion"

    EsTablaArmas = (
        "ARMOURY" in Nombre
        and "RANGED WEAPONS" in Contenido
        and "KEYWORDS:" not in Contenido
    )

    if EsTablaArmas:
        return "TablaArmas"

    TieneFichaCompleta = (
        "UNIT COMPOSITION" in Contenido
        and "KEYWORDS" in Contenido
    )

    TieneFichaConAtributos = (
        "KEYWORDS:" in Contenido
        and "ABILITIES" in Contenido
    )

    if TieneFichaCompleta or TieneFichaConAtributos:
        return "FichaUnidad"

    return "RevisionManual"


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

    
    Grupos = AgruparPaginas(Registros)

    for Grupo in Grupos:
        TextoGrupo = "\n".join(
            Documento[Numero - 1].get_text("text")
            for Numero in Grupo["Paginas"]
        )

        Grupo["Tipo"] = ClasificarGrupo(
            Grupo["Unidad"],
            TextoGrupo
        )

    return {
        "Grupos": Grupos,
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
