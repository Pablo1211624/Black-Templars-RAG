
import json
from pathlib import Path

import pymupdf


# Rutas independientes del directorio desde donde
# ejecutemos el programa.
ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "Data" / "Pdfs"
REPORT = ROOT / "Backend" / "preprocesos" / "PdfAnalizadorReporte.json"


def analyze_pdf(pdf_path: Path) -> dict:
    """Obtiene estadísticas básicas de un PDF."""

    with pymupdf.open(pdf_path) as doc:
        if doc.needs_pass:
            raise ValueError(f"PDF protegido: {pdf_path.name}")

        # Analizamos todas las páginas individualmente.
        text_per_page = [
            len(page.get_text("text").strip())
            for page in doc
        ]

        total_pages = len(doc)

        return {
            "file": pdf_path.name,
            "pages": total_pages,
            "total_characters": sum(text_per_page),
            "avg_chars_per_page": round(
                sum(text_per_page) / max(total_pages, 1), 2
            ),
            "text_per_page": text_per_page,
            "pages_with_little_text": [
                i + 1
                for i, count in enumerate(text_per_page)
                if count < 50
            ],
        }


def main():
    pdfs = sorted(PDF_DIR.glob("*.pdf"))

    if not pdfs:
        raise SystemExit("No se encontraron archivos PDF.")

    results = []

    for pdf in pdfs:
        result = analyze_pdf(pdf)
        results.append(result)

        print(f"\nDocumento: {result['file']}")
        print(f"Paginas: {result['pages']}")
        print(f"Caracteres: {result['total_characters']}")
        print(
            "Promedio por pagina:",
            result["avg_chars_per_page"]
        )

    REPORT.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nReporte generado: {REPORT}")


if __name__ == "__main__":
    main()
