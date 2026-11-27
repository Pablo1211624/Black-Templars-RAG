
from app.Procesamiento.InterpretadorOpciones import (
    InterpretarOpciones
)


def CrearOpciones(Regla, Alternativas=None):
    return {
        "Reglas": [{
            "Regla": Regla,
            "Alternativas": Alternativas or [],
            "Pagina": 30,
        }],
        "Notas": [],
        "DeclaraNinguna": False,
    }


def test_sustitucion_directa():
    Opciones = CrearOpciones(
        "This model can have its 1 onslaught gatling cannon "
        "replaced with 1 heavy flamer."
    )

    Resultado, Revision = InterpretarOpciones(Opciones)

    assert Revision is False

    Regla = Resultado["Estructuradas"][0]

    assert Regla["Tipo"] == "Sustitucion"
    assert Regla["OrigenTexto"] == (
        "1 onslaught gatling cannon"
    )
    assert Regla["DestinosTexto"] == ["1 heavy flamer"]
    assert Regla["Eleccion"] == "Directa"


def test_sustitucion_con_alternativas():
    Opciones = CrearOpciones(
        "This model’s 2 twin heavy bolters can be replaced "
        "with one of the following:",
        [
            "2 assault cannons",
            "2 twin lascannons",
        ],
    )

    Resultado, Revision = InterpretarOpciones(Opciones)

    assert Revision is False

    Regla = Resultado["Estructuradas"][0]

    assert Regla["OrigenTexto"] == "2 twin heavy bolters"
    assert Regla["Eleccion"] == "UnaDeVarias"
    assert len(Regla["DestinosTexto"]) == 2


def test_equipamiento_adicional():
    Opciones = CrearOpciones(
        "This model can be equipped with "
        "1 hunter-killer missile."
    )

    Resultado, Revision = InterpretarOpciones(Opciones)

    assert Revision is False
    assert Resultado["Estructuradas"][0]["Tipo"] == (
        "Adicion"
    )
    assert Resultado["Estructuradas"][0]["OrigenTexto"] is None


def test_equipamiento_obligatorio():
    Opciones = CrearOpciones(
        "This model must be equipped with one of the following:",
        [
            "1 servo arm",
            "1 conversion beamer",
        ],
    )

    Resultado, Revision = InterpretarOpciones(Opciones)

    assert Revision is False
    assert Resultado["Estructuradas"][0]["Tipo"] == (
        "EleccionObligatoria"
    )
    assert Resultado["Estructuradas"][0]["Eleccion"] == (
        "UnaDeVarias"
    )


def test_restriccion_proporcional_queda_pendiente():
    Opciones = CrearOpciones(
        "For every 5 models in this unit, 1 model’s "
        "Astartes chainsword can be replaced "
        "with 1 eviscerator."
    )

    Resultado, Revision = InterpretarOpciones(Opciones)

    assert Revision is True
    assert Resultado["Estructuradas"] == []
    assert len(Resultado["Pendientes"]) == 1


def test_regla_de_grupo_no_se_simplifica():
    Opciones = CrearOpciones(
        "Any number of models can each have their "
        "heavy bolter replaced with 1 multi-melta."
    )

    Resultado, Revision = InterpretarOpciones(Opciones)

    assert Revision is True
    assert Resultado["Estructuradas"] == []
    assert Resultado["Pendientes"][0]["Pagina"] == 30
