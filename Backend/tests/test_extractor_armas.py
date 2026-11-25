
from app.Procesamiento.ExtractorArmas import ExtraerArmas


def test_extrae_arma_disparo():
    Texto = (
        "RANGED WEAPONS\n"
        "RANGE\nA\nBS\nS\nAP\nD\n"
        "Artisan plasma pistol [PISTOL]\n"
        "12\"\n1\n2+\n8\n-3\n2\n"
    )

    Armas, Revision = ExtraerArmas(Texto, 35)

    assert Revision is False
    assert len(Armas["Disparo"]) == 1
    assert Armas["Disparo"][0]["Nombre"] == "Artisan plasma pistol"
    assert Armas["Disparo"][0]["Habilidades"] == ["PISTOL"]
    assert Armas["Disparo"][0]["BS"] == "2+"
    assert Armas["Disparo"][0]["Pagina"] == 35


def test_extrae_arma_con_habilidad_en_otra_linea():
    Texto = (
        "MELEE WEAPONS\n"
        "RANGE\nA\nWS\nS\nAP\nD\n"
        "Talassarian tempest blade – strike\n"
        "[DEVASTATING WOUNDS]\n"
        "Melee\n4\n2+\n6\n-3\n3\n"
    )

    Armas, Revision = ExtraerArmas(Texto, 35)

    assert Revision is False
    assert Armas["CuerpoACuerpo"][0]["Nombre"] == (
        "Talassarian tempest blade – strike"
    )
    assert Armas["CuerpoACuerpo"][0]["Habilidades"] == [
        "DEVASTATING WOUNDS"
    ]


def test_no_confunde_nota_con_nombre_arma():
    Texto = (
        "RANGED WEAPON\n"
        "RANGE\nA\nBS\nS\nAP\nD\n"
        "Hunter-killer missile [ONE SHOT]\n"
        "48\"\n1\n2+\n14\n-3\nD6\n"
        "One Shot: The bearer can only shoot once per battle.\n"
        "Storm bolter [RAPID FIRE 2]\n"
        "24\"\n2\n3+\n4\n0\n1\n"
    )

    Armas, Revision = ExtraerArmas(Texto, 65)

    assert Revision is False
    assert len(Armas["Disparo"]) == 2
    assert Armas["Disparo"][1]["Nombre"] == "Storm bolter"


def test_sin_armas_no_inventa_perfiles():
    Armas, Revision = ExtraerArmas(
        "DROP POD\nUNIT COMPOSITION\n1 Drop Pod",
        53
    )

    assert Armas == {
        "Disparo": [],
        "CuerpoACuerpo": [],
    }
    assert Revision is False
