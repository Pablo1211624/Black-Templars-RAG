
from copy import deepcopy

from app.Procesamiento.AuditorCalidadEquipo import (
    AuditarFicha,
    ProponerCorreccion,
)


def CrearFicha():
    return {
        "Unidad": "UNIDAD DE PRUEBA",
        "Documento": "reglas.pdf",
        "Armas": {
            "Disparo": [],
            "CuerpoACuerpo": [],
        },
        "EquipamientoInicial": [],
        "OpcionesEquipo": {"Reglas": []},
        "InterpretacionOpciones": {"Estructuradas": []},
        "InterpretacionRestricciones": {"Interpretadas": []},
        "InterpretacionCompuestas": {"Pendientes": []},
    }


def test_propone_cuatro_correcciones():
    Textos = [
        "Any number of models can each have their "
        "bolt pistol replaced one of the following:",

        "Any number of models can each have their "
        "power fist replaced with one 1 chainfist.",

        "This model’s 2 lascannons can be replaced "
        "with on of the following:",

        "This model’s twin heavy bolter replaced "
        "with 1 twin lascannon.",
    ]

    Ficha = CrearFicha()

    Ficha["InterpretacionCompuestas"]["Pendientes"] = [
        {
            "ReglaOriginal": Texto,
            "Pagina": Indice + 1,
            "Alternativas": [],
        }
        for Indice, Texto in enumerate(Textos)
    ]

    Resultado = AuditarFicha(Ficha)

    assert len(Resultado) == 4
    assert all(
        Observacion["Propuesta"]
        for Observacion in Resultado
    )
    assert all(
        Observacion["Estado"] == "PendienteVerificacionPDF"
        for Observacion in Resultado
    )


def test_no_modifica_texto_original():
    Ficha = CrearFicha()

    Ficha["InterpretacionCompuestas"]["Pendientes"] = [{
        "ReglaOriginal": (
            "This model’s twin heavy bolter replaced "
            "with 1 twin lascannon."
        ),
        "Pagina": 215,
        "Alternativas": [],
    }]

    Antes = deepcopy(Ficha)

    AuditarFicha(Ficha)

    assert Ficha == Antes


def test_detecta_posible_errata_volite():
    Ficha = CrearFicha()

    Ficha["Armas"]["Disparo"].append({
        "Nombre": "Volkite culverin"
    })

    Ficha["OpcionesEquipo"]["Reglas"].append({
        "Regla": "Test rule",
        "Alternativas": ["2 volite culverins"],
        "Pagina": 211,
    })

    Resultado = AuditarFicha(Ficha)

    assert len(Resultado) == 1
    assert Resultado[0]["Tipo"] == (
        "PosibleErrataNombreArma"
    )
    assert Resultado[0]["Propuesta"] == (
        "2 volkite culverins"
    )


def test_detecta_posible_equipamiento_duplicado():
    Ficha = CrearFicha()

    Ficha["EquipamientoInicial"].append({
        "Sujeto": "This model",
        "Elementos": [{
            "Cantidad": 1,
            "Nombre": "ironhail heavy stubber",
        }],
    })

    Ficha["InterpretacionOpciones"]["Estructuradas"].append({
        "Tipo": "Adicion",
        "Sujeto": "This model",
        "DestinosTexto": ["1 ironhail heavy stubber"],
        "Pagina": 56,
        "ReglaOriginal": (
            "This model can be equipped with "
            "1 ironhail heavy stubber."
        ),
    })

    Resultado = AuditarFicha(Ficha)

    assert len(Resultado) == 1
    assert Resultado[0]["Tipo"] == (
        "PosibleEquipamientoDuplicado"
    )
    assert Resultado[0]["Propuesta"] is None


def test_ficha_sin_anomalias():
    assert AuditarFicha(CrearFicha()) == []

    assert ProponerCorreccion(
        "This model can be equipped with 1 storm bolter."
    ) is None
