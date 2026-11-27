
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


def NormalizarNombre(Texto):
    Texto = unicodedata.normalize("NFKC", Texto).casefold()
    Texto = re.sub(r"^\d+\s+", "", Texto)
    return " ".join(Texto.rstrip(".* ").split())


def ProponerCorreccion(Texto):
    """Sugiere correcciones sin modificar el texto fuente."""

    Patrones = [
        (
            r"\breplaced one of the following:$",
            "replaced with one of the following:",
        ),
        (
            r"\bwith one 1\b",
            "with 1",
        ),
        (
            r"\bwith on of the following:$",
            "with one of the following:",
        ),
        (
            r"^(This model[’']s .+?) replaced with\b",
            r"\1 can be replaced with",
        ),
    ]

    for Patron, Reemplazo in Patrones:
        Corregido, Cambios = re.subn(
            Patron, Reemplazo, Texto, count=1
        )

        if Cambios:
            return Corregido

    return None


def AuditarFicha(Ficha):
    Observaciones = []
    Unidad = Ficha["Unidad"]

    def Agregar(Tipo, Pagina, Texto, Propuesta, Detalle):
        Observaciones.append({
            "Unidad": Unidad,
            "Documento": Ficha["Documento"],
            "Pagina": Pagina,
            "Tipo": Tipo,
            "TextoOriginal": Texto,
            "Propuesta": Propuesta,
            "Detalle": Detalle,
            "Estado": "PendienteVerificacionPDF",
        })

    # 1. Identificar reglas que aún no se interpretaron.
    Pendientes = Ficha.get(
        "InterpretacionCompuestas", {}
    ).get("Pendientes", [])

    for Regla in Pendientes:
        Original = Regla["ReglaOriginal"]

        Agregar(
            "ReglaNoInterpretada",
            Regla["Pagina"],
            Original,
            ProponerCorreccion(Original),
            "La regla no coincide con los patrones seguros.",
        )

    # 2. Detectar la posible errata 'volite/volkite'.
    NombresArmas = [
        Arma["Nombre"].casefold()
        for Grupo in Ficha.get("Armas", {}).values()
        for Arma in Grupo
    ]

    if any("volkite" in Nombre for Nombre in NombresArmas):
        for Regla in Ficha.get(
            "OpcionesEquipo", {}
        ).get("Reglas", []):

            for Alternativa in Regla["Alternativas"]:
                if re.search(
                    r"\bvolite\b", Alternativa, flags=re.I
                ):
                    Propuesta = re.sub(
                        r"\bvolite\b",
                        "volkite",
                        Alternativa,
                        flags=re.I,
                    )

                    Agregar(
                        "PosibleErrataNombreArma",
                        Regla["Pagina"],
                        Alternativa,
                        Propuesta,
                        "La tabla de armas utiliza volkite.",
                    )

    # 3. Revisar adiciones del mismo modelo
    # que ya figuran en su equipamiento inicial.
    Inicial = {
        NormalizarNombre(Elemento["Nombre"])
        for Declaracion in Ficha.get(
            "EquipamientoInicial", []
        )
        if Declaracion["Sujeto"].casefold() == "this model"
        for Elemento in Declaracion["Elementos"]
    }

    Reglas = (
        Ficha.get(
            "InterpretacionOpciones", {}
        ).get("Estructuradas", [])
        + Ficha.get(
            "InterpretacionRestricciones", {}
        ).get("Interpretadas", [])
    )

    for Regla in Reglas:
        if (
            Regla["Tipo"] != "Adicion"
            or Regla["Sujeto"].casefold() != "this model"
        ):
            continue

        for Destino in Regla["DestinosTexto"]:
            if NormalizarNombre(Destino) in Inicial:
                Agregar(
                    "PosibleEquipamientoDuplicado",
                    Regla["Pagina"],
                    Regla["ReglaOriginal"],
                    None,
                    "La opción añade un elemento que "
                    "figura en el equipamiento inicial.",
                )

    return Observaciones


def AuditarFichas(Fichas):
    return [
        Observacion
        for Ficha in Fichas
        for Observacion in AuditarFicha(Ficha)
    ]


if __name__ == "__main__":
    Entrada = Path(
        "preprocesos/PdfExtraccionFichasReporte.json"
    )

    Salida = Path(
        "preprocesos/AuditoriaCalidadEquipo.json"
    )

    Fichas = json.loads(
        Entrada.read_text(encoding="utf-8")
    )

    Observaciones = AuditarFichas(Fichas)

    Salida.write_text(
        json.dumps(
            Observaciones,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Observaciones:", len(Observaciones))

    Tipos = Counter(
        Observacion["Tipo"]
        for Observacion in Observaciones
    )

    print("Tipos:", dict(Tipos))

    for Observacion in Observaciones:
        print(
            "- {}: {} (p. {})".format(
                Observacion["Unidad"],
                Observacion["Tipo"],
                Observacion["Pagina"],
            )
        )

    print("Reporte:", Salida)
