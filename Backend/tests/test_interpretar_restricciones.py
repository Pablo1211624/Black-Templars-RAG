
from app.Procesamiento.InterpretadorRestricciones import (
    InterpretarRestricciones
)


def CrearRegla(Texto, Alternativas=None):
    return [{
        "ReglaOriginal": Texto,
        "Pagina": 30,
        "Alternativas": Alternativas or [],
    }]


def test_cualquier_cantidad_de_modelos():
    Reglas = CrearRegla(
        "Any number of models can each have their "
        "thunder hammer and storm shield replaced with "
        "1 twin lightning claws."
    )

    Resultado = InterpretarRestricciones(Reglas)

    Regla = Resultado["Interpretadas"][0]

    assert Regla["Restriccion"]["Tipo"] == "CualquierCantidad"
    assert Regla["Sujeto"] == "models"
    assert Regla["OrigenTexto"] == "thunder hammer and storm shield"
    assert Regla["DestinosTexto"] == ["1 twin lightning claws"]


def test_posesivo_plural_con_alternativas():
    Reglas = CrearRegla(
        "Any number of Veteran Bikers’ bolt pistols "
        "can each be replaced with one of the following:",
        ["1 boltgun", "1 plasma pistol"],
    )

    Resultado = InterpretarRestricciones(Reglas)
    Regla = Resultado["Interpretadas"][0]

    assert Regla["Sujeto"] == "Veteran Bikers"
    assert Regla["OrigenTexto"] == "bolt pistols"
    assert Regla["Eleccion"] == "UnaDeVarias"


def test_limite_maximo_de_modelos():
    Reglas = CrearRegla(
        "Up to 2 models can each have their Servitor "
        "servo-arm replaced with one of the following:",
        ["1 plasma cannon", "1 multi-melta"],
    )

    Resultado = InterpretarRestricciones(Reglas)
    Regla = Resultado["Interpretadas"][0]

    assert Regla["Restriccion"]["Tipo"] == "MaximoEnUnidad"
    assert Regla["Restriccion"]["Maximo"] == 2


def test_restriccion_proporcional():
    Reglas = CrearRegla(
        "For every 5 models in this unit, 1 model’s "
        "Astartes chainsword can be replaced with "
        "1 eviscerator."
    )

    Resultado = InterpretarRestricciones(Reglas)
    Regla = Resultado["Interpretadas"][0]

    assert Regla["Restriccion"]["Tipo"] == "PorCadaModelos"
    assert Regla["Restriccion"]["PorCada"] == 5
    assert Regla["Restriccion"]["Maximo"] == 1
    assert Regla["Tipo"] == "Sustitucion"


def test_adicion_proporcional():
    Reglas = CrearRegla(
        "For every 5 models in this unit, 1 model "
        "can be equipped with 1 grenade harness."
    )

    Resultado = InterpretarRestricciones(Reglas)
    Regla = Resultado["Interpretadas"][0]

    assert Regla["Tipo"] == "Adicion"
    assert Regla["Restriccion"]["PorCada"] == 5
    assert Regla["DestinosTexto"] == ["1 grenade harness"]


def test_texto_ambiguo_permanece_pendiente():
    Reglas = CrearRegla(
        "Any number of models can each have their "
        "power fist replaced with one 1 chainfist."
    )

    Resultado = InterpretarRestricciones(Reglas)

    assert Resultado["Interpretadas"] == []
    assert len(Resultado["Pendientes"]) == 1


def test_modelo_especifico_con_alternativas():
    Reglas = CrearRegla(
        "The Veteran Biker Sergeant’s bolt pistol can be "
        "replaced with one of the following:",
        ["1 boltgun", "1 combi-weapon", "1 plasma pistol"],
    )

    Resultado = InterpretarRestricciones(Reglas)

    assert Resultado["Pendientes"] == []

    Regla = Resultado["Interpretadas"][0]

    assert Regla["Restriccion"]["Tipo"] == "ModeloEspecifico"
    assert Regla["Sujeto"] == "The Veteran Biker Sergeant"
    assert Regla["OrigenTexto"] == "bolt pistol"
    assert len(Regla["DestinosTexto"]) == 3
    assert Regla["Eleccion"] == "UnaDeVarias"


def test_modelo_especifico_con_cantidad():
    Reglas = CrearRegla(
        "1 Scout Sniper’s scout sniper rifle can be "
        "replaced with 1 missile launcher."
    )

    Resultado = InterpretarRestricciones(Reglas)

    Regla = Resultado["Interpretadas"][0]

    assert Regla["Sujeto"] == "1 Scout Sniper"
    assert Regla["Restriccion"]["CantidadModelosIndicada"] == 1
    assert Regla["DestinosTexto"] == ["1 missile launcher"]


def test_modelo_indefinido_con_sustitucion():
    Reglas = CrearRegla(
        "An Attack Bike’s heavy bolter can be "
        "replaced with 1 multi-melta."
    )

    Resultado = InterpretarRestricciones(Reglas)

    Regla = Resultado["Interpretadas"][0]

    assert Regla["Sujeto"] == "An Attack Bike"
    assert Regla["OrigenTexto"] == "heavy bolter"
    assert Regla["Restriccion"]["Tipo"] == "ModeloEspecifico"


def test_cantidad_concreta_de_armas():
    Reglas = CrearRegla(
        "2 of this model’s heavy bolters can be "
        "replaced with one of the following:",
        ["2 autocannons", "2 lascannons"],
    )

    Resultado = InterpretarRestricciones(Reglas)

    Regla = Resultado["Interpretadas"][0]

    assert Regla["Restriccion"]["Tipo"] == "CantidadArmas"
    assert Regla["Restriccion"]["CantidadArmas"] == 2
    assert Regla["OrigenTexto"] == "heavy bolters"
    assert Regla["Eleccion"] == "UnaDeVarias"


def test_sustitucion_individual_de_cada_arma():
    Reglas = CrearRegla(
        "Each of this model’s grav-flux bombards can be "
        "replaced with one of the following:",
        [
            "1 cyclonic melta lance",
            "1 storm cannon",
            "1 meltagun and 1 Leviathan siege claw",
        ],
    )

    Resultado = InterpretarRestricciones(Reglas)

    Regla = Resultado["Interpretadas"][0]

    assert Regla["Restriccion"]["Tipo"] == "CadaArma"
    assert Regla["Sujeto"] == "This model"
    assert len(Regla["DestinosTexto"]) == 3
    assert Regla["DestinosTexto"][2] == (
        "1 meltagun and 1 Leviathan siege claw"
    )


def test_instruccion_compuesta_permanece_pendiente():
    Reglas = CrearRegla(
        "The Assault Sergeant can do one of the following:",
        [
            "Replace its bolt pistol and Astartes chainsword "
            "with 1 twin lightning claws.",
            "Be equipped with 1 Astartes shield.",
        ],
    )

    Resultado = InterpretarRestricciones(Reglas)

    assert Resultado["Interpretadas"] == []
    assert len(Resultado["Pendientes"]) == 1
