from pptx import Presentation

def replace_placeholders(caminho_arquivo, nome, cpf, caminho_saida):
    prs = Presentation(caminho_arquivo)

    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragrafo in shape.text_frame.paragraphs:
                    for run in paragrafo.runs:
                        if "{NOME}" in run.text or "{CPF}" in run.text:
                            run.text = run.text.replace("{NOME}", nome).replace("{CPF}", cpf)

    prs.save(caminho_saida)