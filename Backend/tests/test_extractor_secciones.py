
from app.Procesamiento.ExtractorSecciones import ExtraerSecciones


def test_extrae_habilidades():
    Paginas = [{
        "Pagina": 30,
        "Texto": (
            "LAND SPEEDER\n"
            "ABILITIES\n"
            "CORE: Deep Strike\n"
            "FACTION: Oath of Moment\n"
            "Purgation Run: This unit can move.\n"
            "M\nT\nSV\nW\nLD\nOC\n"
        ),
    }]

    Resultado = ExtraerSecciones(Paginas, "LAND SPEEDER")

    assert len(Resultado["Habilidades"]) == 1
    assert "CORE: Deep Strike" in Resultado["Habilidades"][0]["Texto"]
    assert "Purgation Run" in Resultado["Habilidades"][0]["Texto"]
    assert Resultado["Habilidades"][0]["Pagina"] == 30
    assert "\nM\n" not in Resultado["Habilidades"][0]["Texto"]


def test_separa_habilidades_equipo_y_danio():
    Paginas = [{
        "Pagina": 57,
        "Texto": (
            "ABILITIES\n"
            "CORE: Hover\n"
            "FACTION: Oath of Moment\n"
            "Aerial Assault: Example.\n"
            "WARGEAR ABILITIES\n"
            "Cluster Bombs: Example.\n"
            "DAMAGED: 1-10 WOUNDS REMAINING\n"
            "Subtract 1 from the Hit roll.\n"
            "M\nT\nSV\n"
        ),
    }]

    Resultado = ExtraerSecciones(
        Paginas, "THUNDERHAWK GUNSHIP"
    )

    assert len(Resultado["Habilidades"]) == 1
    assert len(Resultado["HabilidadesEquipo"]) == 1
    assert len(Resultado["ReglasDanio"]) == 1

    assert "DAMAGED" not in Resultado["HabilidadesEquipo"][0]["Texto"]
    assert Resultado["ReglasDanio"][0]["Encabezado"] == (
        "DAMAGED: 1-10 WOUNDS REMAINING"
    )


def test_separa_opciones_y_composicion():
    Paginas = [{
        "Pagina": 32,
        "Texto": (
            "WARGEAR OPTIONS\n"
            "■Any model can replace its shield.\n"
            "UNIT COMPOSITION\n"
            "■1 Assault Terminator Sergeant\n"
            "■4-9 Assault Terminators\n"
            "Every model is equipped with: thunder hammer.\n"
            "TERMINATOR ASSAULT SQUAD\n"
            "Description of the unit.\n"
        ),
    }]

    Resultado = ExtraerSecciones(
        Paginas, "TERMINATOR ASSAULT SQUAD"
    )

    assert len(Resultado["OpcionesEquipo"]) == 1
    assert len(Resultado["Composicion"]) == 1
    assert "UNIT COMPOSITION" not in (
        Resultado["OpcionesEquipo"][0]["Texto"]
    )
    assert "Description of the unit" not in (
        Resultado["Composicion"][0]["Texto"]
    )


def test_composicion_con_encabezado_especial():
    Paginas = [{
        "Pagina": 38,
        "Texto": (
            "UNIT COMPOSITION (6 MODELS MAXIMUM)\n"
            "■1-6 Victrix Honour Guard\n"
            "VICTRIX HONOUR GUARD\n"
        ),
    }]

    Resultado = ExtraerSecciones(
        Paginas, "VICTRIX HONOUR GUARD"
    )

    assert Resultado["Composicion"][0]["Encabezado"] == (
        "UNIT COMPOSITION (6 MODELS MAXIMUM)"
    )
    assert "1-6 Victrix Honour Guard" in (
        Resultado["Composicion"][0]["Texto"]
    )


def test_unidad_sin_opciones_de_equipo():
    Paginas = [
        {
            "Pagina": 53,
            "Texto": "ABILITIES\nCORE: Deep Strike\nM\nT\n",
        },
        {
            "Pagina": 54,
            "Texto": (
                "UNIT COMPOSITION\n"
                "■1 Drop Pod\n"
                "DROP POD\n"
            ),
        },
    ]

    Resultado = ExtraerSecciones(Paginas, "DROP POD")

    assert Resultado["OpcionesEquipo"] == []
    assert Resultado["Habilidades"][0]["Pagina"] == 53
    assert Resultado["Composicion"][0]["Pagina"] == 54
