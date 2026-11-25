
import json
from pathlib import Path

import pymupdf


Raiz = Path(__file__).resolve().parents[2]
CarpetaPdfs = Raiz / "Data" / "Pdfs"

Archivo = CarpetaPdfs / (
    "eng_08-06_warhammer40000_faction_pack_space-marines"
    "-nd2ezs5yzn-wxe2nf2ckk.pdf"
)

Reporte = Path(__file__).with_name(
    "PdfTablasCatoSicariusReporte.json"
)

ColumnasArmas = {
    "RANGED WEAPONS": [
        "Arma", "RANGE", "A", "BS", "S", "AP", "D"
    ],
    "MELEE WEAPONS": [
        "Arma", "RANGE", "A", "WS", "S", "AP", "D"
    ],
}


def ObtenerLineas(Texto):
    """Separa el texto de un bloque en líneas útiles."""
    return [
        Linea.strip()
        for Linea in Texto.splitlines()
        if Linea.strip()
    ]


def ExtraerCaracteristicas(Bloques):
    """Relaciona los atributos con sus valores."""

    Encabezados = ["M", "T", "SV", "W", "LD", "OC"]

    for Bloque in Bloques:
        Lineas = ObtenerLineas(Bloque[4])

        if Lineas[:6] == Encabezados:
            Valores = Lineas[6:]

            if len(Valores) == len(Encabezados):
                return dict(zip(Encabezados, Valores))

    return {}


def ExtraerArmas(Bloques):
    """Extrae las filas de las tablas de armas."""

    Resultado = {
        "RANGED WEAPONS": [],
        "MELEE WEAPONS": [],
    }

    Advertencias = []
    SeccionActual = None

    for Bloque in Bloques:
        if Bloque[6] != 0:
            continue

        Lineas = ObtenerLineas(Bloque[4])

        if not Lineas:
            continue

        PrimeraLinea = Lineas[0]

        if PrimeraLinea == "WARGEAR OPTIONS":
            break

        if PrimeraLinea in ColumnasArmas:
            SeccionActual = PrimeraLinea

            # Validamos los encabezados de la tabla.
            Esperados = ColumnasArmas[SeccionActual][1:]

            if Lineas[1:] != Esperados:
                Advertencias.append(
                    f"Encabezados inesperados: {SeccionActual}"
                )

            continue

        if SeccionActual is None:
            continue

        Columnas = ColumnasArmas[SeccionActual]

        if len(Lineas) != len(Columnas):
            Advertencias.append(
                f"Fila no reconocida: {Lineas}"
            )
            continue

        Fila = dict(zip(Columnas, Lineas))
        Resultado[SeccionActual].append(Fila)

    return Resultado, Advertencias


def Principal():
    with pymupdf.open(Archivo) as Documento:
        Pagina = Documento[35]  # LAND SPEEDER

        Bloques = Pagina.get_text(
            "blocks", sort=False
        )

        Caracteristicas = ExtraerCaracteristicas(Bloques)
        Armas, Advertencias = ExtraerArmas(Bloques)

        Resultado = {
        "Documento": Archivo.name,
        "Pagina": 36,
        "Unidad": "CATO SICARIUS",
        "Caracteristicas": Caracteristicas,
        "Armas": Armas,
        "Advertencias": Advertencias,
    }

    Reporte.write_text(
        json.dumps(
            Resultado,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8",
    )

    print(f"Reporte generado: {Reporte}")
    print(f"Armas a distancia: {len(Armas['RANGED WEAPONS'])}")
    print(f"Armas cuerpo a cuerpo: {len(Armas['MELEE WEAPONS'])}")
    print(f"Advertencias: {len(Advertencias)}")


if __name__ == "__main__":
    Principal()
