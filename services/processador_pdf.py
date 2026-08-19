import io
import os
import sys
from PIL import Image
import pytesseract
import re
import fitz

# Configura codificação do stdout para UTF-8 no Windows caso necessário
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def extrair_texto_pdf(origem_pdf: bytes | str) -> list[str]:
    """
    Extrai todo o texto de um arquivo PDF, retornando uma lista de strings.

    Parâmetros:
        origem_pdf (bytes | str): Buffer em bytes do PDF ou caminho para o arquivo PDF.

    Retorna:
        list[str]: Lista de strings onde o índice [0] representa a primeira página,
                   índice [1] a segunda página, e assim por diante.
    """
    if isinstance(origem_pdf, str):
        if not os.path.exists(origem_pdf):
            raise FileNotFoundError(f"Erro: O arquivo '{origem_pdf}' não foi encontrado.")
        print(f"[PDF] Lendo arquivo: {origem_pdf}")
        doc = fitz.open(origem_pdf)
    elif isinstance(origem_pdf, bytes):
        print(f"[PDF] Lendo arquivo a partir de buffer ({len(origem_pdf)} bytes)")
        doc = fitz.open(stream=origem_pdf, filetype="pdf")
    else:
        raise TypeError("O parâmetro 'origem_pdf' deve ser do tipo bytes ou str.")

    total_paginas = len(doc)
    paginas_texto = []

    print(f"[PDF] Total de páginas encontradas: {total_paginas}\n")

    for num_pagina in range(total_paginas):
        pagina = doc.load_page(num_pagina)

        texto_pagina = pagina.get_text("text").strip()

        if texto_pagina and len(texto_pagina) > 60:
            paginas_texto.append(texto_pagina)
            continue

        # Caso o texto não seja extraído diretamente (PDFs escaneados/imagens), aplicamos OCR

        # Gera a imagem inicial da página
        pix = pagina.get_pixmap(dpi=300) 
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        
        # Detecta a orientação da imagem e rotaciona se necessário
        try:
            osd = pytesseract.image_to_osd(img)            
            match = re.search(r'Rotate: (\d+)', osd)
            
            if match:
                angulo = int(match.group(1))
                
                if angulo != 0:
                    img = img.rotate(-angulo, expand=True) 
        except Exception as e:
            print(f"Não foi possível detectar a orientação da página {num_pagina + 1}: {e}")
    
        # Aplica o OCR na imagem
        texto_pagina = pytesseract.image_to_string(img, lang='por')        
        paginas_texto.append(texto_pagina)

    # Verifica se algum texto foi extraído (PDFs escaneados/imagens podem retornar strings vazias)
    texto_combinado = "".join(paginas_texto)
    if not texto_combinado.strip():
        print("[AVISO] Nenhum texto foi extraído. O PDF pode ser composto apenas por imagens ou estar protegido contra cópia.")

    doc.close()
    return paginas_texto