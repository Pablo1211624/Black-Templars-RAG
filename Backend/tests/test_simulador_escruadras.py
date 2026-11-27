"""Pruebas autónomas con minificturas extraídas de las unidades reales.
No requieren PDF ni archivo preprocesos/*.json: son aptas para CI.
"""
from copy import deepcopy
from app.Procesamiento.SimuladorEscuadras import SimularEscuadra

import json

# Recortes de 3 fichas del documento de Space Marines, sin dependencias externas.
FICHAS = json.loads(r'''{"ASSAULT SQUAD":{"Unidad":"ASSAULT SQUAD","Secciones":{"Composicion":[{"Encabezado":"UNIT COMPOSITION","Texto":"■1 Assault Sergeant\n■4-9 Assault Marines\n"}]},"EquipamientoInicial":[{"Sujeto":"Every model","Elementos":[{"Cantidad":1,"Nombre":"bolt pistol"},{"Cantidad":1,"Nombre":"Astartes chainsword"}]}],"InterpretacionRestricciones":{"Interpretadas":[{"ReglaOriginal":"The Assault Sergeant’s bolt pistol can be replaced with one of the following:","Tipo":"Sustitucion","Sujeto":"The Assault Sergeant","Restriccion":{"Tipo":"ModeloEspecifico","Maximo":null,"PorCada":null,"CantidadModelosIndicada":null,"CantidadArmas":null},"OrigenTexto":"bolt pistol","DestinosTexto":["1 grav-pistol*","1 hand flamer*","1 inferno pistol*","1 plasma pistol"]},{"ReglaOriginal":"The Assault Sergeant’s Astartes chainsword can be replaced with one of the following:","Tipo":"Sustitucion","Sujeto":"The Assault Sergeant","Restriccion":{"Tipo":"ModeloEspecifico","Maximo":null,"PorCada":null,"CantidadModelosIndicada":null,"CantidadArmas":null},"OrigenTexto":"Astartes chainsword","DestinosTexto":["1 power fist","1 power weapon","1 thunder hammer"]},{"ReglaOriginal":"Up to 2 Assault Marines can each have their bolt pistol and Astartes chainsword replaced with one of the following:","Tipo":"Sustitucion","Sujeto":"Assault Marines","Restriccion":{"Tipo":"MaximoEnUnidad","Maximo":2,"PorCada":null},"OrigenTexto":"bolt pistol and Astartes chainsword","DestinosTexto":["1 plasma pistol and 1 Astartes chainsword","1 flamer and 1 close combat weapon","1 meltagun and 1 close combat weapon","1 plasma gun and 1 close combat weapon"]},{"ReglaOriginal":"For every 5 models in this unit, 1 model’s Astartes chainsword can be replaced with 1 eviscerator.","Tipo":"Sustitucion","Sujeto":"model","Restriccion":{"Tipo":"PorCadaModelos","Maximo":1,"PorCada":5},"OrigenTexto":"Astartes chainsword","DestinosTexto":["1 eviscerator"]}]}},"RELIC TERMINATOR SQUAD":{"Unidad":"RELIC TERMINATOR SQUAD","Secciones":{"Composicion":[{"Encabezado":"UNIT COMPOSITION","Texto":"■1 Relic Terminator Sergeant\n■4-9 Relic Terminators\n"}]},"EquipamientoInicial":[{"Sujeto":"Every model","Elementos":[{"Cantidad":1,"Nombre":"combi-bolter"},{"Cantidad":1,"Nombre":"power fist"}]}],"InterpretacionRestricciones":{"Interpretadas":[{"ReglaOriginal":"The Relic Terminator Sergeant’s combi-bolter can be replaced with one of the following:","Tipo":"Sustitucion","Sujeto":"The Relic Terminator Sergeant","Restriccion":{"Tipo":"ModeloEspecifico","Maximo":null,"PorCada":null,"CantidadModelosIndicada":null,"CantidadArmas":null},"OrigenTexto":"combi-bolter","DestinosTexto":["1 plasma blaster","1 volkite charger"]},{"ReglaOriginal":"For every 5 models in this unit, 1 Relic Terminator’s combi-bolter can be replaced with one of the following:","Tipo":"Sustitucion","Sujeto":"Relic Terminator","Restriccion":{"Tipo":"PorCadaModelos","Maximo":1,"PorCada":5},"OrigenTexto":"combi-bolter","DestinosTexto":["1 heavy flamer","1 reaper autocannon"]},{"ReglaOriginal":"For every 5 models in this unit, 1 model can be equipped with 1 grenade harness.","Tipo":"Adicion","Sujeto":"model","Restriccion":{"Tipo":"PorCadaModelos","Maximo":1,"PorCada":5},"OrigenTexto":null,"DestinosTexto":["1 grenade harness"]},{"ReglaOriginal":"Any number of models can each have their power fist replaced with 1 power weapon.","Tipo":"Sustitucion","Sujeto":"models","Restriccion":{"Tipo":"CualquierCantidad","Maximo":null,"PorCada":null},"OrigenTexto":"power fist","DestinosTexto":["1 power weapon"]},{"ReglaOriginal":"Any number of models can each have their combi-bolter and power fist replaced with 1 twin lightning claws.","Tipo":"Sustitucion","Sujeto":"models","Restriccion":{"Tipo":"CualquierCantidad","Maximo":null,"PorCada":null},"OrigenTexto":"combi-bolter and power fist","DestinosTexto":["1 twin lightning claws"]}]}},"ASTARTES SERVITORS":{"Unidad":"ASTARTES SERVITORS","Secciones":{"Composicion":[{"Encabezado":"UNIT COMPOSITION","Texto":"■4 Astartes Servitors\n"}]},"EquipamientoInicial":[{"Sujeto":"Every model","Elementos":[{"Cantidad":1,"Nombre":"Servitor servo-arm"}]}],"InterpretacionRestricciones":{"Interpretadas":[{"ReglaOriginal":"Up to 2 models can each have their Servitor servo-arm replaced with one of the following:","Tipo":"Sustitucion","Sujeto":"models","Restriccion":{"Tipo":"MaximoEnUnidad","Maximo":2,"PorCada":null},"OrigenTexto":"Servitor servo-arm","DestinosTexto":["1 heavy bolter and 1 close combat weapon","1 multi-melta and 1 close combat weapon","1 plasma cannon and 1 close combat weapon"]}]}}}''')


def f(nombre):
    return deepcopy(FICHAS[nombre])


def assault(marines=4):
    return ([{"Id": "S", "Tipo": "Assault Sergeant"}]
            + [{"Id": f"M{i}", "Tipo": "Assault Marines"} for i in range(1, marines + 1)])


def paso(modelo, regla, alternativa=None):
    p = {"ModeloId": modelo, "IndiceRegla": regla}
    if alternativa is not None:
        p["IndiceAlternativa"] = alternativa
    return p


def test_composicion_minima_e_inventarios_independientes():
    r = SimularEscuadra(f("ASSAULT SQUAD"), assault(), [paso("S", 1, 0)])
    assert r["Estado"] == "Completada"
    assert "power fist" in r["InventarioFinal"]["S"]
    assert "power fist" not in r["InventarioFinal"]["M1"]
    assert r["InventarioInicial"]["S"] != r["InventarioFinal"]["S"]


def test_por_cada_cinco_no_permita_dos_en_cinco():
    r = SimularEscuadra(f("ASSAULT SQUAD"), assault(), [paso("M1", 3), paso("M2", 3)])
    assert r["Estado"] == "Rechazada"
    assert r["Motivo"] == "LimiteSuperado"
    assert r["InventarioFinal"] == r["InventarioInicial"]


def test_por_cada_cinco_permita_dos_en_diez():
    r = SimularEscuadra(f("ASSAULT SQUAD"), assault(9), [paso("M1", 3), paso("M2", 3)])
    assert r["Estado"] == "Completada"
    assert r["InventarioFinal"]["M1"]["eviscerator"] == 1
    assert r["InventarioFinal"]["M2"]["eviscerator"] == 1


def test_maximo_dos_aplicaciones_en_distintos_modelos():
    r = SimularEscuadra(f("ASSAULT SQUAD"), assault(), [
        paso("M1", 2, 1), paso("M2", 2, 2), paso("M3", 2, 3)
    ])
    assert r["Estado"] == "Rechazada"
    assert r["Motivo"] == "LimiteSuperado"


def test_sargento_no_puede_usar_regla_restringida_a_marines():
    r = SimularEscuadra(f("ASSAULT SQUAD"), assault(), [paso("S", 2, 1)])
    assert r["Motivo"] == "ModeloNoElegible"


def test_dos_reglas_compiten_por_el_mismo_equipo_de_un_modelo():
    r = SimularEscuadra(f("ASSAULT SQUAD"), assault(), [
        paso("M1", 3), paso("M1", 2, 1)
    ])
    assert r["Estado"] == "Rechazada"
    assert r["Motivo"] == "OrigenInsuficiente"
    assert r["InventarioFinal"] == r["InventarioInicial"]


def test_un_modelo_no_repite_misma_regla():
    r = SimularEscuadra(f("ASSAULT SQUAD"), assault(9), [paso("M1", 3), paso("M1", 3)])
    assert r["Motivo"] == "ReglaYaUtilizadaPorModelo"


def test_no_acepta_composicion_fuera_de_rango_ni_id_duplicado():
    ficha = f("ASSAULT SQUAD")
    r1 = SimularEscuadra(ficha, assault(3), [])
    assert r1["Estado"] == "NoEvaluable" and r1["Motivo"] == "CantidadModelosFueraDeRango"
    modelos = assault()
    modelos[1]["Id"] = "S"
    r2 = SimularEscuadra(ficha, modelos, [])
    assert r2["Estado"] == "NoEvaluable" and r2["Motivo"] == "IdDuplicado"


def test_no_aplica_reglas_con_asteriscos_sin_resolver():
    r = SimularEscuadra(f("ASSAULT SQUAD"), assault(), [paso("S", 0, 0)])
    assert r["Estado"] == "Rechazada"
    assert r["Motivo"] == "DestinoNoDesglosable"


def test_adicion_por_cada_cinco_aplica_limite():
    ficha = f("RELIC TERMINATOR SQUAD")
    modelos = ([{"Id": "S", "Tipo": "Relic Terminator Sergeant"}]
               + [{"Id": f"T{i}", "Tipo": "Relic Terminators"} for i in range(1, 5)])
    r = SimularEscuadra(ficha, modelos, [paso("T1", 2)])
    assert r["Estado"] == "Completada"
    assert r["InventarioFinal"]["T1"]["grenade harness"] == 1
    r2 = SimularEscuadra(ficha, modelos, [paso("T1", 2), paso("T2", 2)])
    assert r2["Motivo"] == "LimiteSuperado"


def test_una_de_hasta_dos_servoarms_por_servidores():
    ficha = f("ASTARTES SERVITORS")
    modelos = [{"Id": f"V{i}", "Tipo": "Astartes Servitors"} for i in range(1, 5)]
    r = SimularEscuadra(ficha, modelos, [paso("V1", 0, 0), paso("V2", 0, 1)])
    assert r["Estado"] == "Completada"
    assert r["InventarioFinal"]["V1"]["heavy bolter"] == 1
    assert r["InventarioFinal"]["V2"]["multi-melta"] == 1


def test_no_modifica_parametros():
    ficha = f("ASTARTES SERVITORS")
    modelos = [{"Id": f"V{i}", "Tipo": "Astartes Servitors"} for i in range(1, 5)]
    pasos = [paso("V1", 0, 0)]
    antes = deepcopy((ficha, modelos, pasos))
    SimularEscuadra(ficha, modelos, pasos)
    assert (ficha, modelos, pasos) == antes


def test_cantidad_modelos_indicada_limita_la_regla_a_uno():
    ficha = f("ASSAULT SQUAD")
    regla = ficha["InterpretacionRestricciones"]["Interpretadas"][2]
    regla["Restriccion"] = {
        "Tipo": "ModeloEspecifico",
        "CantidadModelosIndicada": 1,
    }
    regla["Sujeto"] = "1 Assault Marine"
    resultado = SimularEscuadra(ficha, assault(), [
        paso("M1", 2, 1), paso("M2", 2, 2)
    ])
    assert resultado["Motivo"] == "LimiteSuperado"


def test_respeta_limite_total_explicito_de_unit_composition():
    ficha = f("ASSAULT SQUAD")
    ficha["Secciones"]["Composicion"][0]["Encabezado"] = (
        "UNIT COMPOSITION (5 MODELS MAXIMUM)"
    )
    resultado = SimularEscuadra(ficha, assault(5), [])
    assert resultado["Estado"] == "NoEvaluable"
    assert resultado["Motivo"] == "LimiteTotalUnidad"
