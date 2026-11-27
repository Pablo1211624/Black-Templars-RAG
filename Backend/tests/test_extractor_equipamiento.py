
from app.Procesamiento.ExtractorEquipamiento import (
    ExtraerEquipamientoInicial
)


def CrearSecciones(Texto):
    return {
        "Composicion": [{
            "Pagina": 10,
            "Texto": Texto,
        }]
    }


def test_extrae_equipamiento_con_cantidades():
    Secciones = CrearSecciones(
        "This model is equipped with: heavy bolter; "
        "2 heavy flamers; 3 hunter-killer missiles."
    )

    Resultado, Revision = ExtraerEquipamientoInicial(Secciones)

    assert Revision is False
    assert len(Resultado) == 1

    Elementos = Resultado[0]["Elementos"]

    assert Elementos[0] == {
        "Cantidad": 1,
        "Nombre": "heavy bolter",
    }
    assert Elementos[1]["Cantidad"] == 2
    assert Elementos[2]["Cantidad"] == 3


def test_distingue_equipamiento_de_modelos():
    Secciones = CrearSecciones(
        "The Biker Sergeant and every Space Marine Biker\n"
        "is equipped with: bolt pistol; twin boltgun.\n"
        "An Attack Bike is equipped with: "
        "bolt pistol; heavy bolter."
    )

    Resultado, Revision = ExtraerEquipamientoInicial(Secciones)

    assert Revision is False
    assert len(Resultado) == 2
    assert Resultado[0]["Sujeto"] == (
        "The Biker Sergeant and every Space Marine Biker"
    )
    assert Resultado[1]["Sujeto"] == "An Attack Bike"
    assert Resultado[1]["Elementos"][1]["Nombre"] == (
        "heavy bolter"
    )


def test_nothing_no_se_convierte_en_arma():
    Secciones = CrearSecciones(
        "This model is equipped with: nothing."
    )

    Resultado, Revision = ExtraerEquipamientoInicial(Secciones)

    assert Revision is False
    assert len(Resultado) == 1
    assert Resultado[0]["Elementos"] == []


def test_sin_declaracion_no_inventa_equipamiento():
    Secciones = CrearSecciones(
        "■1 Drop Pod\nTRANSPORT"
    )

    Resultado, Revision = ExtraerEquipamientoInicial(Secciones)

    assert Resultado == []
    assert Revision is False


def test_no_mezcla_narrativa_con_equipamiento():
    Secciones = CrearSecciones(
        "This model is equipped with: multi-melta; "
        "heavy bolter;\n"
        "close-combat weapon\n"
        "Streaking over the battlefield on humming engines\n"
        "and attacking enemy infantry."
    )

    Resultado, Revision = ExtraerEquipamientoInicial(Secciones)

    assert Revision is True
    assert len(Resultado[0]["Elementos"]) == 3
    assert Resultado[0]["Elementos"][2]["Nombre"] == (
        "close-combat weapon"
    )
