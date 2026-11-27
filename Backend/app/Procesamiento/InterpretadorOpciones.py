
import re


PATRONES = [
    (
        "Sustitucion",
        re.compile(
            r"^This model[’']s "
            r"(?P<Origen>.+?) can be replaced with "
            r"(?P<Destino>.+?)[.]?$",
            re.IGNORECASE,
        ),
    ),
    (
        "Sustitucion",
        re.compile(
            r"^This model can have its "
            r"(?P<Origen>.+?) replaced with "
            r"(?P<Destino>.+?)[.]?$",
            re.IGNORECASE,
        ),
    ),
    (
        "Adicion",
        re.compile(
            r"^This model can be equipped with "
            r"(?P<Destino>.+?)[.]?$",
            re.IGNORECASE,
        ),
    ),
    (
        "EleccionObligatoria",
        re.compile(
            r"^This model must be equipped with "
            r"(?P<Destino>.+?)[.]?$",
            re.IGNORECASE,
        ),
    ),
]


def InterpretarOpciones(OpcionesEquipo):
    """
    Estructura opciones de un único modelo.

    No aplica sustituciones ni calcula configuraciones legales.
    Las instrucciones no reconocidas quedan pendientes.
    """

    Resultado = {
        "Estructuradas": [],
        "Pendientes": [],
    }

    for Regla in OpcionesEquipo.get("Reglas", []):
        Texto = Regla["Regla"].strip()

        DatosBase = {
            "ReglaOriginal": Texto,
            "Pagina": Regla["Pagina"],
        }

        Coincidencia = None
        TipoEncontrado = None

        for Tipo, Patron in PATRONES:
            Coincidencia = Patron.fullmatch(Texto)

            if Coincidencia is not None:
                TipoEncontrado = Tipo
                break

        if Coincidencia is None:
            Resultado["Pendientes"].append({
                **DatosBase,
                "Alternativas": Regla["Alternativas"],
            })
            continue

        Destino = (
            Coincidencia.group("Destino")
            .strip()
            .removesuffix(".")
        )

        EsSeleccion = (
            Destino.casefold() == "one of the following:"
        )

        if EsSeleccion:
            Destinos = list(Regla["Alternativas"])
        else:
            Destinos = [Destino]

        # Evitar interpretar tablas incompletas o ambiguas.
        EstructuraInvalida = (
            not Destinos
            or (
                bool(Regla["Alternativas"])
                and not EsSeleccion
            )
        )

        if EstructuraInvalida:
            Resultado["Pendientes"].append({
                **DatosBase,
                "Alternativas": Regla["Alternativas"],
            })
            continue

        Resultado["Estructuradas"].append({
            **DatosBase,
            "Tipo": TipoEncontrado,
            "Sujeto": "This model",
            "OrigenTexto": Coincidencia.groupdict().get(
                "Origen"
            ),
            "DestinosTexto": Destinos,
            "Eleccion": (
                "UnaDeVarias"
                if EsSeleccion
                else "Directa"
            ),
        })

    RequiereRevision = bool(Resultado["Pendientes"])

    return Resultado, RequiereRevision
