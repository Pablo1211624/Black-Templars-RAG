
import re


PATRONES = [
    (
        "CualquierCantidad",
        "Sustitucion",
        re.compile(
            r"^Any number of (?P<Sujeto>.+?) can each have their "
            r"(?P<Origen>.+?) replaced with (?P<Destino>.+)$",
            re.IGNORECASE,
        ),
    ),
    (
        "CualquierCantidad",
        "Sustitucion",
        re.compile(
            r"^Any number of (?P<Sujeto>.+?)[’'] "
            r"(?P<Origen>.+?) can each be replaced with "
            r"(?P<Destino>.+)$",
            re.IGNORECASE,
        ),
    ),
    (
        "MaximoEnUnidad",
        "Sustitucion",
        re.compile(
            r"^Up to (?P<Maximo>\d+) (?P<Sujeto>.+?) "
            r"can each have their (?P<Origen>.+?) replaced with "
            r"(?P<Destino>.+)$",
            re.IGNORECASE,
        ),
    ),
    (
        "PorCadaModelos",
        "Sustitucion",
        re.compile(
            r"^For every (?P<PorCada>\d+) models in this unit, "
            r"(?P<Maximo>\d+) (?P<Sujeto>.+?)[’']s "
            r"(?P<Origen>.+?) can be replaced with "
            r"(?P<Destino>.+)$",
            re.IGNORECASE,
        ),
    ),
    (
        "PorCadaModelos",
        "Adicion",
        re.compile(
            r"^For every (?P<PorCada>\d+) models in this unit, "
            r"(?P<Maximo>\d+) (?P<Sujeto>.+?) "
            r"can be equipped with (?P<Destino>.+)$",
            re.IGNORECASE,
        ),
    ),
]


PATRONES_ESPECIALES = [
    (
        "ModeloEspecifico",
        re.compile(
            r"^(?P<Sujeto>(?:The|An|A|1)\s+.+?)[’']s "
            r"(?P<Origen>.+?) can be replaced with "
            r"(?P<Destino>.+)$",
            re.IGNORECASE,
        ),
    ),
    (
        "CantidadArmas",
        re.compile(
            r"^(?P<Cantidad>\d+) of this model[’']s "
            r"(?P<Origen>.+?) can be replaced with "
            r"(?P<Destino>.+)$",
            re.IGNORECASE,
        ),
    ),
    (
        "CadaArma",
        re.compile(
            r"^Each of this model[’']s "
            r"(?P<Origen>.+?) can be replaced with "
            r"(?P<Destino>.+)$",
            re.IGNORECASE,
        ),
    ),
]


def InterpretarCasoEspecial(Regla):
    """Reconoce sustituciones con sujetos o cantidades explícitas."""

    Texto = Regla["ReglaOriginal"].strip()

    for Tipo, Patron in PATRONES_ESPECIALES:
        Coincidencia = Patron.fullmatch(Texto)

        if Coincidencia is None:
            continue

        Datos = Coincidencia.groupdict()

        Destino = (
            Datos["Destino"]
            .strip()
            .removesuffix(".")
        )

        EsLista = (
            Destino.casefold() == "one of the following:"
        )

        Destinos = (
            list(Regla["Alternativas"])
            if EsLista
            else [Destino]
        )

        # No inventar alternativas ni ignorar listas.
        if (
            not Destinos
            or any(not Valor.strip() for Valor in Destinos)
            or (Regla["Alternativas"] and not EsLista)
        ):
            return None

        Sujeto = Datos.get("Sujeto") or "This model"

        CantidadModelos = (
            1 if Sujeto.startswith("1 ") else None
        )

        CantidadArmas = (
            int(Datos["Cantidad"])
            if Datos.get("Cantidad")
            else None
        )

        return {
            "ReglaOriginal": Texto,
            "Pagina": Regla["Pagina"],
            "Tipo": "Sustitucion",
            "Sujeto": Sujeto,
            "Restriccion": {
                "Tipo": Tipo,
                "Maximo": None,
                "PorCada": None,
                "CantidadModelosIndicada": CantidadModelos,
                "CantidadArmas": CantidadArmas,
            },
            "OrigenTexto": Datos["Origen"].strip(),
            "DestinosTexto": Destinos,
            "Eleccion": (
                "UnaDeVarias" if EsLista else "Directa"
            ),
        }

    return None


def InterpretarRestricciones(Pendientes):
    """Interpreta límites explícitos sin calcular equipos legales."""

    Resultado = {
        "Interpretadas": [],
        "Pendientes": [],
    }

    for Regla in Pendientes:
        Texto = Regla["ReglaOriginal"].strip()
        Coincidencia = None
        TipoRestriccion = None
        TipoOperacion = None

        for TipoRestriccion, TipoOperacion, Patron in PATRONES:
            Coincidencia = Patron.fullmatch(Texto)

            if Coincidencia:
                break

        
        if Coincidencia is None:
            CasoEspecial = InterpretarCasoEspecial(Regla)

            if CasoEspecial is not None:
                Resultado["Interpretadas"].append(
                    CasoEspecial
                )
            else:
                Resultado["Pendientes"].append(Regla)

            continue

        Datos = Coincidencia.groupdict()

        Destino = Datos["Destino"].strip().removesuffix(".")

        EsLista = (
            Destino.casefold() == "one of the following:"
        )

        Destinos = (
            list(Regla["Alternativas"])
            if EsLista
            else [Destino]
        )

        # No corregimos expresiones ambiguas del documento.
        DestinoAmbiguo = bool(
            re.match(r"^one\s+\d+\b", Destino, re.I)
        )

        if (
            not Destinos
            or DestinoAmbiguo
            or (not EsLista and Regla["Alternativas"])
        ):
            Resultado["Pendientes"].append(Regla)
            continue

        Resultado["Interpretadas"].append({
            "ReglaOriginal": Texto,
            "Pagina": Regla["Pagina"],
            "Tipo": TipoOperacion,
            "Sujeto": Datos["Sujeto"],
            "Restriccion": {
                "Tipo": TipoRestriccion,
                "Maximo": (
                    int(Datos["Maximo"])
                    if Datos.get("Maximo")
                    else None
                ),
                "PorCada": (
                    int(Datos["PorCada"])
                    if Datos.get("PorCada")
                    else None
                ),
            },
            "OrigenTexto": Datos.get("Origen"),
            "DestinosTexto": Destinos,
            "Eleccion": (
                "UnaDeVarias"
                if EsLista
                else "Directa"
            ),
        })

    return Resultado
