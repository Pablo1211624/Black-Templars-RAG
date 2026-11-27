from app.Procesamiento.ValidadorCruceEquipo import ValidarCruceInicial


def CrearFicha(Origen, Elementos, Sujeto="This model", Tipo="Sustitucion"):
    return {
        "Unidad": "UNIDAD DE PRUEBA",
        "EquipamientoInicial": [{
            "Sujeto": "This model",
            "Elementos": Elementos,
        }],
        "InterpretacionOpciones": {
            "Estructuradas": [{
                "Tipo": Tipo,
                "Sujeto": Sujeto,
                "OrigenTexto": Origen,
                "Pagina": 10,
                "ReglaOriginal": "Regla de prueba",
            }]
        },
    }


def test_coincide_con_guion_unicode_y_cantidad():
    Ficha = CrearFicha(
        "2 multi-meltas",
        [{"Cantidad": 2, "Nombre": "multi‑meltas"}],
    )
    Resultado = ValidarCruceInicial([Ficha])
    assert Resultado[0]["Estado"] == "CoincideConInicial"


def test_coincide_con_dos_armas_combinadas():
    Ficha = CrearFicha(
        "bolt pistol and Astartes chainsword",
        [
            {"Cantidad": 1, "Nombre": "bolt pistol"},
            {"Cantidad": 1, "Nombre": "Astartes chainsword"},
        ],
    )
    Resultado = ValidarCruceInicial([Ficha])
    assert Resultado[0]["Estado"] == "CoincideConInicial"


def test_no_coincidencia_no_implica_ilegalidad():
    Ficha = CrearFicha(
        "2 twin hellstrike missile launchers",
        [{"Cantidad": 2, "Nombre": "twin hellstrike launchers"}],
    )
    Resultado = ValidarCruceInicial([Ficha])
    assert Resultado[0]["Estado"] == "NoCoincideConInicial"
    assert Resultado[0]["Faltantes"][0]["Inicial"] == 0


def test_excluye_adiciones_y_modelos_especificos():
    FichaAdicion = CrearFicha(
        None, [], Tipo="Adicion"
    )
    FichaOtroModelo = CrearFicha(
        "bolt pistol", [{"Cantidad": 1, "Nombre": "bolt pistol"}],
        Sujeto="The Sergeant",
    )
    assert ValidarCruceInicial([FichaAdicion, FichaOtroModelo]) == []


def test_documenta_alias_en_storm_eagle_sin_cambiar_original():
    Ficha = CrearFicha(
        "2 twin hellstrike missile launchers",
        [{"Cantidad": 2, "Nombre": "twin hellstrike launchers"}],
    )
    Ficha["Unidad"] = "STORM EAGLE GUNSHIP"
    Resultado = ValidarCruceInicial([Ficha])[0]

    assert Resultado["Estado"] == "CoincidePorAliasDocumentado"
    assert Resultado["Faltantes"] == []
    assert Resultado["AliasUtilizados"] == [{
        "NombreRegla": "twin hellstrike missile launchers",
        "NombreInicial": "twin hellstrike launchers",
        "Cantidad": 2,
    }]
    assert Resultado["ReglaOriginal"] == "Regla de prueba"


def test_documenta_alias_en_fire_raptor():
    Ficha = CrearFicha(
        "2 twin hellstrike missile launchers",
        [{"Cantidad": 2, "Nombre": "twin hellstrike launchers"}],
    )
    Ficha["Unidad"] = "FIRE RAPTOR GUNSHIP"
    Resultado = ValidarCruceInicial([Ficha])[0]

    assert Resultado["Estado"] == "CoincidePorAliasDocumentado"


def test_no_aplica_alias_a_otra_unidad_ni_cantidad():
    Otra = CrearFicha(
        "2 twin hellstrike missile launchers",
        [{"Cantidad": 2, "Nombre": "twin hellstrike launchers"}],
    )
    Otra["Unidad"] = "OTRA UNIDAD"
    CantidadDiferente = CrearFicha(
        "1 twin hellstrike missile launchers",
        [{"Cantidad": 2, "Nombre": "twin hellstrike launchers"}],
    )
    CantidadDiferente["Unidad"] = "STORM EAGLE GUNSHIP"

    Resultado = ValidarCruceInicial([Otra, CantidadDiferente])
    assert all(
        R["Estado"] == "NoCoincideConInicial"
        for R in Resultado
    )
