"""Simulación conservadora y transaccional de sustituciones por modelo.

Alcance: una sola declaración 'This model', sustituciones simples de
InterpretacionOpciones y restricciones CantidadArmas / CadaArma.
No certifica legalidad de configuraciones del juego; ignora reglas no modeladas.
"""

import json
from collections import Counter
from pathlib import Path

from app.Procesamiento.ValidadorCruceEquipo import NormalizarNombre, SepararOrigenes


FUENTES = {
    "Opciones": ("InterpretacionOpciones", "Estructuradas"),
    "Restricciones": ("InterpretacionRestricciones", "Interpretadas"),
}
TIPOS_PERMITIDOS = {"CantidadArmas", "CadaArma"}


def _InventarioInicial(Ficha):
    Declaraciones = [
        D for D in Ficha.get("EquipamientoInicial", [])
        if D.get("Sujeto", "").casefold() == "this model"
    ]
    if len(Declaraciones) != 1:
        return None
    Inventario = Counter()
    for Elemento in Declaraciones[0].get("Elementos", []):
        Cantidad = Elemento.get("Cantidad")
        Nombre = NormalizarNombre(Elemento.get("Nombre", ""))
        if (
            type(Cantidad) is not int
            or Cantidad <= 0
            or not Nombre
        ):
            return None
        Inventario[Nombre] += Cantidad
    return Inventario


def _NombreEnInventario(Nombre, Inventario):
    """Solo flexiones triviales de singular/plural; nunca alias arbitrarios."""
    Nombre = NormalizarNombre(Nombre)
    if Nombre in Inventario:
        return Nombre
    if Nombre.endswith("s") and Nombre[:-1] in Inventario:
        return Nombre[:-1]
    if Nombre + "s" in Inventario:
        return Nombre + "s"
    return Nombre


def _Origenes(Regla, Fuente):
    Origenes = SepararOrigenes(Regla.get("OrigenTexto"))
    if not Origenes:
        return None
    if Fuente == "Opciones":
        return Origenes
    Restriccion = Regla.get("Restriccion", {})
    Tipo = Restriccion.get("Tipo")
    if Tipo not in TIPOS_PERMITIDOS or len(Origenes) != 1:
        return None
    Nombre, TextoCantidad = next(iter(Origenes.items()))
    if Tipo == "CantidadArmas":
        Cantidad = Restriccion.get("CantidadArmas")
        if type(Cantidad) is not int or Cantidad < 1:
            return None
        if TextoCantidad not in (1, Cantidad):
            return None
    else:  # CadaArma: una aplicación por arma, no todas de golpe.
        if TextoCantidad != 1:
            return None
        Cantidad = 1
    return Counter({Nombre: Cantidad})


def _Destino(Alternativa):
    """No interpreta notas de pie, comas ni disyunciones sin analizar."""
    Texto = Alternativa.strip()
    if not Texto or "*" in Texto or "," in Texto:
        return None
    return SepararOrigenes(Texto)


def _Limpiar(Inventario):
    return dict(sorted(
        (Nombre, Cantidad)
        for Nombre, Cantidad in Inventario.items() if Cantidad > 0
    ))


def SimularSustituciones(Ficha, Pasos):
    """Aplica una secuencia declarada; si falla algún paso, revierte todo.

    Cada paso: {"Fuente": "Opciones"|"Restricciones", "IndiceRegla": N,
                "IndiceAlternativa": M}.
    IndiceAlternativa puede omitirse solo para reglas con un único destino.
    Las reglas CantidadArmas y las de Opciones se usan una vez por índice;
    las CadaArma pueden usarse varias veces mientras haya origen.
    """
    Inicial = _InventarioInicial(Ficha)
    Resultado = {
        "Unidad": Ficha.get("Unidad"),
        "Estado": "NoEvaluable" if Inicial is None else "Completada",
        "InventarioInicial": None if Inicial is None else _Limpiar(Inicial),
        "InventarioFinal": None if Inicial is None else _Limpiar(Inicial),
        "Pasos": [],
        "ReversionAplicada": False,
        "Alcance": "Solo sustituciones de This model; no valida legalidad",
    }
    if Inicial is None:
        return Resultado
    Inventario = Inicial.copy()
    Usadas = set()

    for Numero, Paso in enumerate(Pasos, start=1):
        Registro = {"Paso": Numero, "Estado": "Rechazado"}
        Motivo = None
        if not isinstance(Paso, dict):
            Motivo = "PasoInvalido"
        else:
            Fuente = Paso.get("Fuente")
            Indice = Paso.get("IndiceRegla")
            Registro.update({"Fuente": Fuente, "IndiceRegla": Indice})
            if Fuente not in FUENTES or type(Indice) is not int or Indice < 0:
                Motivo = "PasoInvalido"
            else:
                Clave, Subclave = FUENTES[Fuente]
                Reglas = Ficha.get(Clave, {}).get(Subclave, [])
                if Indice >= len(Reglas):
                    Motivo = "ReglaNoEncontrada"
                else:
                    Regla = Reglas[Indice]
                    TipoRestriccion = Regla.get("Restriccion", {}).get("Tipo")
                    if (
                        Regla.get("Tipo") != "Sustitucion"
                        or (Fuente == "Restricciones" and TipoRestriccion not in TIPOS_PERMITIDOS)
                    ):
                        Motivo = "TipoNoSoportado"
                    elif NormalizarNombre(Regla.get("Sujeto", "")) != "this model":
                        Motivo = "SujetoNoSoportado"
                    elif (Fuente, Indice) in Usadas and TipoRestriccion != "CadaArma":
                        Motivo = "ReglaYaUtilizada"
                    else:
                        Origenes = _Origenes(Regla, Fuente)
                        Alternativas = Regla.get("DestinosTexto", [])
                        Alternativa = Paso.get("IndiceAlternativa")
                        if not Origenes:
                            Motivo = "OrigenAmbiguo"
                        elif not isinstance(Alternativas, list) or not Alternativas:
                            Motivo = "SinDestinos"
                        elif Alternativa is None and len(Alternativas) == 1:
                            Alternativa = 0
                        elif type(Alternativa) is not int or not 0 <= Alternativa < len(Alternativas):
                            Motivo = "AlternativaInvalida"
                        if Motivo is None:
                            Registro["IndiceAlternativa"] = Alternativa
                            Destinos = _Destino(Alternativas[Alternativa])
                            if not Destinos:
                                Motivo = "DestinoNoDesglosable"
                            else:
                                Consumos = Counter()
                                for Nombre, Cantidad in Origenes.items():
                                    ClaveNombre = _NombreEnInventario(Nombre, Inventario)
                                    Consumos[ClaveNombre] += Cantidad
                                Faltantes = {
                                    Nombre: {"Necesario": Necesario, "Disponible": Inventario[Nombre]}
                                    for Nombre, Necesario in Consumos.items()
                                    if Inventario[Nombre] < Necesario
                                }
                                if Faltantes:
                                    Motivo = "OrigenInsuficiente"
                                    Registro["Faltantes"] = Faltantes
                                else:
                                    # Actualización atómica de un paso, sin dejar negativos.
                                    for Nombre, Cantidad in Consumos.items():
                                        Inventario[Nombre] -= Cantidad
                                    Altas = Counter()
                                    for Nombre, Cantidad in Destinos.items():
                                        ClaveNombre = _NombreEnInventario(Nombre, Inventario)
                                        Altas[ClaveNombre] += Cantidad
                                    for Nombre, Cantidad in Altas.items():
                                        Inventario[Nombre] += Cantidad
                                    Registro.update({
                                        "Estado": "Aplicado",
                                        "ReglaOriginal": Regla.get("ReglaOriginal"),
                                        "AlternativaElegida": Alternativas[Alternativa],
                                        "Consumido": dict(Consumos),
                                        "Anadido": dict(Altas),
                                        "InventarioTrasPaso": _Limpiar(Inventario),
                                    })
                                    Usadas.add((Fuente, Indice))
        if Motivo is not None:
            Registro["Motivo"] = Motivo
            Resultado["Pasos"].append(Registro)
            Resultado["Estado"] = "Rechazada"
            Resultado["ReversionAplicada"] = True
            Resultado["InventarioFinal"] = _Limpiar(Inicial)
            return Resultado
        Resultado["Pasos"].append(Registro)

    Resultado["InventarioFinal"] = _Limpiar(Inventario)
    return Resultado


if __name__ == "__main__":
    Entrada = Path("preprocesos/PdfExtraccionFichasReporte.json")
    Salida = Path("preprocesos/SimulacionesSustituciones.json")
    Fichas = json.loads(Entrada.read_text(encoding="utf-8"))
    PorUnidad = {Ficha["Unidad"]: Ficha for Ficha in Fichas}
    Casos = {
        "KRATOS_dos_reglas": (
            "KRATOS",
            [
                {"Fuente": "Restricciones", "IndiceRegla": 0, "IndiceAlternativa": 0},
                {"Fuente": "Restricciones", "IndiceRegla": 1, "IndiceAlternativa": 2},
            ],
        ),
        "RELIC_CONTEMPTOR_encadenada": (
            "RELIC CONTEMPTOR DREADNOUGHT",
            [
                {"Fuente": "Restricciones", "IndiceRegla": 0, "IndiceAlternativa": 7},
                {"Fuente": "Restricciones", "IndiceRegla": 1, "IndiceAlternativa": 0},
            ],
        ),
        "IRONCLAD_origen_compartido": (
            "IRONCLAD DREADNOUGHT",
            [
                {"Fuente": "Opciones", "IndiceRegla": 1},
                {"Fuente": "Opciones", "IndiceRegla": 2},
            ],
        ),
    }
    Reporte = {}
    for Etiqueta, (Unidad, Pasos) in Casos.items():
        Reporte[Etiqueta] = SimularSustituciones(PorUnidad[Unidad], Pasos)
    Salida.write_text(json.dumps(Reporte, ensure_ascii=False, indent=2), encoding="utf-8")
    for Etiqueta, Resultado in Reporte.items():
        print("{}: {} ({} pasos)".format(Etiqueta, Resultado["Estado"], len(Resultado["Pasos"])))
        for Paso in Resultado["Pasos"]:
            if Paso["Estado"] == "Rechazado":
                print("  Motivo:", Paso["Motivo"])
        print("  Inventario final:", Resultado["InventarioFinal"])
    print("Reporte:", Salida)
