"""Cruce conservador de sustituciones para modelos específicos.

No calcula legalidad de configuraciones ni aplica sustituciones.
"""
import json
import re
from collections import Counter
from pathlib import Path

from app.Procesamiento.ValidadorCruceEquipo import (
    NormalizarNombre,
    SepararOrigenes,
)


# Equivalencia específica comprobada en el PDF de Space Marines, pp. 133-134.
# Una variante del nombre no implica por sí sola legalidad.
ALIAS_MODELOS_DOCUMENTADOS = {
    ("SCOUT SNIPER SQUAD", "scout sniper rifle", 1): "sniper rifle",
}


PATRON_MODELO = re.compile(
    r"^[■▪]\s*\d+(?:-\d+)?\s+(.+?)\s*$"
)


def ClaveModelo(Texto):
    """Normaliza una designación de modelo para comparar nombres."""
    Texto = NormalizarNombre(Texto)
    Texto = re.sub(r"^(?:the|an|a|each|every|1)\s+", "", Texto)
    Texto = re.split(r"\s+[-–—]\s+", Texto, maxsplit=1)[0]
    # Solo normalizamos el plural regular del último término.
    Palabras = Texto.split()
    if Palabras and Palabras[-1].endswith("s") and not Palabras[-1].endswith("ss"):
        Palabras[-1] = Palabras[-1][:-1]
    return " ".join(Palabras)


def ModelosComposicion(Ficha):
    """Obtiene únicamente los nombres declarados en UNIT COMPOSITION."""
    Modelos = set()
    for Bloque in Ficha.get("Secciones", {}).get("Composicion", []):
        for Linea in Bloque["Texto"].splitlines():
            Hallazgo = PATRON_MODELO.match(Linea.strip())
            if Hallazgo:
                Modelos.add(ClaveModelo(Hallazgo.group(1)))
    return Modelos


def AplicaDeclaracion(SujetoDeclaracion, SujetoRegla):
    """Comprueba si la declaración cubre explícitamente al sujeto."""
    if NormalizarNombre(SujetoDeclaracion) == "every model":
        return True
    Partes = re.split(
        r"\s+and\s+(?=(?:every|each|the|an|a)\b)",
        SujetoDeclaracion,
        flags=re.IGNORECASE,
    )
    return any(ClaveModelo(Parte) == SujetoRegla for Parte in Partes)


def ValidarCruceModelos(Fichas):
    """Examina las sustituciones ya clasificadas como ModeloEspecifico."""
    Resultado = []

    for Ficha in Fichas:
        Modelos = ModelosComposicion(Ficha)

        for Regla in Ficha.get(
            "InterpretacionRestricciones", {}
        ).get("Interpretadas", []):
            if (
                Regla.get("Tipo") != "Sustitucion"
                or Regla.get("Restriccion", {}).get("Tipo") != "ModeloEspecifico"
            ):
                continue

            Sujeto = ClaveModelo(Regla["Sujeto"])
            Declaracion = None
            Faltantes = []
            AliasUtilizados = []

            if Sujeto not in Modelos:
                Estado = "SujetoNoIdentificado"
            else:
                Elegibles = [
                    D for D in Ficha.get("EquipamientoInicial", [])
                    if AplicaDeclaracion(D["Sujeto"], Sujeto)
                ]
                # Preferimos la asignación al modelo exacto sobre una genérica.
                Especificas = [
                    D for D in Elegibles
                    if NormalizarNombre(D["Sujeto"]) != "every model"
                ]
                if len(Especificas) == 1:
                    Declaracion = Especificas[0]
                elif not Especificas and len(Elegibles) == 1:
                    Declaracion = Elegibles[0]

                Origenes = SepararOrigenes(Regla.get("OrigenTexto"))
                if Declaracion is None or Origenes is None:
                    Estado = "NoEvaluable"
                else:
                    Inicial = Counter()
                    for Elemento in Declaracion["Elementos"]:
                        Inicial[NormalizarNombre(Elemento["Nombre"])] += Elemento["Cantidad"]
                    for Nombre, Cantidad in Origenes.items():
                        if Inicial[Nombre] >= Cantidad:
                            continue

                        Equivalente = ALIAS_MODELOS_DOCUMENTADOS.get(
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
                "Sujeto": Regla["Sujeto"],
                "DeclaracionUtilizada": (
                    Declaracion["Sujeto"] if Declaracion else None
                ),
                "Estado": Estado,
                "Faltantes": Faltantes,
                "AliasUtilizados": AliasUtilizados,
            })

    return Resultado


if __name__ == "__main__":
    Entrada = Path("preprocesos/PdfExtraccionFichasReporte.json")
    Salida = Path("preprocesos/ValidacionCruceModelos.json")
    Fichas = json.loads(Entrada.read_text(encoding="utf-8"))
    Resultados = ValidarCruceModelos(Fichas)
    Salida.write_text(
        json.dumps(Resultados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Sustituciones de modelos examinadas:", len(Resultados))
    print("Estados:", dict(Counter(x["Estado"] for x in Resultados)))
    for R in Resultados:
        if R["Estado"] != "CoincideConInicial":
            print("- {} / {}: {}".format(
                R["Unidad"], R["Sujeto"], R["Estado"]
            ))
            print("  Regla:", R["ReglaOriginal"])
            print("  Faltantes:", R["Faltantes"])
            print("  Alias:", R["AliasUtilizados"])
