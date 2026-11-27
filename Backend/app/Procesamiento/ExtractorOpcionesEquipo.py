
import re


def ExtraerOpcionesEquipo(Secciones):
    """Agrupa reglas, alternativas y notas sin interpretar restricciones."""

    Resultado = {
        "Reglas": [],
        "Notas": [],
        "DeclaraNinguna": False,
    }

    RequiereRevision = False

    for Bloque in Secciones.get("OpcionesEquipo", []):
        Actual = None
        Destino = None

        for Linea in Bloque["Texto"].splitlines():
            # El PDF contiene caracteres de control invisibles.
            Linea = "".join(
                Caracter
                for Caracter in Linea
                if ord(Caracter) >= 32
            ).strip()

            if not Linea:
                continue

            Principal = re.match(r"^[■▪]\s*(.*)$", Linea)
            Alternativa = re.match(r"^[◦○]\s*(.*)$", Linea)
            Nota = re.match(r"^(\*{1,3})\s+(.+)$", Linea)

            if Principal:
                Texto = Principal.group(1).strip()

                if Texto.casefold() == "none":
                    Resultado["DeclaraNinguna"] = True
                    Actual = None
                    Destino = None

                elif Texto:
                    Actual = {
                        "Regla": Texto,
                        "Alternativas": [],
                        "Pagina": Bloque["Pagina"],
                    }

                    Resultado["Reglas"].append(Actual)
                    Destino = "Regla"

                else:
                    RequiereRevision = True
                    Actual = None
                    Destino = None

            elif Alternativa:
                Texto = Alternativa.group(1).strip()

                if Actual is None or not Texto:
                    RequiereRevision = True
                    Resultado["Notas"].append({
                        "Marcador": "SinContexto",
                        "Texto": Linea,
                        "Pagina": Bloque["Pagina"],
                    })
                    Destino = "Nota"

                else:
                    Actual["Alternativas"].append(Texto)
                    Destino = "Alternativa"

            elif Nota:
                Resultado["Notas"].append({
                    "Marcador": Nota.group(1),
                    "Texto": Nota.group(2),
                    "Pagina": Bloque["Pagina"],
                })
                Destino = "Nota"

            elif Destino == "Regla" and Actual is not None:
                Actual["Regla"] += " " + Linea

            elif Destino == "Alternativa" and Actual is not None:
                Actual["Alternativas"][-1] += " " + Linea

            elif Destino == "Nota" and Resultado["Notas"]:
                Resultado["Notas"][-1]["Texto"] += " " + Linea

            else:
                RequiereRevision = True
                Resultado["Notas"].append({
                    "Marcador": "SinContexto",
                    "Texto": Linea,
                    "Pagina": Bloque["Pagina"],
                })
                Destino = "Nota"

    return Resultado, RequiereRevision
