from copy import deepcopy

from app.Procesamiento.ValidadorCruceArmasIndividuales import (
    ValidarCruceArmasIndividuales,
)


def CrearFicha(
    Origen="heavy bolters",
    Tipo="CantidadArmas",
    CantidadArmas=2,
    Inicial=None,
    Alternativas=None,
):
    return {
        "Unidad": "UNIDAD DE PRUEBA",
        "EquipamientoInicial": [{
            "Sujeto": "This model",
            "Elementos": Inicial if Inicial is not None else [
                {"Cantidad": 4, "Nombre": "heavy bolters"}
            ],
        }],
        "InterpretacionRestricciones": {
            "Interpretadas": [{
                "ReglaOriginal": "Regla de prueba",
                "Pagina": 42,
                "Tipo": "Sustitucion",
                "Sujeto": "This model",
                "Restriccion": {
                    "Tipo": Tipo,
                    "CantidadArmas": CantidadArmas,
                },
                "OrigenTexto": Origen,
                "DestinosTexto": Alternativas or ["2 autocannons"],
                "Eleccion": "UnaDeVarias",
            }]
        },
    }


def test_cantidad_armas_exige_cantidad_explicita():
    F = CrearFicha()
    R = ValidarCruceArmasIndividuales([F])[0]
    assert R["Estado"] == "CoincideConInicial"
    assert R["CantidadRequeridaPorAplicacion"] == 2
    assert R["CantidadInicial"] == 4


def test_cantidad_armas_insuficiente_no_es_legalidad():
    F = CrearFicha(Inicial=[{"Cantidad": 1, "Nombre": "heavy bolters"}])
    R = ValidarCruceArmasIndividuales([F])[0]
    assert R["Estado"] == "SinOrigenDemostrable"
    assert R["CantidadInicial"] == 1


def test_cada_arma_con_dos_unidades_disponibles():
    F = CrearFicha(
        Origen="grav-flux bombards", Tipo="CadaArma", CantidadArmas=None,
        Inicial=[{"Cantidad": 2, "Nombre": "grav-flux bombards"}],
        Alternativas=["1 storm cannon"],
    )
    R = ValidarCruceArmasIndividuales([F])[0]
    assert R["Estado"] == "CoincideConInicial"
    assert R["CantidadInicial"] == 2
    assert R["CantidadRequeridaPorAplicacion"] == 1


def test_sustitucion_previa_produce_combi_bolter_condicionalmente():
    F = CrearFicha(
        Origen="heavy plasma cannons", Tipo="CadaArma",
        CantidadArmas=None,
        Inicial=[{"Cantidad": 2, "Nombre": "heavy plasma cannons"}],
        Alternativas=[
            "1 Dreadnought chainfist and 1 combi-bolter",
            "1 twin volkite culverin",
        ],
    )
    Segunda = deepcopy(F["InterpretacionRestricciones"]["Interpretadas"][0])
    Segunda["ReglaOriginal"] = "Combi-bolters can be replaced"
    Segunda["OrigenTexto"] = "combi-bolters"
    Segunda["DestinosTexto"] = ["1 graviton blaster"]
    F["InterpretacionRestricciones"]["Interpretadas"].append(Segunda)

    Primero, Segundo = ValidarCruceArmasIndividuales([F])
    assert Primero["Estado"] == "CoincideConInicial"
    assert Segundo["Estado"] == "DisponibleTrasSustitucionPrevia"
    assert Segundo["CantidadInicial"] == 0
    assert len(Segundo["FuentesPreviasPosibles"]) == 1
    Fuente = Segundo["FuentesPreviasPosibles"][0]
    assert Fuente["Alternativa"] == "1 Dreadnought chainfist and 1 combi-bolter"
    assert Fuente["MaximoPotencial"] == 2
    assert Fuente["IndiceReglaOrigen"] == 0


def test_no_inventa_dependencia_ante_alternativa_no_elegible():
    F = CrearFicha(
        Origen="heavy plasma cannons", Tipo="CadaArma", CantidadArmas=None,
        Inicial=[{"Cantidad": 0, "Nombre": "heavy plasma cannons"}],
        Alternativas=["1 combi-bolter"],
    )
    Segunda = deepcopy(F["InterpretacionRestricciones"]["Interpretadas"][0])
    Segunda["OrigenTexto"] = "combi-bolters"
    F["InterpretacionRestricciones"]["Interpretadas"].append(Segunda)
    Primero, Segundo = ValidarCruceArmasIndividuales([F])
    assert Primero["Estado"] == "SinOrigenDemostrable"
    assert Segundo["Estado"] == "SinOrigenDemostrable"


def test_mantiene_reglas_kratos_distintas_aunque_compartan_encabezado():
    F = CrearFicha()
    F["InterpretacionRestricciones"]["Interpretadas"].append(
        deepcopy(F["InterpretacionRestricciones"]["Interpretadas"][0])
    )
    Resultados = ValidarCruceArmasIndividuales([F])
    assert len(Resultados) == 2
    assert [R["IndiceRegla"] for R in Resultados] == [0, 1]
    assert all(R["Estado"] == "CoincideConInicial" for R in Resultados)


def test_no_modifica_ficha_original():
    F = CrearFicha()
    Antes = deepcopy(F)
    ValidarCruceArmasIndividuales([F])
    assert F == Antes


def test_omite_restricciones_de_otras_familias():
    F = CrearFicha()
    F["InterpretacionRestricciones"]["Interpretadas"][0]["Restriccion"]["Tipo"] = "CualquierCantidad"
    assert ValidarCruceArmasIndividuales([F]) == []
