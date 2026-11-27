
from app.Procesamiento.ExtractorOpcionesEquipo import (
    ExtraerOpcionesEquipo
)


def CrearSecciones(Texto):
    return {
        "OpcionesEquipo": [{
            "Pagina": 70,
            "Texto": Texto,
        }]
    }


def test_agrupa_alternativas():
    Secciones = CrearSecciones(
        "■This model's plasma destroyer can be replaced "
        "with one of the following:\n"
        "◦1 conversion beam cannon\n"
        "◦1 infernus cannon\n"
        "■This model can be equipped with 1 storm bolter."
    )

    Resultado, Revision = ExtraerOpcionesEquipo(Secciones)

    assert Revision is False
    assert len(Resultado["Reglas"]) == 2
    assert Resultado["Reglas"][0]["Alternativas"] == [
        "1 conversion beam cannon",
        "1 infernus cannon",
    ]


def test_reconstruye_reglas_multilinea():
    Secciones = CrearSecciones(
        "■The Sergeant's bolt pistol can be\n"
        "replaced with one of the following:\n"
        "◦1 boltgun\n"
        "◦1 combi-weapon"
    )

    Resultado, Revision = ExtraerOpcionesEquipo(Secciones)

    assert Revision is False
    assert Resultado["Reglas"][0]["Regla"].endswith(
        "replaced with one of the following:"
    )


def test_conserva_notas_independientes():
    Secciones = CrearSecciones(
        "■This model can be equipped with one of the following:\n"
        "◦2 heavy flamers*\n"
        "* The profile for this weapon can be found on the Adeptus\n"
        "Astartes Legends Armoury card."
    )

    Resultado, Revision = ExtraerOpcionesEquipo(Secciones)

    assert Revision is False
    assert len(Resultado["Notas"]) == 1
    assert Resultado["Notas"][0]["Marcador"] == "*"
    assert Resultado["Notas"][0]["Texto"].endswith("card.")


def test_none_no_genera_reglas():
    Resultado, Revision = ExtraerOpcionesEquipo(
        CrearSecciones("■None")
    )

    assert Revision is False
    assert Resultado["Reglas"] == []
    assert Resultado["DeclaraNinguna"] is True


def test_alternativa_sin_regla_requiere_revision():
    Resultado, Revision = ExtraerOpcionesEquipo(
        CrearSecciones("◦1 storm bolter")
    )

    assert Revision is True
    assert Resultado["Reglas"] == []
    assert Resultado["Notas"][0]["Marcador"] == "SinContexto"
