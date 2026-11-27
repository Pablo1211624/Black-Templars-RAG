from copy import deepcopy

from app.Procesamiento.SimuladorSustituciones import SimularSustituciones


def ficha(elementos=None, opciones=None, restricciones=None):
    return {
        "Unidad": "PRUEBA",
        "EquipamientoInicial": [{
            "Sujeto": "This model",
            "Elementos": elementos if elementos is not None else [
                {"Cantidad": 4, "Nombre": "heavy bolters"}
            ],
        }],
        "InterpretacionOpciones": {"Estructuradas": opciones or []},
        "InterpretacionRestricciones": {"Interpretadas": restricciones or []},
    }


def regla(origen, alternativas, tipo="CantidadArmas", cantidad=2):
    return {
        "ReglaOriginal": "Ejemplo original",
        "Pagina": 11,
        "Tipo": "Sustitucion",
        "Sujeto": "This model",
        "Restriccion": {"Tipo": tipo, "CantidadArmas": cantidad},
        "OrigenTexto": origen,
        "DestinosTexto": alternativas,
    }


def paso(indice, alternativa=0, fuente="Restricciones"):
    return {
        "Fuente": fuente,
        "IndiceRegla": indice,
        "IndiceAlternativa": alternativa,
    }


def test_dos_reglas_independientes_consumen_cuatro_bolters():
    f = ficha(restricciones=[
        regla("heavy bolters", ["2 autocannons"]),
        regla("heavy bolters", ["2 volkite culverins"]),
    ])
    r = SimularSustituciones(f, [paso(0), paso(1)])
    assert r["Estado"] == "Completada"
    assert r["InventarioFinal"] == {
        "autocannons": 2,
        "volkite culverins": 2,
    }
    assert len(r["Pasos"]) == 2


def test_arma_obtenida_habilita_sustitucion_posterior():
    f = ficha(
        elementos=[{"Cantidad": 2, "Nombre": "heavy plasma cannons"}],
        restricciones=[
            regla("heavy plasma cannons", ["1 Dreadnought chainfist and 1 combi-bolter"], tipo="CadaArma"),
            regla("combi-bolters", ["1 graviton blaster"], tipo="CadaArma"),
        ],
    )
    r = SimularSustituciones(f, [paso(0), paso(1)])
    assert r["Estado"] == "Completada"
    assert r["InventarioFinal"] == {
        "heavy plasma cannons": 1,
        "dreadnought chainfist": 1,
        "graviton blaster": 1,
    }


def test_origen_no_disponible_revierte_toda_la_simulacion():
    f = ficha(restricciones=[
        regla("heavy bolters", ["2 autocannons"]),
        regla("heavy bolters", ["2 volkite culverins"]),
        regla("heavy bolters", ["2 lascannons"]),
    ])
    r = SimularSustituciones(f, [paso(0), paso(1), paso(2)])
    assert r["Estado"] == "Rechazada"
    assert r["ReversionAplicada"]
    assert r["Pasos"][-1]["Motivo"] == "OrigenInsuficiente"
    assert r["InventarioFinal"] == r["InventarioInicial"]
    assert all(c >= 0 for c in r["InventarioFinal"].values())


def test_regla_de_grupo_cantidad_armas_no_se_aplica_dos_veces():
    f = ficha(restricciones=[regla("heavy bolters", ["2 autocannons"])])
    r = SimularSustituciones(f, [paso(0), paso(0)])
    assert r["Estado"] == "Rechazada"
    assert r["Pasos"][-1]["Motivo"] == "ReglaYaUtilizada"


def test_cada_arma_se_puede_aplicar_dos_veces_si_hay_dos():
    f = ficha(
        elementos=[{"Cantidad": 2, "Nombre": "grav-flux bombards"}],
        restricciones=[regla("grav-flux bombards", ["1 storm cannon"], tipo="CadaArma")],
    )
    r = SimularSustituciones(f, [paso(0), paso(0)])
    assert r["Estado"] == "Completada"
    assert r["InventarioFinal"] == {"storm cannon": 2}
    r3 = SimularSustituciones(f, [paso(0), paso(0), paso(0)])
    assert r3["Estado"] == "Rechazada"
    assert r3["Pasos"][-1]["Motivo"] == "OrigenInsuficiente"


def test_alternativas_multiples_requieren_eleccion_explicita():
    f = ficha(restricciones=[regla("heavy bolters", ["2 autocannons", "2 lascannons"])])
    r = SimularSustituciones(f, [{"Fuente": "Restricciones", "IndiceRegla": 0}])
    assert r["Estado"] == "Rechazada"
    assert r["Pasos"][-1]["Motivo"] == "AlternativaInvalida"


def test_rechaza_destino_con_nota_no_resuelta_y_comas():
    for destino in ("2 lascannons*", "1 flamer, 1 plasma cutter and 2 servo-arms"):
        f = ficha(restricciones=[regla("heavy bolters", [destino])])
        r = SimularSustituciones(f, [paso(0)])
        assert r["Estado"] == "Rechazada"
        assert r["Pasos"][-1]["Motivo"] == "DestinoNoDesglosable"


def test_no_modifica_la_ficha_original():
    f = ficha(restricciones=[regla("heavy bolters", ["2 autocannons"])])
    antes = deepcopy(f)
    SimularSustituciones(f, [paso(0)])
    assert f == antes


def test_no_simula_modelos_especificos_ni_adiciones():
    f = ficha(opciones=[{
        "Tipo": "Adicion", "Sujeto": "This model",
        "OrigenTexto": None, "DestinosTexto": ["1 boltgun"],
    }])
    r = SimularSustituciones(f, [paso(0, fuente="Opciones")])
    assert r["Pasos"][-1]["Motivo"] == "TipoNoSoportado"
    f2 = ficha(opciones=[{
        "Tipo": "Sustitucion", "Sujeto": "The Sergeant",
        "OrigenTexto": "heavy bolters", "DestinosTexto": ["1 boltgun"],
    }])
    r2 = SimularSustituciones(f2, [paso(0, fuente="Opciones")])
    assert r2["Pasos"][-1]["Motivo"] == "SujetoNoSoportado"


def test_sin_equipo_inicial_no_inventa_inventario():
    f = ficha()
    f["EquipamientoInicial"] = []
    assert SimularSustituciones(f, [paso(0)])["Estado"] == "NoEvaluable"


def test_sustituciones_directas_compiten_por_misma_arma():
    f = ficha(
        elementos=[{"Cantidad": 1, "Nombre": "storm bolter"}],
        opciones=[
            {"Tipo": "Sustitucion", "Sujeto": "This model", "OrigenTexto": "storm bolter", "DestinosTexto": ["1 hurricane bolter"]},
            {"Tipo": "Sustitucion", "Sujeto": "This model", "OrigenTexto": "storm bolter", "DestinosTexto": ["1 heavy flamer"]},
        ],
    )
    r = SimularSustituciones(f, [paso(0, fuente="Opciones"), paso(1, fuente="Opciones")])
    assert r["Estado"] == "Rechazada"
    assert r["Pasos"][-1]["Motivo"] == "OrigenInsuficiente"
    assert r["InventarioFinal"] == {"storm bolter": 1}
