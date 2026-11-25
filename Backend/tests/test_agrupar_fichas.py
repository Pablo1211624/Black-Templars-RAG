
from app.Procesamiento.AgrupadorFichas import AgruparPaginas


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
