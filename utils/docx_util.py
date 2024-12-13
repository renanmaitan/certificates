from docx import Document


def replace_placeholders(caminho_arquivo, nome, cpf, caminho_saida):
    doc = Document(caminho_arquivo)

    def replace_in_runs(runs, placeholder, replacement):
        for run in runs:
            if placeholder in run.text:
                run.text = run.text.replace(placeholder, replacement)

    for par in doc.paragraphs:
        if "{NOME}" in par.text or "{CPF}" in par.text:
            replace_in_runs(par.runs, "{NOME}", nome)
            replace_in_runs(par.runs, "{CPF}", cpf)

    for table in doc.tables:
        for linha in table.rows:
            for celula in linha.cells:
                if "{NOME}" in celula.text or "{CPF}" in celula.text:
                    for par in celula.paragraphs:
                        replace_in_runs(par.runs, "{NOME}", nome)
                        replace_in_runs(par.runs, "{CPF}", cpf)

    doc.save(caminho_saida)