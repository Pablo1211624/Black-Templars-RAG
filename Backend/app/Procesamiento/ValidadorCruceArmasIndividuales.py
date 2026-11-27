"""Cruce conservador de restricciones CantidadArmas y CadaArma.

No genera configuraciones de ejército ni valida legalidad. Detecta fuentes
posibles de armamento procedente de una elección previa de la misma ficha.
"""

import json
import re
from collections import Counter
from pathlib import Path

from app.Procesamiento.ValidadorCruceEquipo import (
    NormalizarNombre,
    SepararOrigenes,
)


TIPOS_INDIVIDUALES = {"CantidadArmas", "CadaArma"}


def _VariantesPorFlexion(Nombre, Inventario):
    """Devuelve nombre exacto o singular/plural regular; no crea alias léxicos."""
    if Nombre in Inventario:
        return Nombre, False
    if Nombre.endswith("s") and Nombre[:-1] in Inventario:
        return Nombre[:-1], True
    if Nombre + "s" in Inventario:
        return Nombre + "s", True
    return None, False


def _CantidadDisponible(Nombre, Inventario):
    Equivalente, PorFlexion = _VariantesPorFlexion(Nombre, Inventario)
    if Equivalente is None:
        return 0, None
    return Inventario[Equivalente], (
        {"NombreRegla": Nombre, "NombreInventario": Equivalente}
        if PorFlexion else None
    )


def _InventarioInicial(Ficha):
    Declaraciones = [
        D for D in Ficha.get("EquipamientoInicial", [])
        if D.get("Sujeto", "").casefold() == "this model"
    ]
    if len(Declaraciones) != 1:
        return None
    Inventario = Counter()
    for Item in Declaraciones[0].get("Elementos", []):
        Cantidad = Item.get("Cantidad")
        if not isinstance(Cantidad, int) or Cantidad < 0:
            return None
        Inventario[NormalizarNombre(Item["Nombre"])] += Cantidad
    return Inventario


def _Origen(Regla):
    """Extrae una única clase de arma y cantidad por aplicación."""
    Origenes = SepararOrigenes(Regla.get("OrigenTexto"))
    if not Origenes or len(Origenes) != 1:
        return None
    Nombre, CantidadDelTexto = next(iter(Origenes.items()))
    Tipo = Regla.get("Restriccion", {}).get("Tipo")
    if Tipo == "CantidadArmas":
        Cantidad = Regla["Restriccion"].get("CantidadArmas")
        if not isinstance(Cantidad, int) or Cantidad < 1:
            return None
        # Si el origen incluye otra cantidad explícita, no aceptar conflicto.
        if CantidadDelTexto != 1 and CantidadDelTexto != Cantidad:
            return None
        return Nombre, Cantidad
    if Tipo == "CadaArma":
        if CantidadDelTexto != 1:
            return None
        return Nombre, 1
    return None


def _SepararDestino(Alternativa):
    """Solo agrupa enumeraciones explícitas de equipo; elimina notas '*' al final."""
    Texto = re.sub(r"\*{1,3}$", "", Alternativa.strip()).strip()
    if not Texto or re.search(r"\s+or\s+", Texto, flags=re.I):
        return None
    return SepararOrigenes(Texto)


def _BuscarProductores(Reglas, IndiceActual, NombreBuscado, Inventario):
    """Busca producciones directas desde el equipo inicial, en reglas previas.

    Un productor es una posibilidad condicional, nunca equipamiento garantizado.
    No explora secuencias arbitrarias, ciclos ni reglas de modelos distintos.
    """
    Productores = []
    for Indice, Regla in enumerate(Reglas[:IndiceActual]):
        if Regla.get("Tipo") != "Sustitucion":
            continue
        if NormalizarNombre(Regla.get("Sujeto", "")) != "this model":
            continue
        Origen = _Origen(Regla)
        if Origen is None:
            continue
        NombreBase, CantidadBase = Origen
        Disponibles, _ = _CantidadDisponible(NombreBase, Inventario)
        if Disponibles < CantidadBase:
            continue
        Tipo = Regla["Restriccion"]["Tipo"]
        MaxAplicaciones = Disponibles if Tipo == "CadaArma" else 1
        for Alternativa in Regla.get("DestinosTexto", []):
            Destinos = _SepararDestino(Alternativa)
            if not Destinos:
                continue
            Introducida, _ = _CantidadDisponible(NombreBuscado, Destinos)
            if Introducida == 0:
                continue
            Productores.append({
                "IndiceReglaOrigen": Indice,
                "ReglaOrigen": Regla["ReglaOriginal"],
                "Alternativa": Alternativa,
                "CantidadIntroducidaPorAplicacion": Introducida,
                "MaximoPotencial": Introducida * MaxAplicaciones,
            })
    return Productores


def ValidarCruceArmasIndividuales(Fichas):
    """Valida origen inicial o procedencia condicional para 5 reglas especiales."""
    Resultado = []
    for Ficha in Fichas:
        Reglas = Ficha.get("InterpretacionRestricciones", {}).get("Interpretadas", [])
        Inventario = _InventarioInicial(Ficha)
        for Indice, Regla in enumerate(Reglas):
            Tipo = Regla.get("Restriccion", {}).get("Tipo")
            if Tipo not in TIPOS_INDIVIDUALES:
                continue
            Origen = _Origen(Regla)
            Flexion = None
            Disponibles = 0
            FuentesPrevias = []
            if Inventario is None or Origen is None:
                Estado = "NoEvaluable"
                NombreOrigen = None if Origen is None else Origen[0]
                Necesarios = None if Origen is None else Origen[1]
            else:
                NombreOrigen, Necesarios = Origen
                Disponibles, Flexion = _CantidadDisponible(NombreOrigen, Inventario)
                if Disponibles >= Necesarios:
                    Estado = "CoincidePorFlexion" if Flexion else "CoincideConInicial"
                else:
                    FuentesPrevias = _BuscarProductores(
                        Reglas, Indice, NombreOrigen, Inventario
                    )
                    MaximoPotencial = max(
                        (P["MaximoPotencial"] for P in FuentesPrevias), default=0
                    )
                    if MaximoPotencial >= Necesarios:
                        Estado = "DisponibleTrasSustitucionPrevia"
                    else:
                        Estado = "SinOrigenDemostrable"
            Resultado.append({
                "Unidad": Ficha["Unidad"],
                "Pagina": Regla["Pagina"],
                "IndiceRegla": Indice,
                "ReglaOriginal": Regla["ReglaOriginal"],
                "TipoRestriccion": Tipo,
                "Estado": Estado,
                "NombreOrigen": NombreOrigen,
                "CantidadRequeridaPorAplicacion": Necesarios,
                "CantidadInicial": Disponibles,
                "FlexionUtilizada": Flexion,
                "FuentesPreviasPosibles": FuentesPrevias,
            })
    return Resultado


if __name__ == "__main__":
    Entrada = Path("preprocesos/PdfExtraccionFichasReporte.json")
    Salida = Path("preprocesos/ValidacionCruceArmasIndividuales.json")
    Fichas = json.loads(Entrada.read_text(encoding="utf-8"))
    Resultados = ValidarCruceArmasIndividuales(Fichas)
    Salida.write_text(
        json.dumps(Resultados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Reglas examinadas:", len(Resultados))
    print("Estados:", dict(Counter(R["Estado"] for R in Resultados)))
    for Registro in Resultados:
        print("- {}: {} (regla #{})".format(
            Registro["Unidad"], Registro["Estado"], Registro["IndiceRegla"]
        ))
        for Fuente in Registro["FuentesPreviasPosibles"]:
            print("  Posible origen:", Fuente["Alternativa"])
    print("Reporte:", Salida)
