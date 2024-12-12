import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from typing import List, Tuple, Dict, Union
from selenium.webdriver.chrome.options import Options

class Searcher():
    def __init__(self, visible_chrome: bool = True):
        self.config_path = 'config/searcher.json'
        self.config = self.load_cfg()
        chrome_options = Options()
        if not visible_chrome: 
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--disable-webgl")
        self.driver = webdriver.Chrome(chrome_options)
    
    def load_cfg(self) -> dict:
        with open(self.config_path, 'r') as file:
            return json.load(file)
        
    def get_url(self)-> str:
        return self.config['site_receita']
    
    def set_url(self, url: str)-> None:
        self.config['site_receita'] = url
        
    def get_cpf_id(self) -> str:
        return self.config["cpf_field_id"]
    
    def set_cpf_id(self, cpf: str) -> None:
        self.config["cpf_field_id"] = cpf
        
    def get_data_nasc_id(self) -> str:
        return self.config["data_nasc_id"]
    
    def set_data_nasc_id(self, data: str) -> None:
        self.config["data_nasc_id"] = data
    
    def get_consultar_id(self) -> str:
        return self.config["consultar_id"]
    
    def set_consultar_id(self, consultar_id: str) -> None:
        self.config["consultar_id"] = consultar_id

    def save_cfg(self):
        with open(self.config_path, 'w') as file:
            json.dump(self.config, file)
            
    def close(self):
        self.save_cfg()
        self.driver.quit()
        
    def search_by_batch(self, lista: List[Tuple[str, str]], callback) -> List[Dict[str, str]]:
        dados = []
        for pessoa in lista:
            if "x" in str.lower(pessoa[0]):
                new_cpfs = self.try_cpf(pessoa[0])
                for new_cpf in new_cpfs:
                    dados.extend(self.search(new_cpf, pessoa[1], callback))
                continue
            dados.extend(self.search(pessoa[0], pessoa[1], callback))
        return dados
            
    def search(self, cpf: str, data_nasc: str, callback, check_tentativas = 1)-> List[Dict[str, str]]:
        if "x" in str.lower(data_nasc):
            dados = []
            dates = self.try_nasc(data_nasc, [])
            for date in dates:
                dados.extend(self.search(cpf,date,callback))
            return dados
        if check_tentativas > 3: return [{"Erro": "Não foi possível verificar o checkbox"}]
        callback("Direcionando para a receita federal")
        self.driver.get(self.get_url())
        callback("Preenchendo CPF")
        cpf_field = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, self.get_cpf_id()))
        )
        cpf_field.send_keys(cpf)
        callback("Preenchendo Data de Nascimento")
        data_nasc_field = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located((By.ID, self.get_data_nasc_id()))
        )
        data_nasc_field.send_keys(data_nasc)
        callback("Verificando o checkbox")
        iframe = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#hcaptcha > iframe"))
        )
        self.driver.switch_to.frame(iframe)
        checkbox = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "checkbox"))
        )
        checkbox.click()
        WebDriverWait(self.driver, 15).until(
            lambda driver: checkbox.get_attribute("aria-checked") == "true"
        )
        if checkbox.get_attribute("aria-checked") != "true":
            callback(f"Erro ao fazer o checkbox para {cpf}. Tentativas restantes: {3-check_tentativas}")
            return self.search(cpf, data_nasc, callback, check_tentativas+1)
        self.driver.switch_to.default_content()
        callback("Buscando dados")        
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, self.get_consultar_id()))
        ).click()
        
        try:
            erro_data_nasc = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#content-core > div > div > div.clConteudoCentro > span > h4 > b"))
            )
            if erro_data_nasc:
                return [{"Erro": "Data de nascimento incorreta. Verifique as informações e tente novamente."}]
        except:
            pass
        
        try:
            erro_cpf = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#content-core > div > div > div.clConteudoCentro > span > h4"))
            )
            if erro_cpf:
                return [{"Erro": "CPF incorreto. Verifique o CPF e tente novamente."}]
        except:
            pass
        
        try:
            container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "clConteudoEsquerda"))
            )
            linhas = container.text.split("\n")
            for linha in linhas:
                if "Nome" in linha:
                    nome = " ".join(linha.split(":")[1:]).strip()
                elif "Data de Nascimento" in linha:
                    data = linha.split(":")[1].strip()
                elif "No do CPF" in linha:
                    n_cpf = linha.split(":")[1].strip()
            return [{
                "cpf": n_cpf,
                "nome": nome,
                "nasc": data
            }]
        except Exception as e:
            return [{
                "Erro": str(e)
            }]
            
    @staticmethod
    def valida_cpf(cpf: str) -> bool:
        cpf = ''.join(filter(str.isdigit, cpf))
        if len(cpf) != 11:
            return False
        if cpf == cpf[0] * 11:
            return False
        soma = 0
        for i in range(9):
            soma += int(cpf[i]) * (10 - i)
        primeiro_digito = (soma * 10) % 11
        if primeiro_digito == 10 or primeiro_digito == 11:
            primeiro_digito = 0
        soma = 0
        for i in range(10):
            soma += int(cpf[i]) * (11 - i)
        segundo_digito = (soma * 10) % 11
        if segundo_digito == 10 or segundo_digito == 11:
            segundo_digito = 0
        if cpf[-2:] == f"{primeiro_digito}{segundo_digito}":
            return True
        return False
    
    @staticmethod
    def try_cpf(cpf: str):
        gaps = []
        for i, char in enumerate(cpf):
            if str.lower(char) == "x":
                gaps.append(i)
        cpf_list = list(cpf)
        if len(gaps)>0:
            possibles = Searcher.recursive_replace(cpf_list,gaps,gaps[0])
            return possibles
        return [cpf]
    
    @staticmethod
    def recursive_replace(cpf: List[str], gaps: List[int], gap: int):
        valid_result = []
        gaps.remove(gap)
        for i in range(10):
            cpf[gap] = str(i)
            if len(gaps) == 0:
                if Searcher.valida_cpf("".join(cpf)):
                    valid_result.append("".join(cpf))
            else:
                valid_result.extend(Searcher.recursive_replace(cpf,gaps.copy(),gaps[0]))
        return valid_result
    
    @staticmethod
    def try_nasc(nasc: str, possibles: List[str] = []):
        dia = nasc[0:2]
        mes = nasc[2:4]
        ano = nasc[4:]
        if str.lower(dia[0]) == "x":
            for i in range(4):
                Searcher.try_nasc(f"{i}{dia[1]}{mes}{ano}", possibles)
        elif str.lower(dia[1]) == "x":
            for i in range(10):
                Searcher.try_nasc(f"{dia[0]}{i}{mes}{ano}", possibles)
        elif str.lower(mes[0]) == "x":
            for i in range(2):
                Searcher.try_nasc(f"{dia}{i}{mes[1]}{ano}", possibles)
        elif str.lower(mes[1]) == "x":
            for i in range(10):
                Searcher.try_nasc(f"{dia}{mes[0]}{i}{ano}", possibles)
        elif str.lower(ano[0]) == "x":
            for i in range(1,3):
                Searcher.try_nasc(f"{dia}{mes}{i}{ano[1:]}", possibles)
        elif str.lower(ano[1]) == "x":
            for i in [9,0]:
                Searcher.try_nasc(f"{dia}{mes}{ano[0]}{i}{ano[2:]}", possibles)
        elif str.lower(ano[2]) == "x":
            for i in range(10):
                Searcher.try_nasc(f"{dia}{mes}{ano[0:2]}{i}{ano[3]}", possibles)
        elif str.lower(ano[3]) == "x":
            for i in range(10):
                Searcher.try_nasc(f"{dia}{mes}{ano[0:3]}{i}", possibles)
        if not "x" in str.lower(f"{dia}{mes}{ano}"):
            possibles.append(f"{dia}{mes}{ano}")
        return possibles