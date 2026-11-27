from app.Procesamiento.ValidadorCruceModelos import (
    ValidarCruceModelos,
)


def CrearFicha(
    SujetoRegla="The Assault Sergeant",
    Origen="bolt pistol",
    Composicion="■1 Assault Sergeant\n■4-9 Assault Marines",
    Declaraciones=None,
    Tipo="ModeloEspecifico",
):
    if Declaraciones is None:
        Declaraciones = [{
            "Sujeto": "Every model",
            "Elementos": [
                {"Cantidad": 1, "Nombre": "bolt pistol"},
                {"Cantidad": 1, "Nombre": "Astartes chainsword"},
            ],
        }]

    return {
        "Unidad": "UNIDAD DE PRUEBA",
        "Secciones": {
            "Composicion": [{"Texto": Composicion}]
        },
        "EquipamientoInicial": Declaraciones,
        "InterpretacionRestricciones": {
            "Interpretadas": [{
                "Tipo": "Sustitucion",
                "Sujeto": SujetoRegla,
                "OrigenTexto": Origen,
                "Pagina": 20,
                "ReglaOriginal": "Regla de prueba",
                "Restriccion": {"Tipo": Tipo},
            }]
        },
    }


def test_modelo_especifico_hereda_equipo_de_every_model():
    Resultado = ValidarCruceModelos([CrearFicha()])
    assert len(Resultado) == 1
    assert Resultado[0]["Estado"] == "CoincideConInicial"
    assert Resultado[0]["DeclaracionUtilizada"] == "Every model"


def test_prefiere_declaracion_de_modelo_especifico():
    Ficha = CrearFicha(
        SujetoRegla="The Company Ancient",
        Origen="close combat weapon",
        Composicion="■1 Company Ancient\n■2 Company Veterans",
        Declaraciones=[
            {
                "Sujeto": "Every model",
                "Elementos": [{"Cantidad": 1, "Nombre": "bolt pistol"}],
            },
            {
                "Sujeto": "The Company Ancient",
                "Elementos": [{
                    "Cantidad": 1, "Nombre": "close combat weapon"
                }],
            },
        ],
    )
    Resultado = ValidarCruceModelos([Ficha])
    assert Resultado[0]["Estado"] == "CoincideConInicial"
    assert Resultado[0]["DeclaracionUtilizada"] == "The Company Ancient"


def test_declaracion_compuesta_y_attack_bike():
    Composicion = (
        "■1 Biker Sergeant\n"
        "■2-5 Space Marine Bikers\n"
        "■0-1 Attack Bike"
    )
    Declaraciones = [
        {
            "Sujeto": "The Biker Sergeant and every Space Marine Biker",
            "Elementos": [{"Cantidad": 1, "Nombre": "bolt pistol"}],
        },
        {
            "Sujeto": "An Attack Bike",
            "Elementos": [{"Cantidad": 1, "Nombre": "heavy bolter"}],
        },
    ]
    Fichas = [
        CrearFicha(
            SujetoRegla="The Biker Sergeant",
            Origen="bolt pistol",
            Composicion=Composicion,
            Declaraciones=Declaraciones,
        ),
        CrearFicha(
            SujetoRegla="An Attack Bike",
            Origen="heavy bolter",
            Composicion=Composicion,
            Declaraciones=Declaraciones,
        ),
    ]
    Resultado = ValidarCruceModelos(Fichas)
    assert [R["Estado"] for R in Resultado] == [
        "CoincideConInicial",
        "CoincideConInicial",
    ]
    assert Resultado[1]["DeclaracionUtilizada"] == "An Attack Bike"


def test_sujeto_no_declarado_no_hereda_equipo_generico():
    Ficha = CrearFicha(
        SujetoRegla="The Captain",
        Composicion="■1 Assault Sergeant\n■4-9 Assault Marines",
    )
    Resultado = ValidarCruceModelos([Ficha])
    assert Resultado[0]["Estado"] == "SujetoNoIdentificado"
    assert Resultado[0]["DeclaracionUtilizada"] is None


def test_diferencia_de_nombre_no_se_declara_ilegalidad():
    Ficha = CrearFicha(
        SujetoRegla="1 Scout Sniper",
        Origen="scout sniper rifle",
        Composicion="■1 Scout Sniper Sergeant\n■4-9 Scout Snipers",
        Declaraciones=[{
            "Sujeto": "Every model",
            "Elementos": [{"Cantidad": 1, "Nombre": "sniper rifle"}],
        }],
    )
    Resultado = ValidarCruceModelos([Ficha])
    assert Resultado[0]["Estado"] == "NoCoincideConInicial"
    assert Resultado[0]["Faltantes"][0]["Nombre"] == "scout sniper rifle"


def test_no_incluye_otras_categorias():
    Ficha = CrearFicha(Tipo="PorCadaModelos")
    assert ValidarCruceModelos([Ficha]) == []


def test_alias_scout_sniper_solo_unidad_documentada():
    Ficha = CrearFicha(
        SujetoRegla="1 Scout Sniper",
        Origen="scout sniper rifle",
        Composicion="■1 Scout Sniper Sergeant\n■4-9 Scout Snipers",
        Declaraciones=[{
            "Sujeto": "Every model",
            "Elementos": [{"Cantidad": 1, "Nombre": "sniper rifle"}],
        }],
    )
    Ficha["Unidad"] = "SCOUT SNIPER SQUAD"
    Resultado = ValidarCruceModelos([Ficha])[0]
    assert Resultado["Estado"] == "CoincidePorAliasDocumentado"
    assert Resultado["Faltantes"] == []
    assert Resultado["AliasUtilizados"] == [{
        "NombreRegla": "scout sniper rifle",
        "NombreInicial": "sniper rifle",
        "Cantidad": 1,
    }]


def test_alias_no_se_aplica_a_cantidad_distinta():
    Ficha = CrearFicha(
        SujetoRegla="1 Scout Sniper",
        Origen="2 scout sniper rifles",
        Composicion="■1 Scout Sniper Sergeant\n■4-9 Scout Snipers",
        Declaraciones=[{
            "Sujeto": "Every model",
            "Elementos": [{"Cantidad": 2, "Nombre": "sniper rifle"}],
        }],
    )
    Ficha["Unidad"] = "SCOUT SNIPER SQUAD"
    Resultado = ValidarCruceModelos([Ficha])[0]
    assert Resultado["Estado"] == "NoCoincideConInicial"
    assert Resultado["AliasUtilizados"] == []
