---
name: gen-pdf
description: Converts a Markdown file to a styled PDF with DevExpert branding (logo in bottom-right corner). Use when asked to generate a PDF from a Markdown document, or when any DevExpert proposal/document needs to be exported as PDF.
---

# gen-pdf — Generador de PDFs con estilo DevExpert

Convierte cualquier fichero Markdown a PDF con la tipografía, colores y logo de DevExpert.

## Cuándo usar esta skill

- El usuario pide generar un PDF a partir de un fichero `.md`
- Se acaba de crear o actualizar un documento/propuesta y hay que exportarlo
- El usuario pide añadir el logo de DevExpert a un PDF existente

## Dependencias

```bash
pip install markdown-it-py[plugins] weasyprint reportlab PyPDF2
```

## Rutas clave

- **Logo DevExpert:** `/Users/antonio/Library/Mobile Documents/iCloud~md~obsidian/Documents/Cerebro/150 - 🏆 ACTIVOS/DevExpert/Charlas/Domina las recomposiciones en Jetpack Compose/templates/devexpert-slide-footer.png`
- **Output por defecto:** `~/Documents/aipal/40-archive/`

## Script de generación

Usa el siguiente script Python. Acepta `input_md` y `output_pdf` como variables:

```python
import os
from markdown_it import MarkdownIt
from weasyprint import HTML, CSS
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter
import tempfile

md = MarkdownIt("commonmark", {"breaks": True, "html": True}).enable("table")

LOGO_PATH = "/Users/antonio/Library/Mobile Documents/iCloud~md~obsidian/Documents/Cerebro/150 - 🏆 ACTIVOS/DevExpert/Charlas/Domina las recomposiciones en Jetpack Compose/templates/devexpert-slide-footer.png"

CSS_STYLES = """
@page { size: A4; margin: 2cm 2.5cm; }
body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.5; color: #333; }
h1 { color: #1a56a0; font-size: 18pt; border-bottom: 2px solid #1a56a0; padding-bottom: 6px; margin-top: 40px; }
h2 { color: #1a56a0; font-size: 13pt; margin-top: 36px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
h3 { color: #2c7be5; font-size: 11pt; margin-top: 28px; }
ul { margin: 6px 0 6px 20px; padding: 0; }
li { margin-bottom: 3px; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 9.5pt; }
th { background-color: #1a56a0; color: white; padding: 6px 10px; text-align: left; }
td { padding: 5px 10px; border-bottom: 1px solid #ddd; }
tr:nth-child(even) td { background-color: #f5f8ff; }
strong { color: #1a56a0; }
hr { page-break-after: always; border: none; margin: 0; }
blockquote { border-left: 3px solid #2c7be5; padding-left: 12px; color: #555; margin: 8px 0; }
"""

def gen_pdf(input_md, output_pdf, add_logo=True):
    with open(input_md, 'r', encoding='utf-8') as f:
        content = f.read()

    html_content = md.render(content)
    full_html = f'<html><body>{html_content}</body></html>'
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
    HTML(string=full_html).write_pdf(output_pdf, stylesheets=[CSS(string=CSS_STYLES)])

    if add_logo:
        reader = PdfReader(output_pdf)
        writer = PdfWriter()
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_logo_pdf = f.name

        page_width, page_height = A4
        c = canvas.Canvas(temp_logo_pdf, pagesize=A4)
        c.drawImage(LOGO_PATH, page_width - 120, 15, width=100, height=25,
                   mask='auto', preserveAspectRatio=True)
        c.showPage()
        c.save()

        logo_page = PdfReader(temp_logo_pdf).pages[0]
        for page in reader.pages:
            page.merge_page(logo_page)
            writer.add_page(page)

        with open(output_pdf, 'wb') as out:
            writer.write(out)
        os.unlink(temp_logo_pdf)
```

## Instrucciones de uso

1. Importa o copia la función `gen_pdf` en un script temporal en `/tmp/`
2. Llámala con `input_md` = ruta al fichero Markdown, `output_pdf` = ruta de salida
3. `add_logo=True` por defecto (siempre para documentos DevExpert)
4. Tras generar, copia a `/var/folders/hl/jhc62x9j18sf_50prjn2xl080000gn/T/aipal/documents/` y responde con `[[document:/ruta]]`

## Notas

- Los `---` en el Markdown generan saltos de página en el PDF
- Los saltos de línea simples se respetan (comportamiento igual que Obsidian)
- Las tablas Markdown se renderizan correctamente
