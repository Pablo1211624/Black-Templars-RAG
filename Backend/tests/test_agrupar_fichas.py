
from app.Procesamiento.AgrupadorFichas import AgruparPaginas, ClasificarGrupo, ObtenerTituloFicha


def test_agrupa_paginas_de_misma_unidad():
    Registros = [
        {"Pagina": 34, "Unidad": "MARNEUS CALGAR"},
        {"Pagina": 35, "Unidad": "CATO SICARIUS"},
        {"Pagina": 36, "Unidad": "CATO SICARIUS"},
        {"Pagina": 37, "Unidad": "VICTRIX HONOUR GUARD"},
    ]

    Resultado = AgruparPaginas(Registros)

    assert len(Resultado) == 3
    assert Resultado[1]["Unidad"] == "CATO SICARIUS"
    assert Resultado[1]["Paginas"] == [35, 36]


def test_no_agrupa_paginas_no_consecutivas():
    Registros = [
        {"Pagina": 10, "Unidad": "UNIDAD A"},
        {"Pagina": 12, "Unidad": "UNIDAD A"},
    ]

    Resultado = AgruparPaginas(Registros)

    assert len(Resultado) == 2


def test_no_mezcla_unidades_con_nombres_similares():
    Registros = [
        {"Pagina": 123, "Unidad": "ASSAULT SQUAD"},
        {"Pagina": 124, "Unidad": "ASSAULT SQUAD"},
        {
            "Pagina": 125,
            "Unidad": "ASSAULT SQUAD WITH JUMP PACKS"
        },
        {
            "Pagina": 126,
            "Unidad": "ASSAULT SQUAD WITH JUMP PACKS"
        },
    ]

    Resultado = AgruparPaginas(Registros)

    assert len(Resultado) == 2

    assert Resultado[0] == {
        "Unidad": "ASSAULT SQUAD",
        "Paginas": [123, 124],
    }

    assert Resultado[1] == {
        "Unidad": "ASSAULT SQUAD WITH JUMP PACKS",
        "Paginas": [125, 126],
    }


def test_clasifica_ficha_unidad():
    Texto = (
        "CATO SICARIUS "
        "RANGED WEAPONS "
        "ABILITIES "
        "UNIT COMPOSITION "
        "KEYWORDS: Infantry"
    )

    assert ClasificarGrupo(
        "CATO SICARIUS", Texto
    ) == "FichaUnidad"


def test_clasifica_tabla_armas():
    Texto = (
        "ADEPTUS ASTARTES LEGENDS ARMOURY "
        "RANGED WEAPONS "
        "RANGE A BS S AP D"
    )

    assert ClasificarGrupo(
        "ADEPTUS ASTARTES LEGENDS ARMOURY",
        Texto
    ) == "TablaArmas"


def test_marca_contenido_desconocido():
    assert ClasificarGrupo(
        "SECCION GENERAL",
        "Introduccion al reglamento"
    ) == "RevisionManual"


def test_clasifica_reglas_faccion():
    Texto = (
        "RENEGADES AND TRAITORS "
        "UNIT OPTIONS "
        "The following Adeptus Astartes datasheets "
        "can be included in Heretic Astartes armies. "
        "Replace instances of the Imperium keyword "
        "with Chaos."
    )

    Resultado = ClasificarGrupo(
        "RENEGADES AND TRAITORS",
        Texto
    )

    assert Resultado == "ReglasFaccion"


def test_reconstruye_titulo_con_fuente_semilight():
    class PaginaFalsa:
        class Rectangulo:
            width = 538.58

        rect = Rectangulo()

        def get_text(self, Formato):
            assert Formato == "dict"

            Fragmentos = [
                ("ERADICATOR SQUAD", "Akhand-Extrabold", 15, 14, 116),
                ("WITH", "Akhand-Semilight", 9, 123, 138),
                ("HEAVY", "Akhand-Semilight", 9, 141, 160),
                ("BOLTERS", "Akhand-Semilight", 9, 163, 198),
            ]

            Spans = []

            for Texto, Fuente, Tamano, X1, X2 in Fragmentos:
                Y = 16 if Tamano == 15 else 21.6

                Spans.append({
                    "text": Texto,
                    "font": Fuente,
                    "size": Tamano,
                    "bbox": (X1, Y, X2, Y + Tamano),
                })

            return {
                "blocks": [
                    {"lines": [{"spans": Spans}]}
                ]
            }

    Resultado = ObtenerTituloFicha(PaginaFalsa())

    assert Resultado == (
        "ERADICATOR SQUAD WITH HEAVY BOLTERS"
    )


