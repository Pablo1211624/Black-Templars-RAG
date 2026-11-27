"""Pruebas autónomas para combinar restricciones y elecciones compuestas.

No necesitan PDF ni el reporte JSON: pueden ejecutarse en CI.
"""
from copy import deepcopy

from app.Procesamiento.SimuladorEscuadras import SimularEscuadra


def ficha(salto=False):
    nombre = "ASSAULT SQUAD WITH JUMP PACKS" if salto else "ASSAULT SQUAD"
    sargento = "Assault Sergeant with Jump Pack" if salto else "Assault Sergeant"
    marines = "Assault Marines with Jump Packs" if salto else "Assault Marines"
    return {
        "Unidad": nombre,
        "Secciones": {"Composicion": [{
            "Encabezado": "UNIT COMPOSITION",
            "Texto": f"■1 {sargento}\n■4-9 {marines}\n",
        }]},
        "EquipamientoInicial": [{
            "Sujeto": "Every model",
            "Elementos": [
                {"Cantidad": 1, "Nombre": "bolt pistol"},
                {"Cantidad": 1, "Nombre": "Astartes chainsword"},
            ],
        }],
        "InterpretacionRestricciones": {"Interpretadas": [{
            "Tipo": "Sustitucion",
            "Sujeto": f"The {sargento}",
            "Restriccion": {"Tipo": "ModeloEspecifico", "CantidadModelosIndicada": None},
            "OrigenTexto": "Astartes chainsword",
            "DestinosTexto": ["1 power fist"],
            "ReglaOriginal": "The Sergeant's Astartes chainsword can be replaced with 1 power fist.",
        }]},
        "InterpretacionCompuestas": {"Compuestas": [{
            "Tipo": "EleccionEntreOperaciones",
            "Sujeto": f"The {sargento}",
            "Eleccion": "UnaDeVarias",
            "ReglaOriginal": f"The {sargento} can do one of the following:",
            "Pagina": 126 if salto else 124,
            "Operaciones": [
                {
                    "Tipo": "Sustitucion",
                    "OrigenTexto": "bolt pistol and Astartes chainsword",
                    "DestinoTexto": "1 twin lightning claws",
                    "TextoOriginal": "Replace its bolt pistol and Astartes chainsword with 1 twin lightning claws.",
                },
                {
                    "Tipo": "Adicion",
                    "OrigenTexto": None,
                    "DestinoTexto": "1 Astartes shield",
                    "TextoOriginal": "Be equipped with 1 Astartes shield.",
                },
            ],
        }]},
    }


def modelos(salto=False):
    return ([{"Id": "S1", "Tipo": "Assault Sergeant with Jump Pack" if salto else "Assault Sergeant"}]
            + [{"Id": f"M{i}", "Tipo": "Assault Marines with Jump Packs" if salto else "Assault Marines"}
               for i in range(1, 5)])


def comp(indice, modelo="S1"):
    return {"ModeloId": modelo, "Fuente": "Compuestas", "IndiceRegla": 0, "IndiceAlternativa": indice}


def restr():
    return {"ModeloId": "S1", "IndiceRegla": 0}


def test_compuesta_sustituye_dos_armas_en_sargento():
    resultado = SimularEscuadra(ficha(), modelos(), [comp(0)])
    assert resultado["Estado"] == "Completada"
    assert resultado["InventarioFinal"]["S1"] == {"twin lightning claws": 1}
    assert resultado["InventarioFinal"]["M1"] == resultado["InventarioInicial"]["M1"]
    assert resultado["Pasos"][0]["Fuente"] == "Compuestas"


def test_compuesta_anade_escudo_sin_consumir_armas():
    resultado = SimularEscuadra(ficha(), modelos(), [comp(1)])
    assert resultado["Estado"] == "Completada"
    assert resultado["InventarioFinal"]["S1"] == {
        "astartes chainsword": 1,
        "astartes shield": 1,
        "bolt pistol": 1,
    }
    assert resultado["Pasos"][0]["Consumido"] == {}


def test_no_puede_escoger_ambas_operaciones_compuestas():
    resultado = SimularEscuadra(ficha(), modelos(), [comp(1), comp(0)])
    assert resultado["Estado"] == "Rechazada"
    assert resultado["Motivo"] == "ReglaYaUtilizadaPorModelo"
    assert resultado["InventarioFinal"] == resultado["InventarioInicial"]
    assert resultado["ReversionAplicada"] is True


def test_marines_no_pueden_usar_opcion_reservada_para_sargento():
    resultado = SimularEscuadra(ficha(), modelos(), [comp(1, "M1")])
    assert resultado["Estado"] == "Rechazada"
    assert resultado["Motivo"] == "ModeloNoElegible"


def test_conflicto_con_sustitucion_previa_revierte_todo():
    resultado = SimularEscuadra(ficha(), modelos(), [restr(), comp(0)])
    assert resultado["Estado"] == "Rechazada"
    assert resultado["Motivo"] == "OrigenInsuficiente"
    assert resultado["InventarioFinal"] == resultado["InventarioInicial"]


def test_adicion_compuesta_y_restriccion_compatibles_tienen_indices_independientes():
    resultado = SimularEscuadra(ficha(), modelos(), [comp(1), restr()])
    assert resultado["Estado"] == "Completada"
    assert resultado["InventarioFinal"]["S1"] == {
        "astartes shield": 1,
        "bolt pistol": 1,
        "power fist": 1,
    }
    assert [p["Fuente"] for p in resultado["Pasos"]] == ["Compuestas", "Restricciones"]


def test_admite_sargento_con_jump_pack():
    resultado = SimularEscuadra(ficha(salto=True), modelos(salto=True), [comp(0)])
    assert resultado["Estado"] == "Completada"
    assert resultado["InventarioFinal"]["S1"] == {"twin lightning claws": 1}


def test_compuesta_requiere_indice_alternativa_explicito():
    paso = {"ModeloId": "S1", "Fuente": "Compuestas", "IndiceRegla": 0}
    resultado = SimularEscuadra(ficha(), modelos(), [paso])
    assert resultado["Motivo"] == "AlternativaInvalida"


def test_compuesta_no_desglosable_rechazada_sin_modificar_datos():
    f, m = ficha(), modelos()
    f["InterpretacionCompuestas"]["Compuestas"][0]["Operaciones"][1]["DestinoTexto"] = "1 shield*"
    p = [comp(1)]
    original = deepcopy((f, m, p))
    resultado = SimularEscuadra(f, m, p)
    assert resultado["Motivo"] == "DestinoNoDesglosable"
    assert (f, m, p) == original
    assert resultado["InventarioFinal"] == resultado["InventarioInicial"]


def test_fuente_desconocida_rechazada_sin_confusion():
    paso = {**comp(1), "Fuente": "Inventada"}
    resultado = SimularEscuadra(ficha(), modelos(), [paso])
    assert resultado["Motivo"] == "FuenteNoSoportada"


def test_regla_compuesta_malformada_no_se_ejecuta():
    f = ficha()
    f["InterpretacionCompuestas"]["Compuestas"][0]["Eleccion"] = "Todas"
    resultado = SimularEscuadra(f, modelos(), [comp(1)])
    assert resultado["Motivo"] == "TipoNoSoportado"
