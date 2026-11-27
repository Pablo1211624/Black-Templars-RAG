
import re

PATRON_EQUIPAMIENTO = re.compile(
    r"\bis equipped with:\s*",
    re.IGNORECASE
)


def ExtraerEquipamientoInicial(Secciones):
    """Extrae el equipamiento inicial sin interpretar sustituciones."""

    Resultado = []
    RequiereRevision = False

    for Bloque in Secciones.get("Composicion", []):
        Lineas = [
            Linea.strip()
            for Linea in Bloque["Texto"].splitlines()
            if Linea.strip()
        ]

        for Indice, Linea in enumerate(Lineas):
            Coincidencia = PATRON_EQUIPAMIENTO.search(Linea)

            if Coincidencia is None:
                continue

            # Identificar a quién pertenece el equipamiento.
            Sujeto = Linea[:Coincidencia.start()].strip()

            if not Sujeto and Indice > 0:
                Sujeto = Lineas[Indice - 1]

            if not Sujeto:
                RequiereRevision = True
                continue

            # Reconstruir la lista cuando ocupa varias líneas.
            TextoEquipo = Linea[Coincidencia.end():].strip()
            Siguiente = Indice + 1

            while "." not in TextoEquipo and Siguiente < len(Lineas):
                Proxima = Lineas[Siguiente]

                # Evitar absorber párrafos narrativos extensos.
                PosibleNarracion = (
                    len(Proxima.split()) >= 7
                    and Proxima[0].isupper()
                    and ";" not in Proxima
                )

                if (
                    PosibleNarracion
                    or PATRON_EQUIPAMIENTO.search(Proxima)
                ):
                    RequiereRevision = True
                    break

                TextoEquipo += " " + Proxima
                Siguiente += 1

            TextoEquipo = TextoEquipo.split(".", 1)[0].strip()

            Elementos = []

            # "nothing" significa que no hay equipo declarado.
            if TextoEquipo.casefold() != "nothing":
                for Fragmento in re.split(r"[;,]", TextoEquipo):
                    Fragmento = Fragmento.strip()

                    if not Fragmento:
                        continue

                    CoincidenciaCantidad = re.fullmatch(
                        r"(\d+)\s+(.+)",
                        Fragmento
                    )

                    if CoincidenciaCantidad:
                        Cantidad = int(
                            CoincidenciaCantidad.group(1)
                        )
                        Nombre = CoincidenciaCantidad.group(2)
                    else:
                        Cantidad = 1
                        Nombre = Fragmento

                    Elementos.append({
                        "Cantidad": Cantidad,
                        "Nombre": Nombre,
                    })

            Resultado.append({
                "Sujeto": Sujeto,
                "Elementos": Elementos,
                "Pagina": Bloque["Pagina"],
                "TextoFuente": TextoEquipo,
            })

    return Resultado, RequiereRevision
