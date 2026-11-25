
SECCIONES = {
    "ABILITIES": "Habilidades",
    "WARGEAR ABILITIES": "HabilidadesEquipo",
    "WARGEAR OPTIONS": "OpcionesEquipo",
    "UNIT COMPOSITION": "Composicion",
    "DAMAGED": "ReglasDanio",
}

LIMITES = {
    "RANGED WEAPONS",
    "RANGED WEAPON",
    "MELEE WEAPONS",
    "MELEE WEAPON",
    "ABILITIES",
    "WARGEAR ABILITIES",
    "WARGEAR OPTIONS",
    "LEADER",
    "TRANSPORT",
    "ATTACHED UNIT",
    "ATTACHED UNITS",
    "POINTS",
    "INVULNERABLE SAVE",
    "M",
    "WARHAMMER L E G E N D S",
}


def IdentificarEncabezado(Linea):
    """Reconoce encabezados y límites de secciones."""

    if Linea.startswith("UNIT COMPOSITION"):
        return "UNIT COMPOSITION"

    if Linea.startswith("DAMAGED:"):
        return "DAMAGED"

    if (
        Linea.startswith("KEYWORDS")
        or Linea.startswith("FACTION KEYWORDS")
        or Linea.startswith("INVULNERABLE SAVE")
    ):
        return "LIMITE"

    if Linea in LIMITES:
        return Linea

    return None


def ExtraerSecciones(Paginas, Unidad):
    """Separa bloques de reglas sin interpretar su contenido."""

    Resultado = {
        Nombre: []
        for Nombre in SECCIONES.values()
    }

    for Pagina in Paginas:
        Lineas = [
            Linea.strip()
            for Linea in Pagina["Texto"].splitlines()
            if Linea.strip()
        ]

        Indice = 0

        while Indice < len(Lineas):
            Encabezado = IdentificarEncabezado(
                Lineas[Indice]
            )

            if Encabezado not in SECCIONES:
                Indice += 1
                continue

            Inicio = Indice + 1
            Final = Inicio

            while Final < len(Lineas):
                Actual = Lineas[Final]

                if (
                    IdentificarEncabezado(Actual) is not None
                    or Actual.casefold() == Unidad.casefold()
                ):
                    break

                Final += 1

            Resultado[SECCIONES[Encabezado]].append({
                "Pagina": Pagina["Pagina"],
                "Encabezado": Lineas[Indice],
                "Texto": "\n".join(Lineas[Inicio:Final]),
            })

            Indice = Final

    return Resultado
