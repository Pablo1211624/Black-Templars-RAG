import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


def NormalizarNombre(Texto):
    Texto = unicodedata.normalize("NFKC", Texto).casefold()
    for Guion in ("‑", "‐", "–", "—", "−"):
        Texto = Texto.replace(Guion, "-")
    return " ".join(Texto.split())


# Equivalencias puntuales observadas en las fichas del PDF.
# Documentan diferencias de nomenclatura, NO certifican legalidad.
# Clave: (unidad, nombre usado por la regla, cantidad requerida).
ALIAS_DOCUMENTADOS = {
    (
        "STORM EAGLE GUNSHIP",
        "twin hellstrike missile launchers",
        2,
    ): "twin hellstrike launchers",
    (
        "FIRE RAPTOR GUNSHIP",
        "twin hellstrike missile launchers",
        2,
    ): "twin hellstrike launchers",
}


def SepararOrigenes(Texto):
    """Devuelve cantidades y nombres, o None si hay una disyunción."""
    if not Texto or re.search(r"\s+or\s+", Texto, re.I):
        return None

    Elementos = Counter()
    for Fragmento in re.split(r"\s+and\s+", Texto, flags=re.I):
        Fragmento = Fragmento.strip().removesuffix(".")
        Coincidencia = re.fullmatch(r"(\d+)\s+(.+)", Fragmento)
        if Coincidencia:
            Cantidad = int(Coincidencia.group(1))
            Nombre = Coincidencia.group(2)
        else:
            Cantidad, Nombre = 1, Fragmento

        Nombre = NormalizarNombre(Nombre)
        if not Nombre or Cantidad <= 0:
            return None
        Elementos[Nombre] += Cantidad

    return Elementos


def ValidarCruceInicial(Fichas):
    """Comprueba presencia en el equipo inicial; NO valida legalidad."""
    Resultado = []

    for Ficha in Fichas:
        Declaraciones = [
            Declaracion
            for Declaracion in Ficha.get("EquipamientoInicial", [])
            if Declaracion["Sujeto"].casefold() == "this model"
        ]

        for Regla in Ficha.get("InterpretacionOpciones", {}).get(
            "Estructuradas", []
        ):
            if (
                Regla["Tipo"] != "Sustitucion"
                or Regla["Sujeto"].casefold() != "this model"
            ):
                continue

            Origenes = SepararOrigenes(Regla["OrigenTexto"])
            Faltantes = []
            AliasUtilizados = []

            if len(Declaraciones) != 1 or Origenes is None:
                Estado = "NoEvaluable"
            else:
                Inicial = Counter()
                for Elemento in Declaraciones[0]["Elementos"]:
                    Inicial[NormalizarNombre(Elemento["Nombre"])] += (
                        Elemento["Cantidad"]
                    )

                for Nombre, Cantidad in Origenes.items():
                    if Inicial[Nombre] >= Cantidad:
                        continue

                    # El alias se usa solo para el nombre, unidad y cantidad
                    # incluidos expresamente en el registro documentado.
                    Equivalente = ALIAS_DOCUMENTADOS.get(
                        (Ficha["Unidad"], Nombre, Cantidad)
                    )
                    if Equivalente and Inicial[Equivalente] >= Cantidad:
                        AliasUtilizados.append({
                            "NombreRegla": Nombre,
                            "NombreInicial": Equivalente,
                            "Cantidad": Cantidad,
                        })
                    else:
                        Faltantes.append({
                            "Nombre": Nombre,
                            "Requerido": Cantidad,
                            "Inicial": Inicial[Nombre],
                        })

                if Faltantes:
                    Estado = "NoCoincideConInicial"
                elif AliasUtilizados:
                    Estado = "CoincidePorAliasDocumentado"
                else:
                    Estado = "CoincideConInicial"

            Resultado.append({
                "Unidad": Ficha["Unidad"],
                "Pagina": Regla["Pagina"],
                "ReglaOriginal": Regla["ReglaOriginal"],
                "Estado": Estado,
                "Faltantes": Faltantes,
                "AliasUtilizados": AliasUtilizados,
            })

    return Resultado


if __name__ == "__main__":
    Entrada = Path("preprocesos/PdfExtraccionFichasReporte.json")
    Salida = Path("preprocesos/ValidacionCruceEquipo.json")

    Fichas = json.loads(Entrada.read_text(encoding="utf-8"))
    Resultado = ValidarCruceInicial(Fichas)
    Salida.write_text(
        json.dumps(Resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Sustituciones directas examinadas:", len(Resultado))
    print("Estados:", dict(Counter(R["Estado"] for R in Resultado)))

    for Registro in Resultado:
        if Registro["Estado"] != "CoincideConInicial":
            print("- {}: {}".format(Registro["Unidad"], Registro["Estado"]))
            print("  Regla:", Registro["ReglaOriginal"])
            for Alias in Registro["AliasUtilizados"]:
                print("  Alias: {} -> {}".format(
                    Alias["NombreRegla"], Alias["NombreInicial"]
                ))
    print("Reporte:", Salida)
