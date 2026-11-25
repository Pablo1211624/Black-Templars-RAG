
from app.Procesamiento.ClasificadorPaginas import (
    ClasificarTexto,
)


def test_ficha_con_armas():
    Texto = """
    LAND SPEEDER
    RANGED WEAPONS
    Multi-melta
    MELEE WEAPONS
    """

    assert ClasificarTexto(Texto) == "FichaConArmas"


def test_ficha_sin_tabla_armas():
    Texto = """
    CATO SICARIUS
    LEADER
    UNIT COMPOSITION
    This model is equipped with a plasma pistol.
    KEYWORDS
    ADEPTUS ASTARTES
    """

    assert ClasificarTexto(Texto) == "FichaSinTablaArmas"


def test_destacamento():
    Texto = """
    THE LIVING MIRACLE
    DETACHMENT RULES
    ANOINTED CHAMPION
    ENHANCEMENTS
    GUIDING OMENS
    """

    assert ClasificarTexto(Texto) == "Destacamento"


def test_pagina_sin_texto():
    assert ClasificarTexto("") == "PocoTexto"
