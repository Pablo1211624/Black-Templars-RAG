
from app.Procesamiento.ExtractorFichas import ExtraerFichas, ExtraerCaracteristicas, AsociarModelos, DetectarLegends


class PaginaFalsa:
    def __init__(self, Texto):
        self.Texto = Texto

    def get_text(self, Formato, sort=False):
        assert Formato == "text"
        return self.Texto


def test_extrae_ficha_y_conserva_paginas():
    Documento = [
        PaginaFalsa("Armas de Cato Sicarius"),
        PaginaFalsa("Composicion de Cato Sicarius"),
        PaginaFalsa("Tabla de armas general"),
    ]

    Grupos = [
        {
            "Unidad": "CATO SICARIUS",
            "Paginas": [1, 2],
            "Tipo": "FichaUnidad",
        },
        {
            "Unidad": "ARMOURY",
            "Paginas": [3],
            "Tipo": "TablaArmas",
        },
    ]

    Resultado = ExtraerFichas(
        Documento,
        Grupos,
        "SpaceMarines.pdf",
    )

    assert len(Resultado) == 1
    assert Resultado[0]["Unidad"] == "CATO SICARIUS"
    assert Resultado[0]["Documento"] == "SpaceMarines.pdf"
    assert [Pagina["Pagina"] for Pagina in Resultado[0]["Paginas"]] == [1, 2]
    assert Resultado[0]["Paginas"][0]["Texto"] == "Armas de Cato Sicarius"
    assert Resultado[0]["Paginas"][1]["Texto"] == "Composicion de Cato Sicarius"


def test_extrae_caracteristicas_simples():
    Texto = (
        "CATO SICARIUS\n"
        "M\nT\nSV\nW\nLD\nOC\n"
        "6\"\n4\n2+\n5\n6+\n1\n"
    )

    Resultado = ExtraerCaracteristicas(Texto)

    assert Resultado == [{
        "M": '6"',
        "T": "4",
        "SV": "2+",
        "W": "5",
        "LD": "6+",
        "OC": "1",
    }]


def test_extrae_multiples_filas():
    Texto = (
        "BIKE SQUAD\n"
        "M\nT\nSV\nW\nLD\nOC\n"
        "12\"\n5\n3+\n3\n6+\n2\n"
        "12\"\n5\n3+\n5\n6+\n2\n"
    )

    Resultado = ExtraerCaracteristicas(Texto)

    assert len(Resultado) == 2
    assert Resultado[0]["W"] == "3"
    assert Resultado[1]["W"] == "5"



def test_no_inventa_caracteristicas():
    Texto = (
        "THUNDERHAWK GUNSHIP\n"
        "T\nSV\nW\nLD\nOC\n"
        "12\n2+\n30\n6+\n0\n"
    )

    Resultado = ExtraerCaracteristicas(Texto)

    assert Resultado == []



def test_extrae_movimiento_antes_de_estadisticas():
    Texto = (
        "CAESTUS ASSAULT RAM\n"
        "T\nSV\nW\nLD\nOC\n"
        "14\"\nM\n10\n3+\n18\n6+\n0\n"
    )

    Resultado = ExtraerCaracteristicas(Texto)

    assert Resultado == [{
        "M": '14"',
        "T": "10",
        "SV": "3+",
        "W": "18",
        "LD": "6+",
        "OC": "0",
    }]


def test_extrae_movimiento_despues_de_estadisticas():
    Texto = (
        "THUNDERHAWK GUNSHIP\n"
        "T\nSV\nW\nLD\nOC\n"
        "12\n2+\n30\n6+\n0\n20\"\nM\n"
    )

    Resultado = ExtraerCaracteristicas(Texto)

    assert Resultado == [{
        "M": '20"',
        "T": "12",
        "SV": "2+",
        "W": "30",
        "LD": "6+",
        "OC": "0",
    }]


def test_extrae_valores_no_aplicables():
    Texto = (
        "XIPHON INTERCEPTOR\n"
        "T\nSV\nW\nLD\nOC\n"
        "-\nM\n9\n3+\n12\n6+\n-\n"
    )

    Resultado = ExtraerCaracteristicas(Texto)

    assert Resultado == [{
        "M": "-",
        "T": "9",
        "SV": "3+",
        "W": "12",
        "LD": "6+",
        "OC": "-",
    }]


def test_asocia_modelos_por_coordenadas():
    class PaginaFalsa:
        def get_text(self, Formato):
            assert Formato == "dict"

            def CrearSpan(Texto, X, Y, Tamano):
                return {
                    "text": Texto,
                    "bbox": (X, Y, X + 40, Y + Tamano),
                    "size": Tamano,
                    "font": "ConduitITCStd-Bold",
                }

            return {
                "blocks": [{
                    "lines": [{
                        "spans": [
                            CrearSpan("ATTACK BIKE", 191, 72, 9),
                            CrearSpan("M", 24, 34, 7),
                            CrearSpan('12"', 17, 44.5, 14),
                            CrearSpan("SPACE MARINE BIKE", 191, 48.7, 9),
                            CrearSpan('12"', 17, 69.4, 14),
                        ]
                    }]
                }]
            }

    Caracteristicas = [
        {"M": '12"', "W": "3"},
        {"M": '12"', "W": "5"},
    ]

    Resultado = AsociarModelos(
        PaginaFalsa(),
        Caracteristicas
    )

    assert Resultado[0]["Modelos"] == ["SPACE MARINE BIKE"]
    assert Resultado[1]["Modelos"] == ["ATTACK BIKE"]


def test_no_inventa_asociaciones():
    class PaginaFalsa:
        def get_text(self, Formato):
            return {"blocks": []}

    Caracteristicas = [
        {"M": '12"', "W": "3"},
        {"M": '12"', "W": "5"},
    ]

    Resultado = AsociarModelos(
        PaginaFalsa(),
        Caracteristicas
    )

    assert Resultado == Caracteristicas


def test_detecta_ficha_legends():
    Paginas = [
        {
            "Pagina": 63,
            "Texto": (
                "WARHAMMER L E G E N D S\n"
                "FERREN AREIOS\n"
                "RANGED WEAPONS\n"
            ),
        }
    ]

    assert DetectarLegends(Paginas) is True


def test_no_confunde_referencia_con_legends():
    Paginas = [
        {
            "Pagina": 29,
            "Texto": (
                "ERADICATOR SQUAD\n"
                "RANGED WEAPONS\n"
                "Adeptus Astartes Legends Armoury card.\n"
            ),
        }
    ]

    assert DetectarLegends(Paginas) is False


