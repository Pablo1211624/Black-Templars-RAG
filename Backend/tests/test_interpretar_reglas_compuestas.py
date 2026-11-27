
from app.Procesamiento.InterpretadorReglasCompuestas import (
    InterpretarReglasCompuestas
)


def CrearRegla(Texto, Alternativas):
    return [{
        "ReglaOriginal": Texto,
        "Pagina": 124,
        "Alternativas": Alternativas,
    }]


def test_interpreta_eleccion_compuesta():
    Reglas = CrearRegla(
        "The Assault Sergeant can do one of the following:",
        [
            "Replace its bolt pistol and Astartes chainsword "
            "with 1 twin lightning claws.",
            "Be equipped with 1 Astartes shield.",
        ],
    )

    Resultado = InterpretarReglasCompuestas(Reglas)

    assert Resultado["Pendientes"] == []
    assert len(Resultado["Compuestas"]) == 1

    Regla = Resultado["Compuestas"][0]

    assert Regla["Eleccion"] == "UnaDeVarias"
    assert Regla["Sujeto"] == "The Assault Sergeant"
    assert len(Regla["Operaciones"]) == 2


def test_distingue_sustitucion_y_adicion():
    Reglas = CrearRegla(
        "The Assault Sergeant can do one of the following:",
        [
            "Replace its bolt pistol and Astartes chainsword "
            "with 1 twin lightning claws.",
            "Be equipped with 1 Astartes shield.",
        ],
    )

    Resultado = InterpretarReglasCompuestas(Reglas)
    Operaciones = Resultado["Compuestas"][0]["Operaciones"]

    assert Operaciones[0]["Tipo"] == "Sustitucion"
    assert Operaciones[0]["OrigenTexto"] == (
        "bolt pistol and Astartes chainsword"
    )
    assert Operaciones[1]["Tipo"] == "Adicion"
    assert Operaciones[1]["DestinoTexto"] == (
        "1 Astartes shield"
    )


def test_no_inventa_operaciones():
    Reglas = CrearRegla(
        "The Sergeant can do one of the following:",
        [
            "Replace its bolt pistol with 1 plasma pistol.",
            "Perform an unknown operation.",
        ],
    )

    Resultado = InterpretarReglasCompuestas(Reglas)

    assert Resultado["Compuestas"] == []
    assert len(Resultado["Pendientes"]) == 1


def test_no_modifica_reglas_con_errores():
    Reglas = CrearRegla(
        "This model’s 2 lascannons can be replaced "
        "with on of the following:",
        ["2 heavy bolters", "2 heavy flamers"],
    )

    Resultado = InterpretarReglasCompuestas(Reglas)

    assert Resultado["Compuestas"] == []
    assert Resultado["Pendientes"][0] == Reglas[0]
