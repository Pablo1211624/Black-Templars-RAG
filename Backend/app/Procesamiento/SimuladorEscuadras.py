"""Simula cambios de equipo en una escuadra elegida explícitamente.

Admite reglas ya interpretadas en InterpretacionRestricciones de las familias
ModeloEspecifico, CualquierCantidad, MaximoEnUnidad y PorCadaModelos;
también las elecciones de InterpretacionCompuestas.Compuestas.

NO certifica legalidad de Warhammer 40K: no interpreta reglas pendientes,
notas *, restricciones cruzadas, costes, ni otras reglas de composición.
El resultado nunca modifica la ficha ni los argumentos del llamador.
"""

import json
import re
from collections import Counter
from pathlib import Path

from app.Procesamiento.ValidadorCruceEquipo import NormalizarNombre, SepararOrigenes
from app.Procesamiento.ValidadorCruceGrupos import ExtraerGruposComposicion
from app.Procesamiento.ValidadorCruceModelos import AplicaDeclaracion, ClaveModelo
from app.Procesamiento.SimuladorSustituciones import _Destino, _NombreEnInventario, _Limpiar


TIPOS = {"ModeloEspecifico", "CualquierCantidad", "MaximoEnUnidad", "PorCadaModelos"}


def _ElegirDeclaracion(Ficha, Clave):
    Candidatas = [
        D for D in Ficha.get("EquipamientoInicial", [])
        if AplicaDeclaracion(D.get("Sujeto", ""), Clave)
    ]
    Especificas = [
        D for D in Candidatas
        if NormalizarNombre(D.get("Sujeto", "")) != "every model"
    ]
    if len(Especificas) == 1:
        return Especificas[0]
    if not Especificas and len(Candidatas) == 1:
        return Candidatas[0]
    return None


def _Preparar(Ficha, Modelos):
    """Requiere un ID por miniatura y todos los grupos declarados."""
    Grupos = ExtraerGruposComposicion(Ficha)
    if not Grupos or not isinstance(Modelos, list) or not Modelos:
        return None, "ComposicionNoEvaluable"
    PorTipo = {G["Clave"]: G for G in Grupos}
    if len(PorTipo) != len(Grupos):
        return None, "GruposAmbiguos"

    Inventarios, Tipos, Contadores = {}, {}, Counter()
    for Modelo in Modelos:
        if not isinstance(Modelo, dict):
            return None, "ModeloInvalido"
        Id = Modelo.get("Id")
        Nombre = Modelo.get("Tipo")
        if not isinstance(Id, str) or not Id.strip() or not isinstance(Nombre, str):
            return None, "ModeloInvalido"
        Clave = ClaveModelo(Nombre)
        if Id in Inventarios:
            return None, "IdDuplicado"
        if Clave not in PorTipo:
            return None, "ModeloFueraDeComposicion"
        D = _ElegirDeclaracion(Ficha, Clave)
        if D is None:
            return None, "EquipamientoNoEvaluable"
        Inventario = Counter()
        for E in D.get("Elementos", []):
            Cantidad = E.get("Cantidad")
            NombreArma = E.get("Nombre", "")
            if type(Cantidad) is not int or Cantidad <= 0 or not isinstance(NombreArma, str):
                return None, "EquipamientoNoEvaluable"
            Normalizado = NormalizarNombre(NombreArma)
            if not Normalizado:
                return None, "EquipamientoNoEvaluable"
            Inventario[Normalizado] += Cantidad
        Inventarios[Id] = Inventario
        Tipos[Id] = Clave
        Contadores[Clave] += 1

    for Clave, Grupo in PorTipo.items():
        if not Grupo["Minimo"] <= Contadores[Clave] <= Grupo["Maximo"]:
            return None, "CantidadModelosFueraDeRango"

    # Límite total explícito de UNIT COMPOSITION (N MODELS MAXIMUM).
    for Bloque in Ficha.get("Secciones", {}).get("Composicion", []):
        Texto = Bloque.get("Encabezado", "")
        Maximo = re.search(r"\((\d+)\s+MODELS?\s+MAXIMUM\)", Texto, re.I)
        if Maximo and len(Modelos) > int(Maximo.group(1)):
            return None, "LimiteTotalUnidad"

    return (Inventarios, Tipos, Grupos), None


def _LimpiarEscuadra(Inventarios):
    return {Id: _Limpiar(Inventario) for Id, Inventario in sorted(Inventarios.items())}


def _Limite(Regla, CantidadModelos):
    R = Regla["Restriccion"]
    Tipo = R.get("Tipo")
    if Tipo == "MaximoEnUnidad":
        Limite = R.get("Maximo")
    elif Tipo == "PorCadaModelos":
        PorCada, Maximo = R.get("PorCada"), R.get("Maximo")
        if type(PorCada) is not int or PorCada <= 0 or type(Maximo) is not int or Maximo <= 0:
            return None
        Limite = (CantidadModelos // PorCada) * Maximo
    elif Tipo == "ModeloEspecifico":
        Limite = R.get("CantidadModelosIndicada")
        if Limite is None:
            return CantidadModelos  # Máximo una vez por miniatura: comprobar aparte.
    elif Tipo == "CualquierCantidad":
        Limite = CantidadModelos
    else:
        return None
    return Limite if type(Limite) is int and Limite >= 0 else None


def SimularEscuadra(Ficha, Modelos, Pasos):
    """Pasos: {"ModeloId":"M1", "IndiceRegla":N, "IndiceAlternativa":M}.

    `Fuente` puede ser "Restricciones" (predeterminado) o "Compuestas".
    `IndiceRegla` indexa la lista de reglas de la fuente seleccionada.
    `IndiceAlternativa` elige una alternativa o una operación compuesta.
    Cada regla se aplica a lo sumo una vez por miniatura; máximos y proporciones
    se cuentan entre todas las miniaturas de esta simulación.
    """
    Preparado, MotivoPreparacion = _Preparar(Ficha, Modelos)
    Resultado = {
        "Unidad": Ficha.get("Unidad"),
        "Estado": "NoEvaluable" if Preparado is None else "Completada",
        "Motivo": MotivoPreparacion,
        "InventarioInicial": None,
        "InventarioFinal": None,
        "Pasos": [],
        "ReversionAplicada": False,
        "Alcance": "Solo reglas grupales interpretadas y cantidad de equipo; no certifica legalidad",
    }
    if Preparado is None:
        return Resultado
    Inicial, Tipos, Grupos = Preparado
    Resultado["InventarioInicial"] = _LimpiarEscuadra(Inicial)
    Resultado["InventarioFinal"] = _LimpiarEscuadra(Inicial)
    if not isinstance(Pasos, list):
        Resultado.update({"Estado": "NoEvaluable", "Motivo": "PasosInvalidos"})
        return Resultado

    Inventarios = {Id: Inv.copy() for Id, Inv in Inicial.items()}
    Reglas = Ficha.get("InterpretacionRestricciones", {}).get("Interpretadas", [])
    Compuestas = Ficha.get("InterpretacionCompuestas", {}).get("Compuestas", [])
    UsosRegla = Counter()
    UsosModeloRegla = set()
    Total = len(Modelos)

    for Numero, Paso in enumerate(Pasos, start=1):
        Registro = {"Paso": Numero, "Estado": "Rechazado"}
        Motivo = None
        if not isinstance(Paso, dict):
            Motivo = "PasoInvalido"
        else:
            Id, Indice = Paso.get("ModeloId"), Paso.get("IndiceRegla")
            Fuente = Paso.get("Fuente", "Restricciones")
            Registro.update({"ModeloId": Id, "IndiceRegla": Indice, "Fuente": Fuente})
            if not isinstance(Id, str) or Id not in Inventarios:
                Motivo = "ModeloNoEncontrado"
            elif Fuente not in {"Restricciones", "Compuestas"}:
                Motivo = "FuenteNoSoportada"
            else:
                Lista = Reglas if Fuente == "Restricciones" else Compuestas
                if type(Indice) is not int or not 0 <= Indice < len(Lista):
                    Motivo = "ReglaNoEncontrada"
                else:
                    Regla = Lista[Indice]
                    Sujeto = ClaveModelo(Regla.get("Sujeto", ""))
                    ClaveUso = (Fuente, Indice, Id)
                    ClaveRegla = (Fuente, Indice)
                    EsCompuesta = Fuente == "Compuestas"
                    if EsCompuesta:
                        TipoSoportado = (
                            Regla.get("Tipo") == "EleccionEntreOperaciones"
                            and Regla.get("Eleccion") == "UnaDeVarias"
                            and isinstance(Regla.get("Operaciones"), list)
                            and len(Regla["Operaciones"]) >= 2
                        )
                    else:
                        TipoSoportado = (
                            Regla.get("Restriccion", {}).get("Tipo") in TIPOS
                            and Regla.get("Tipo") in {"Sustitucion", "Adicion"}
                        )

                    if not TipoSoportado:
                        Motivo = "TipoNoSoportado"
                    elif EsCompuesta and Sujeto != Tipos[Id]:
                        Motivo = "ModeloNoElegible"
                    elif not EsCompuesta and Sujeto not in {"model", "models", Tipos[Id]}:
                        Motivo = "ModeloNoElegible"
                    elif ClaveUso in UsosModeloRegla:
                        Motivo = "ReglaYaUtilizadaPorModelo"
                    else:
                        # En estas fichas, la elección compuesta afecta a un modelo
                        # específico, por lo que no añadimos un límite de grupo ficticio.
                        Limite = (
                            sum(T == Sujeto for T in Tipos.values())
                            if EsCompuesta else _Limite(Regla, Total)
                        )
                        if Limite is None:
                            Motivo = "LimiteNoEvaluable"
                        elif UsosRegla[ClaveRegla] >= Limite:
                            Motivo = "LimiteSuperado"
                        else:
                            Alternativas = (
                                Regla["Operaciones"] if EsCompuesta
                                else Regla.get("DestinosTexto", [])
                            )
                            Alternativa = Paso.get("IndiceAlternativa")
                            if (not EsCompuesta and Alternativa is None
                                    and len(Alternativas) == 1):
                                Alternativa = 0
                            if (type(Alternativa) is not int or
                                    not 0 <= Alternativa < len(Alternativas)):
                                Motivo = "AlternativaInvalida"
                            else:
                                Registro["IndiceAlternativa"] = Alternativa
                                Operacion = Alternativas[Alternativa] if EsCompuesta else Regla
                                TipoOperacion = Operacion.get("Tipo")
                                if EsCompuesta:
                                    DestinoTexto = Operacion.get("DestinoTexto")
                                    OrigenTexto = Operacion.get("OrigenTexto")
                                    TextoAlternativa = Operacion.get("TextoOriginal")
                                else:
                                    DestinoTexto = Alternativas[Alternativa]
                                    OrigenTexto = Regla.get("OrigenTexto")
                                    TextoAlternativa = DestinoTexto
                                if TipoOperacion not in {"Sustitucion", "Adicion"}:
                                    Motivo = "TipoNoSoportado"
                                else:
                                    Altas = _Destino(DestinoTexto) if isinstance(DestinoTexto, str) else None
                                    Origenes = (
                                        SepararOrigenes(OrigenTexto)
                                        if TipoOperacion == "Sustitucion" else Counter()
                                    )
                                    if Altas is None:
                                        Motivo = "DestinoNoDesglosable"
                                    elif (Origenes is None or
                                          (TipoOperacion == "Sustitucion" and not Origenes)):
                                        Motivo = "OrigenAmbiguo"
                                    elif TipoOperacion == "Adicion" and OrigenTexto is not None:
                                        Motivo = "OrigenAmbiguo"
                                    else:
                                        Inventario = Inventarios[Id]
                                        Consumos = Counter()
                                        for Nombre, Cantidad in Origenes.items():
                                            Consumos[_NombreEnInventario(Nombre, Inventario)] += Cantidad
                                        Faltantes = {
                                            Nombre: {"Necesario": Cantidad, "Disponible": Inventario[Nombre]}
                                            for Nombre, Cantidad in Consumos.items()
                                            if Inventario[Nombre] < Cantidad
                                        }
                                        if Faltantes:
                                            Motivo = "OrigenInsuficiente"
                                            Registro["Faltantes"] = Faltantes
                                        else:
                                            # Modificar una copia para garantizar reversión atómica.
                                            Nuevo = Inventario.copy()
                                            for Nombre, Cantidad in Consumos.items():
                                                Nuevo[Nombre] -= Cantidad
                                            Incorporadas = Counter()
                                            for Nombre, Cantidad in Altas.items():
                                                Incorporadas[_NombreEnInventario(Nombre, Nuevo)] += Cantidad
                                            for Nombre, Cantidad in Incorporadas.items():
                                                Nuevo[Nombre] += Cantidad
                                            Inventarios[Id] = Nuevo
                                            UsosModeloRegla.add(ClaveUso)
                                            UsosRegla[ClaveRegla] += 1
                                            Registro.update({
                                                "Estado": "Aplicado",
                                                "ReglaOriginal": Regla["ReglaOriginal"],
                                                "AlternativaElegida": TextoAlternativa,
                                                "Consumido": dict(Consumos),
                                                "Anadido": dict(Incorporadas),
                                                "InventarioTrasPaso": _Limpiar(Nuevo),
                                                "UsosReglaEnUnidad": UsosRegla[ClaveRegla],
                                                "LimiteReglaEnUnidad": Limite,
                                            })
        Resultado["Pasos"].append(Registro)
        if Motivo:
            Registro["Motivo"] = Motivo
            Resultado.update({
                "Estado": "Rechazada",
                "Motivo": Motivo,
                "InventarioFinal": _LimpiarEscuadra(Inicial),
                "ReversionAplicada": True,
            })
            return Resultado

    Resultado["InventarioFinal"] = _LimpiarEscuadra(Inventarios)
    return Resultado


def _ModelosDeDemostracion(Sergeant, Marines):
    return (
        [{"Id": "S1", "Tipo": Sergeant}]
        + [{"Id": f"M{i}", "Tipo": "Assault Marines"} for i in range(1, Marines + 1)]
    )


if __name__ == "__main__":
    Entrada = Path("preprocesos/PdfExtraccionFichasReporte.json")
    Salida = Path("preprocesos/SimulacionesEscuadras.json")
    Fichas = json.loads(Entrada.read_text(encoding="utf-8"))
    PorUnidad = {F["Unidad"]: F for F in Fichas}

    Unidad = PorUnidad["ASSAULT SQUAD"]
    Modelos5 = _ModelosDeDemostracion("Assault Sergeant", 4)
    Modelos10 = _ModelosDeDemostracion("Assault Sergeant", 9)
    Casos = {
        "ASSAULT_5_un_eviscerator": (Unidad, Modelos5, [{"ModeloId": "M1", "IndiceRegla": 3}]),
        "ASSAULT_5_dos_eviscerators": (Unidad, Modelos5, [
            {"ModeloId": "M1", "IndiceRegla": 3},
            {"ModeloId": "M2", "IndiceRegla": 3},
        ]),
        "ASSAULT_10_dos_eviscerators": (Unidad, Modelos10, [
            {"ModeloId": "M1", "IndiceRegla": 3},
            {"ModeloId": "M2", "IndiceRegla": 3},
        ]),
        "ASSAULT_5_hasta_dos": (Unidad, Modelos5, [
            {"ModeloId": "M1", "IndiceRegla": 2, "IndiceAlternativa": 1},
            {"ModeloId": "M2", "IndiceRegla": 2, "IndiceAlternativa": 2},
        ]),
    }
    # Demostración adicional: una única elección entre operaciones distintas.
    Sargento = "S1"
    EscuadraJump = PorUnidad["ASSAULT SQUAD WITH JUMP PACKS"]
    ModelosJump = (
        [{"Id": Sargento, "Tipo": "Assault Sergeant with Jump Pack"}]
        + [{"Id": f"M{i}", "Tipo": "Assault Marines with Jump Packs"} for i in range(1, 5)]
    )
    PasoGarras = {"ModeloId": Sargento, "Fuente": "Compuestas", "IndiceRegla": 0, "IndiceAlternativa": 0}
    PasoEscudo = {"ModeloId": Sargento, "Fuente": "Compuestas", "IndiceRegla": 0, "IndiceAlternativa": 1}
    ModelosSargento = [{"Id": Sargento, "Tipo": "Assault Sergeant"}] + [
        {"Id": f"M{i}", "Tipo": "Assault Marines"} for i in range(1, 5)
    ]
    Casos.update({
        "ASSAULT_sargento_garras": (Unidad, ModelosSargento, [PasoGarras]),
        "ASSAULT_sargento_escudo": (Unidad, ModelosSargento, [PasoEscudo]),
        "ASSAULT_sargento_ambas": (Unidad, ModelosSargento, [PasoEscudo, PasoGarras]),
        "ASSAULT_sargento_conflicto": (Unidad, ModelosSargento, [
            {"ModeloId": Sargento, "IndiceRegla": 1, "IndiceAlternativa": 0},
            PasoGarras,
        ]),
        "JUMP_sargento_garras": (EscuadraJump, ModelosJump, [PasoGarras]),
    })
    Reporte = {Nombre: SimularEscuadra(*Args) for Nombre, Args in Casos.items()}
    Salida.write_text(json.dumps(Reporte, ensure_ascii=False, indent=2), encoding="utf-8")
    for Nombre, R in Reporte.items():
        print(f"{Nombre}: {R['Estado']} ({len(R['Pasos'])} pasos)")
        if R["Motivo"]:
            print("  Motivo:", R["Motivo"])
    print("Reporte:", Salida)
