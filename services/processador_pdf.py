import fitz

def extrair_texto_contrato(pdf_path: str):
    paginas = [] # texto por página
    doc = fitz.open(pdf_path)

    for pag in doc:
        texto = pag.get_text("text")

        if texto:
            paginas.append(texto)
        else:
            tabs = pag.find_tables()

            if tabs.tables:
                table = tabs[0].extract()
                paginas.append(table)

    doc.close()
    return paginas
