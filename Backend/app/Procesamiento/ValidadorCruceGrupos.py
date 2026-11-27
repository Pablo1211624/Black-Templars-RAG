"""Cruce de reglas grupales contra composición y equipamiento inicial.

No aplica sustituciones, no elige tamaño de escuadra, ni certifica
configuraciones legales. No equipara armas distintas automáticamente.
"""
import json
import re
from collections import Counter
from pathlib import Path

from app.Procesamiento.ValidadorCruceEquipo import (
    NormalizarNombre,
    SepararOrigenes,
)
from app.Procesamiento.ValidadorCruceModelos import (
    AplicaDeclaracion,
    ClaveModelo,
)


PATRON_FILA = re.compile(r"^[■▪]\s*(\d+)(?:\s*-\s*(\d+))?\s+(.+?)\s*$")
TIPOS_GRUPALES = {"CualquierCantidad", "MaximoEnUnidad", "PorCadaModelos"}


def ExtraerGruposComposicion(Ficha):
    """Lee rangos mínimo/máximo, sin elegir una composición concreta."""
    Grupos = []
    for Bloque in Ficha.get("Secciones", {}).get("Composicion", []):
        for Linea in Bloque.get("Texto", "").splitlines():
            Coincidencia = PATRON_FILA.fullmatch(Linea.strip())
            if Coincidencia is None:
                continue
            Minimo = int(Coincidencia.group(1))
            Maximo = int(Coincidencia.group(2) or Minimo)
            Nombre = Coincidencia.group(3).strip()
            if Minimo > Maximo:
                continue
            Grupos.append({
                "Nombre": Nombre,
                "Clave": ClaveModelo(Nombre),
                "Minimo": Minimo,
                "Maximo": Maximo,
            })
    return Grupos


def _ElegirDeclaracion(Ficha, Sujeto):
    """Escoge una única declaración sin fusionar equipos ambiguos."""
    Candidatas = [
        D for D in Ficha.get("EquipamientoInicial", [])
        if AplicaDeclaracion(D["Sujeto"], Sujeto)
    ]
    Especificas = [
        D for D in Candidatas
        if NormalizarNombre(D["Sujeto"]) != "every model"
    ]
    if len(Especificas) == 1:
        return Especificas[0]
    if not Especificas and len(Candidatas) == 1:
        return Candidatas[0]
    return None


def _CompararOrigenes(Origenes, Declaracion):
    """Compara cantidades por modelo, y anota flexiones singulares.

    Un plural regular como 'bolt pistols' puede coincidir con 'bolt pistol'.
    No se admite cualquier similitud de cadenas ni se altera el texto fuente.
    """
    Inicial = Counter()
    for Elemento in Declaracion.get("Elementos", []):
        Inicial[NormalizarNombre(Elemento["Nombre"])] += Elemento["Cantidad"]

    Faltantes, Flexiones = [], []
    for Nombre, Cantidad in Origenes.items():
        if Inicial[Nombre] >= Cantidad:
            continue
        Singular = Nombre[:-1] if Nombre.endswith("s") and not Nombre.endswith("ss") else None
        if Singular and Inicial[Singular] >= Cantidad:
            Flexiones.append({"NombreRegla": Nombre, "NombreInicial": Singular})
        else:
            Faltantes.append({
                "Nombre": Nombre,
                "RequeridoPorModelo": Cantidad,
                "InicialPorModelo": Inicial[Nombre],
            })
    return Faltantes, Flexiones


def ValidarCruceGrupos(Fichas):
    """Examina las 3 familias de restricciones grupales reconocidas."""
    Resultado = []
    for Ficha in Fichas:
        Grupos = ExtraerGruposComposicion(Ficha)
        for Regla in Ficha.get("InterpretacionRestricciones", {}).get("Interpretadas", []):
            Restriccion = Regla.get("Restriccion", {})
            Tipo = Restriccion.get("Tipo")
            if Tipo not in TIPOS_GRUPALES:
                continue
            Sujeto = ClaveModelo(Regla.get("Sujeto", ""))
            Generico = Sujeto in {"model", "models"}
            Elegibles = (
                Grupos if Generico
                else [G for G in Grupos if G["Clave"] == Sujeto]
            )

            Origenes = (
                SepararOrigenes(Regla.get("OrigenTexto"))
                if Regla.get("Tipo") == "Sustitucion"
                else None
            )
            Evaluaciones = []
            for Grupo in Elegibles:
                D = _ElegirDeclaracion(Ficha, Grupo["Clave"])
                if D is None:
                    EstadoGrupo = "NoEvaluable"
                    Faltantes, Flexiones = [], []
                elif Regla.get("Tipo") == "Adicion":
                    EstadoGrupo = "AdicionSinOrigen"
                    Faltantes, Flexiones = [], []
                elif Origenes is None:
                    EstadoGrupo = "NoEvaluable"
                    Faltantes, Flexiones = [], []
                else:
                    Faltantes, Flexiones = _CompararOrigenes(Origenes, D)
                    EstadoGrupo = (
                        "NoCoincideConInicial" if Faltantes
                        else "CoincidePorFlexion" if Flexiones
                        else "CoincideConInicial"
                    )

                Evaluaciones.append({
                    "Modelo": Grupo["Nombre"],
                    "Minimo": Grupo["Minimo"],
                    "Maximo": Grupo["Maximo"],
                    "DeclaracionUtilizada": D["Sujeto"] if D else None,
                    "Estado": EstadoGrupo,
                    "Faltantes": Faltantes,
                    "Flexiones": Flexiones,
                })

            if not Elegibles:
                Estado = "SujetoNoIdentificado"
            elif any(E["Estado"] == "NoCoincideConInicial" for E in Evaluaciones):
                Estado = "NoCoincideConInicial"
            elif any(E["Estado"] == "NoEvaluable" for E in Evaluaciones):
                Estado = "NoEvaluable"
            elif all(E["Estado"] == "AdicionSinOrigen" for E in Evaluaciones):
                Estado = "AdicionSinOrigen"
            elif any(E["Estado"] == "CoincidePorFlexion" for E in Evaluaciones):
                Estado = "CoincidePorFlexion"
            else:
                Estado = "CoincideConInicial"

            Resultado.append({
                "Unidad": Ficha["Unidad"],
                "Pagina": Regla["Pagina"],
                "ReglaOriginal": Regla["ReglaOriginal"],
                "Sujeto": Regla["Sujeto"],
                "TipoOperacion": Regla["Tipo"],
                "Restriccion": Restriccion,
                "Estado": Estado,
                "ModelosElegibles": Evaluaciones,
                "TotalModelosUnidad": {
                    "Minimo": sum(G["Minimo"] for G in Grupos),
                    "Maximo": sum(G["Maximo"] for G in Grupos),
                },
            })
    return Resultado


if __name__ == "__main__":
    Entrada = Path("preprocesos/PdfExtraccionFichasReporte.json")
    Salida = Path("preprocesos/ValidacionCruceGrupos.json")
    Fichas = json.loads(Entrada.read_text(encoding="utf-8"))
    Resultado = ValidarCruceGrupos(Fichas)
    Salida.write_text(
        json.dumps(Resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Reglas grupales examinadas:", len(Resultado))
    print("Estados:", dict(Counter(R["Estado"] for R in Resultado)))
    for R in Resultado:
        if R["Estado"] != "CoincideConInicial":
            print("- {}: {} ({})".format(R["Unidad"], R["Estado"], R["Sujeto"]))
    print("Reporte:", Salida)
