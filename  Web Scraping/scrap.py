# Importando Bibliotecas.
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas_gbq as pdgbq
from google.oauth2 import service_account
import re
import time
import yaml
import openpyxl

# Carregar Variáveis
with open('config.yaml', 'r') as file:
    # Carrega o conteúdo do arquivo YAML em um dicionário
    config = yaml.safe_load(file)


# Funções
def fechaCookies(driver):
    '''Função para remover a tela de cookies da página web.'''
    try:
        driver.find_element(By.XPATH, "//*[@id='lgpd-consent-widget']/section/div/div[2]/button[1]").click()
    except:
        None

# Defina o User-Agent desejado
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"

# Configure as opções do ChromeDriver com o User-Agent
chrome_options = Options()
chrome_options.add_argument(f'user-agent={user_agent}')

# Criando serviço para se comunicar com o Google Chrome.
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.maximize_window()

# Acessando o site.
driver.get("https://www.catho.com.br/")
time.sleep(2)

#Buscando vagas para um cargo determinado. 
driver.find_element(By.NAME, "q").send_keys(config['CARGO'])
time.sleep(2)

# Fechar tela de cookies
fechaCookies(driver)
time.sleep(2)

# Clica no botão para pesquisar a vaga.
driver.find_element(By.NAME, "submit").click()
time.sleep(2)

# Quantidade total de vagas
anuncios = driver.find_element(By.XPATH, "//*[@id='search-result']/div[1]/p")
quant_anuncios = anuncios.text.split(": ")[1]
total_pgs = round(int(quant_anuncios) // 15)
if total_pgs == 0:
    total_pgs = 1
print(f"Total de anuncios a percorrer:{str(quant_anuncios)}")
print(f"Total de paginas a percorrer: {total_pgs}" )

# Variaveis auxiliares.
lista_df = []
y = 0
pg = 1

# Iniciando o loop.
while pg <= total_pgs:
    y = y + 1

    # Capturando o bloco de vagas.
    ul_element = driver.find_element(By.XPATH, "/html/body/div[1]/div[1]/main/div[3]/div/div/section/ul")
    li_elements = ul_element.find_elements(By.TAG_NAME, "li")

    c = 0
    # Faz um loop por cada li encontrado
    for li in li_elements:
        c += 1
        titulo = driver.find_element(By.XPATH, f"/html/body/div[1]/div[1]/main/div[3]/div/div/section/ul/li[{c}]/article/article/header/div/div[1]/h2/a")
        empresa = driver.find_element(By.XPATH, f"/html/body/div[1]/div[1]/main/div[3]/div/div/section/ul/li[{c}]/article/article/header/div/p")
        salario = driver.find_element(By.XPATH, f"/html/body/div[1]/div[1]/main/div[3]/div/div/section/ul/li[{c}]/article/article/header/div/div[2]/div[1]")
        regiao = driver.find_element(By.XPATH, f"/html/body/div[1]/div[1]/main/div[3]/div/div/section/ul/li[{c}]/article/article/header/div/div[2]/button/a")
        datapublicacao = driver.find_element(By.XPATH, f"/html/body/div[1]/div[1]/main/div[3]/div/div/section/ul/li[{c}]/article/article/header/div/div[2]/time/span")
        
        # continuarlendo = driver.find_element(By.XPATH, f"/html/body/div[1]/div[1]/main/div[3]/div/div/section/ul/li[{c}]/article/article/div/div[1]/button").click

        descricao = driver.find_element(By.XPATH, f"/html/body/div[1]/div[1]/main/div[3]/div/div/section/ul/li[{c}]/article/article/div/div[1]")

        #print(titulo.text, empresa.text, salario.text, regiao.text, datapublicacao.text, descricao.text)
        
        match = re.search(r'\((\d+)\)', regiao.text)
    
        try:
            vagas = match.group(1)
        except:
            None

        df = pd.DataFrame(
            {
                'titulo': [titulo.text]
                ,'empresa': [empresa.text]
                ,'salario': [salario.text]
                ,'regiao': [regiao.text]
                ,'datapublicacao': [datapublicacao.text]
                ,'vagas': vagas
                ,'descricao': [descricao.text]

            }
        )
        # Adiciona dataframes na lista de DF
        lista_df.append(df)       

    # Incremento da pagina
    pg = pg + 1
    if pg <= total_pgs:
        if "page=" in driver.current_url:
            url = driver.current_url.replace("page=" + str(pg-1), "page=" + str(pg))
        else:
            url = driver.current_url + "&page=" + str(pg)

        driver.get(url)
        time.sleep(3)

# Juntar todos os dataframes 
if len(lista_df) > 1:
    df_final = pd.concat(lista_df)
else:
    df_final = lista_df[0]

df_final.head()
df_final = df_final.reset_index(drop=True)
df_final.to_excel("vagas_catho.xlsx",  index=False)
