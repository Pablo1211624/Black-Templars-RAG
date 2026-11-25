
import re


def ExtraerArmas(Texto, NumeroPagina):
    """Extrae perfiles de armas y conserva su página de origen."""

    Lineas = [
        Linea.strip()
        for Linea in Texto.splitlines()
        if Linea.strip()
    ]

    Tipos = {
        "RANGED WEAPONS": "Disparo",
        "RANGED WEAPON": "Disparo",
        "MELEE WEAPONS": "CuerpoACuerpo",
        "MELEE WEAPON": "CuerpoACuerpo",
    }

    Armas = {"Disparo": [], "CuerpoACuerpo": []}
    Revision = False

    for Indice, Encabezado in enumerate(Lineas):
        Tipo = Tipos.get(Encabezado)

        if Tipo is None:
            continue

        Habilidad = "BS" if Tipo == "Disparo" else "WS"
        Columnas = ["RANGE", "A", Habilidad, "S", "AP", "D"]

        if Lineas[Indice + 1:Indice + 7] != Columnas:
            Revision = True
            continue

        Posicion = Indice + 7
        Fragmentos = []
        Encontradas = 0

        while Posicion < len(Lineas):
            Actual = Lineas[Posicion]

            FinDeTabla = (
                Actual in Tipos
                or Actual in {
                    "FACTION KEYWORDS:",
                    "ABILITIES",
                    "WARGEAR ABILITIES",
                    "WARGEAR OPTIONS",
                    "UNIT COMPOSITION",
                    "M",
                }
                or Actual.startswith("KEYWORDS:")
            )

            if FinDeTabla:
                break

            Valores = Lineas[Posicion:Posicion + 6]

            PatronRango = (
                "Melee" if Tipo == "CuerpoACuerpo"
                else r'\d+["″]'
            )

            Patrones = (
                PatronRango,
                r"(?:\d+|(?:\d+)?D\d+(?:[+-]\d+)?)",
                r"(?:\d+\+|N/A)",
                r"\d+",
                r"-?\d+",
                r"(?:\d+|(?:\d+)?D\d+(?:[+-]\d+)?)",
            )

            EsPerfil = (
                len(Valores) == 6
                and all(
                    re.fullmatch(Patron, Valor)
                    for Patron, Valor in zip(Patrones, Valores)
                )
            )

            if not EsPerfil:
                Fragmentos.append(Actual)
                Posicion += 1
                continue

            # Algunas habilidades aparecen en otra línea.
            if (
                len(Fragmentos) >= 2
                and Fragmentos[-1].startswith("[")
            ):
                NombreCrudo = " ".join(Fragmentos[-2:])
            elif Fragmentos:
                NombreCrudo = Fragmentos[-1]
            else:
                Revision = True
                Posicion += 6
                continue

            Coincidencia = re.fullmatch(
                r"(.*?)\s*\[([^\]]+)\]",
                NombreCrudo
            )

            if Coincidencia:
                Nombre = Coincidencia.group(1).strip()
                Habilidades = [
                    Valor.strip()
                    for Valor in Coincidencia.group(2).split(",")
                ]
            else:
                Nombre = NombreCrudo.strip()
                Habilidades = []

            if not Nombre:
                Revision = True
            else:
                Armas[Tipo].append({
                    "Nombre": Nombre,
                    "Habilidades": Habilidades,
                    "Rango": Valores[0],
                    "A": Valores[1],
                    Habilidad: Valores[2],
                    "S": Valores[3],
                    "AP": Valores[4],
                    "D": Valores[5],
                    "Pagina": NumeroPagina,
                })

                Encontradas += 1

            Fragmentos = []
            Posicion += 6

        if Encontradas == 0:
            Revision = True

    return Armas, Revision
