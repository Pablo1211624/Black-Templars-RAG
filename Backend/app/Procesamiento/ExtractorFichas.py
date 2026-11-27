
import json

import pymupdf

import re

from app.Procesamiento.AgrupadorFichas import (
    AnalizarFichas,
    CarpetaPdfs,
    Raiz,
)

from app.Procesamiento.ExtractorArmas import ExtraerArmas

from app.Procesamiento.ExtractorSecciones import ExtraerSecciones

from app.Procesamiento.ExtractorEquipamiento import ExtraerEquipamientoInicial

from app.Procesamiento.ExtractorOpcionesEquipo import ExtraerOpcionesEquipo

from app.Procesamiento.InterpretadorOpciones import InterpretarOpciones

from app.Procesamiento.InterpretadorRestricciones import InterpretarRestricciones

from app.Procesamiento.InterpretadorReglasCompuestas import (
    InterpretarReglasCompuestas
)

def ExtraerCaracteristicas(Texto):
    """Extrae características estándar y variantes de orden."""

    Campos = ("M", "T", "SV", "W", "LD", "OC")

    Patrones = (
        r'(?:\d+["″]|-)',
        r"\d+",
        r"\d+\+",
        r"\d+",
        r"\d+\+",
        r"(?:\d+|-)",
    )

    Lineas = [
        Linea.strip()
        for Linea in Texto.splitlines()
        if Linea.strip()
    ]

    # Caso 1: estructura estándar.
    for Posicion in range(len(Lineas) - 5):
        Encabezado = tuple(
            Lineas[Posicion:Posicion + 6]
        )

        if Encabezado != Campos:
            continue

        Caracteristicas = []
        Indice = Posicion + 6

        while Indice + 6 <= len(Lineas):
            Valores = Lineas[Indice:Indice + 6]

            SonValidos = all(
                re.fullmatch(Patron, Valor)
                for Patron, Valor in zip(Patrones, Valores)
            )

            if not SonValidos:
                break

            Caracteristicas.append(
                dict(zip(Campos, Valores))
            )

            Indice += 6

        if Caracteristicas:
            return Caracteristicas

    # Caso 2: PyMuPDF devuelve el movimiento
    # fuera del orden habitual.
    for Posicion in range(len(Lineas) - 11):

        Encabezado = Lineas[Posicion:Posicion + 5]

        if Encabezado != list(Campos[1:]):
            continue

        Bloque = Lineas[Posicion + 5:Posicion + 12]

        if Bloque[1] == "M":
            # Movimiento antes de los otros valores.
            Valores = [Bloque[0], *Bloque[2:]]

        elif Bloque[6] == "M":
            # Movimiento después de los otros valores.
            Valores = [Bloque[5], *Bloque[:5]]

        else:
            continue

        SonValidos = all(
            re.fullmatch(Patron, Valor)
            for Patron, Valor in zip(Patrones, Valores)
        )

        if SonValidos:
            return [dict(zip(Campos, Valores))]

    return []


def AsociarModelos(Pagina, Caracteristicas):
    """Asocia las filas de estadísticas con sus modelos por posición visual."""

    if len(Caracteristicas) < 2:
        return Caracteristicas

    Fragmentos = [
        Span
        for Bloque in Pagina.get_text("dict")["blocks"]
        for Linea in Bloque.get("lines", [])
        for Span in Linea.get("spans", [])
        if Span["text"].strip()
    ]

    # Localizar el encabezado M de la tabla.
    EncabezadosM = [
        Span for Span in Fragmentos
        if Span["text"].strip() == "M"
        and Span["bbox"][0] < 50
        and 5 <= Span["size"] <= 9
    ]

    if len(EncabezadosM) != 1:
        return Caracteristicas

    YEncabezado = EncabezadosM[0]["bbox"][3]

    # Encontrar las filas de movimiento en la primera columna.
    Movimientos = sorted(
        (
            Span for Span in Fragmentos
            if Span["bbox"][0] < 45
            and YEncabezado < Span["bbox"][1] < YEncabezado + 100
            and Span["size"] >= 12
        ),
        key=lambda Span: Span["bbox"][1],
    )

    # Verificar que coincidan con los perfiles extraídos.
    if [Span["text"].strip() for Span in Movimientos] != [
        Perfil["M"] for Perfil in Caracteristicas
    ]:
        return Caracteristicas

    Ys = [Span["bbox"][1] for Span in Movimientos]
    Resultado = []

    for Indice, Perfil in enumerate(Caracteristicas):
        LimiteInferior = (
            Ys[Indice] - 6 if Indice == 0
            else (Ys[Indice - 1] + Ys[Indice]) / 2
        )

        LimiteSuperior = (
            Ys[Indice] + 25 if Indice == len(Ys) - 1
            else (Ys[Indice] + Ys[Indice + 1]) / 2
        )

        # Buscar los nombres situados a la derecha de cada fila.
        Etiquetas = sorted(
            (
                Span for Span in Fragmentos
                if 185 <= Span["bbox"][0] <= 400
                and LimiteInferior <= Span["bbox"][1] < LimiteSuperior
                and 8 <= Span["size"] <= 11
                and "bold" in Span["font"].lower()
            ),
            key=lambda Span: (
                Span["bbox"][1],
                Span["bbox"][0],
            ),
        )

        Nombres = " ".join(
            Span["text"].strip()
            for Span in Etiquetas
        )

        NuevoPerfil = Perfil.copy()

        if Nombres:
            NuevoPerfil["Modelos"] = [
                Nombre.strip()
                for Nombre in Nombres.split(",")
                if Nombre.strip()
            ]

        Resultado.append(NuevoPerfil)

    return Resultado


def DetectarLegends(Paginas):
    """Detecta la marca Warhammer Legends en el encabezado."""

    for Pagina in Paginas:
        Lineas = [
            Linea.strip().upper()
            for Linea in Pagina["Texto"].splitlines()[:4]
        ]

        if "WARHAMMER L E G E N D S" in Lineas:
            return True

    return False



def ExtraerFichas(Documento, Grupos, NombreDocumento):
    """Extrae el contenido de cada ficha con sus páginas de origen."""

    Fichas = []

    for Grupo in Grupos:
        if Grupo["Tipo"] != "FichaUnidad":
            continue

        Paginas = []

        for Numero in Grupo["Paginas"]:
            Pagina = Documento[Numero - 1]
            

            Paginas.append({
                "Pagina": Numero,
                "Texto": Pagina.get_text("text", sort=False),
            })

        Secciones = ExtraerSecciones(
            Paginas,
            Grupo["Unidad"]
        )

        OpcionesEquipo, RevisionOpciones = (
            ExtraerOpcionesEquipo(Secciones)
        )

        InterpretacionOpciones, RevisionSemantica = (
            InterpretarOpciones(OpcionesEquipo)
        )

        InterpretacionRestricciones = InterpretarRestricciones(
            InterpretacionOpciones["Pendientes"]
        )

        InterpretacionCompuestas = InterpretarReglasCompuestas(
            InterpretacionRestricciones["Pendientes"]
        )

        EquipamientoInicial, RevisionEquipamiento = (
            ExtraerEquipamientoInicial(Secciones)
        )

        TextoCompleto = "\n".join(
            Pagina["Texto"]
            for Pagina in Paginas
        )

        Caracteristicas = ExtraerCaracteristicas(
            TextoCompleto
        )

        if len(Caracteristicas) > 1:
            Caracteristicas = AsociarModelos(
            Documento[Grupo["Paginas"][0] - 1], Caracteristicas
        )


        EsLegends = DetectarLegends(Paginas)


        Armas = {
            "Disparo": [],
            "CuerpoACuerpo": [],
        }

        RevisionArmas = False

        for PaginaExtraida in Paginas:
            ArmasPagina, RevisionPagina = ExtraerArmas(
                PaginaExtraida["Texto"],
                PaginaExtraida["Pagina"],
            )

            for Tipo in Armas:
                Armas[Tipo].extend(ArmasPagina[Tipo])

            RevisionArmas = RevisionArmas or RevisionPagina

        Fichas.append({
            "Unidad": Grupo["Unidad"],
            "Documento": NombreDocumento,
            "EsLegends": EsLegends,
            "Armas": Armas,
            "InterpretacionOpciones": InterpretacionOpciones,
            "RequiereRevisionSemanticaOpciones": RevisionSemantica,
            "RequiereRevisionArmas": RevisionArmas,
            "OpcionesEquipo": OpcionesEquipo,
            "RequiereRevisionOpciones": RevisionOpciones,
            "InterpretacionRestricciones": InterpretacionRestricciones,
            "RequiereRevisionRestricciones": bool(InterpretacionRestricciones["Pendientes"]),
            "InterpretacionCompuestas": InterpretacionCompuestas,
            "RequiereRevisionFinalOpciones": (RevisionOpciones or bool(InterpretacionCompuestas["Pendientes"])),
            "Paginas": Paginas,
            "Caracteristicas": Caracteristicas,
            "EquipamientoInicial": EquipamientoInicial,
            "RequiereRevisionEquipamiento": RevisionEquipamiento,
            "Secciones": Secciones,
            "RequiereRevisionCaracteristicas": not bool(Caracteristicas),
            "RequiereRevisionModelos": (
                len(Caracteristicas) > 1
                and any(
                    not Perfil.get("Modelos")
                    for Perfil in Caracteristicas
                )
            ),
        })

    return Fichas


def Principal():
    Archivo = CarpetaPdfs / (
        "eng_08-06_warhammer40000_faction_pack_space-marines"
        "-nd2ezs5yzn-wxe2nf2ckk.pdf"
    )

    with pymupdf.open(Archivo) as Documento:
        Resultado = AnalizarFichas(Documento)

        Fichas = ExtraerFichas(
            Documento,
            Resultado["Grupos"],
            Archivo.name,
        )

    RutaReporte = (
        Raiz / "Backend" / "preprocesos"
        / "PdfExtraccionFichasReporte.json"
    )

    RutaReporte.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RutaReporte.write_text(
        json.dumps(
            Fichas,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Fichas extraídas: {len(Fichas)}")
    print(f"Reporte generado: {RutaReporte}")


if __name__ == "__main__":
    Principal()
