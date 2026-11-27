from app.Procesamiento.ValidadorCruceGrupos import ValidarCruceGrupos


def CrearFicha(
    Composicion="■1 Assault Sergeant\n■4-9 Assault Marines",
    Declaraciones=None,
    Sujeto="models",
    Origen="bolt pistol",
    Tipo="CualquierCantidad",
    Operacion="Sustitucion",
    Maximo=None,
    PorCada=None,
):
    if Declaraciones is None:
        Declaraciones = [{
            "Sujeto": "Every model",
            "Elementos": [{"Cantidad": 1, "Nombre": "bolt pistol"}],
        }]
    return {
        "Unidad": "UNIDAD DE PRUEBA",
        "Secciones": {"Composicion": [{"Texto": Composicion}]},
        "EquipamientoInicial": Declaraciones,
        "InterpretacionRestricciones": {
            "Interpretadas": [{
                "Tipo": Operacion,
                "Pagina": 20,
                "Sujeto": Sujeto,
                "OrigenTexto": Origen,
                "ReglaOriginal": "Regla grupal de prueba",
                "Restriccion": {
                    "Tipo": Tipo,
                    "Maximo": Maximo,
                    "PorCada": PorCada,
                },
            }]
        },
    }


def test_any_number_comprueba_todos_los_modelos():
    R = ValidarCruceGrupos([CrearFicha()])[0]
    assert R["Estado"] == "CoincideConInicial"
    assert len(R["ModelosElegibles"]) == 2
    assert R["TotalModelosUnidad"] == {"Minimo": 5, "Maximo": 10}
    assert all(E["DeclaracionUtilizada"] == "Every model" for E in R["ModelosElegibles"])


def test_hasta_dos_modelos_no_incluye_sargento():
    F = CrearFicha(Sujeto="Assault Marines", Tipo="MaximoEnUnidad", Maximo=2)
    R = ValidarCruceGrupos([F])[0]
    assert R["Estado"] == "CoincideConInicial"
    assert R["Restriccion"]["Maximo"] == 2
    assert [E["Modelo"] for E in R["ModelosElegibles"]] == ["Assault Marines"]
    assert R["ModelosElegibles"][0]["Maximo"] == 9


def test_por_cada_cinco_conserva_formula_sin_fijar_tamano():
    F = CrearFicha(Sujeto="model", Tipo="PorCadaModelos", PorCada=5, Maximo=1)
    R = ValidarCruceGrupos([F])[0]
    assert R["Estado"] == "CoincideConInicial"
    assert R["Restriccion"]["PorCada"] == 5
    assert R["Restriccion"]["Maximo"] == 1
    assert R["TotalModelosUnidad"] == {"Minimo": 5, "Maximo": 10}


def test_reconoce_plural_de_arma_sin_inventar_alias():
    F = CrearFicha(
        Composicion="■1 Veteran Biker Sergeant\n■1-4 Veteran Bikers",
        Sujeto="Veteran Bikers",
        Origen="bolt pistols",
    )
    R = ValidarCruceGrupos([F])[0]
    assert R["Estado"] == "CoincidePorFlexion"
    assert R["ModelosElegibles"][0]["Flexiones"][0] == {
        "NombreRegla": "bolt pistols",
        "NombreInicial": "bolt pistol",
    }


def test_adicion_no_necesita_arma_de_origen():
    F = CrearFicha(Tipo="PorCadaModelos", Operacion="Adicion", Origen=None,
                   Maximo=1, PorCada=5)
    R = ValidarCruceGrupos([F])[0]
    assert R["Estado"] == "AdicionSinOrigen"
    assert all(E["Estado"] == "AdicionSinOrigen" for E in R["ModelosElegibles"])


def test_sujeto_que_no_figura_en_composicion_no_se_supone_existente():
    F = CrearFicha(Sujeto="Captain")
    R = ValidarCruceGrupos([F])[0]
    assert R["Estado"] == "SujetoNoIdentificado"
    assert R["ModelosElegibles"] == []
