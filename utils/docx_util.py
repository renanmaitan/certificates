from docx import Document

def replace_placeholders(caminho_arquivo, nome, cpf, caminho_saida):
    doc = Document(caminho_arquivo)
    for par in doc.paragraphs:
        if "{NOME}" in par.text or "{CPF}" in par.text:
            par.text = par.text.replace("{NOME}", nome).replace("{CPF}", cpf)
    for table in doc.tables:
        for linha in table.rows:
            for celula in linha.cells:
                if "{NOME}" in celula.text or "{CPF}" in celula.text:
                    celula.text = celula.text.replace("{NOME}", nome).replace("{CPF}", cpf)

    doc.save(caminho_saida)