
import re


PATRON_ENCABEZADO = re.compile(
    r"^(The .+?) can do one of the following:$",
    re.IGNORECASE,
)

PATRON_SUSTITUCION = re.compile(
    r"^Replace its (.+?) with (.+?)\.?$",
    re.IGNORECASE,
)

PATRON_ADICION = re.compile(
    r"^Be equipped with (.+?)\.?$",
    re.IGNORECASE,
)


def InterpretarReglasCompuestas(Pendientes):
    """Reconoce elecciones entre operaciones distintas."""

    Resultado = {
        "Compuestas": [],
        "Pendientes": [],
    }

    for Regla in Pendientes:
        Texto = Regla["ReglaOriginal"].strip()

        Coincidencia = PATRON_ENCABEZADO.fullmatch(Texto)

        if (
            Coincidencia is None
            or len(Regla["Alternativas"]) < 2
        ):
            Resultado["Pendientes"].append(Regla)
            continue

        Operaciones = []

        for Alternativa in Regla["Alternativas"]:
            Alternativa = Alternativa.strip()

            Sustitucion = PATRON_SUSTITUCION.fullmatch(
                Alternativa
            )

            Adicion = PATRON_ADICION.fullmatch(
                Alternativa
            )

            if Sustitucion:
                Operaciones.append({
                    "Tipo": "Sustitucion",
                    "OrigenTexto": Sustitucion.group(1),
                    "DestinoTexto": Sustitucion.group(2),
                    "TextoOriginal": Alternativa,
                })

            elif Adicion:
                Operaciones.append({
                    "Tipo": "Adicion",
                    "OrigenTexto": None,
                    "DestinoTexto": Adicion.group(1),
                    "TextoOriginal": Alternativa,
                })

            else:
                Operaciones = []
                break

        if not Operaciones:
            Resultado["Pendientes"].append(Regla)
            continue

        Resultado["Compuestas"].append({
            "Tipo": "EleccionEntreOperaciones",
            "Sujeto": Coincidencia.group(1),
            "Operaciones": Operaciones,
            "Eleccion": "UnaDeVarias",
            "ReglaOriginal": Texto,
            "Pagina": Regla["Pagina"],
        })

    return Resultado
