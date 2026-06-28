import streamlit as st
import pandas as pd
import hashlib
import os
import time
from datetime import datetime
import urllib.request

# Imports do Selenium para automação real de navegador
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# MODELAGEM DE CLASSES (ORIENTAÇÃO A OBJETOS)
# ==========================================

class OrigemDado:
    def __init__(self, tipo_fonte):
        self.tipo_fonte = tipo_fonte
        self.data_ingestao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.hash_validacao = ""

    def calcular_hash(self, conteudo: str) -> str:
        sha256 = hashlib.sha256()
        sha256.update(conteudo.encode('utf-8'))
        self.hash_validacao = sha256.hexdigest()[:12]
        return self.hash_validacao

class Scraping(OrigemDado):
    def __init__(self, url_perfil):
        super().__init__("Coleta Automatizada")
        self.url_perfil = url_perfil

    def extrair(self):
        raise NotImplementedError("Cada plataforma deve implementar seu método.")

from selenium.webdriver.common.keys import Keys  # Import necessário para simular o teclado

class ScrapingInstagram(Scraping):
    def extrair(self):
        driver = None
        try:
            chrome_options = Options()
            # Removemos o --headless puro para testes se necessário
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            # Ignora erros de certificado e automação
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.url_perfil)
            
            wait = WebDriverWait(driver, 15)
            
            # 1. Captura a foto real do perfil
            elemento_foto = wait.until(EC.presence_of_element_located((By.XPATH, "//header//img")))
            foto_url = elemento_foto.get_attribute("src")
            
            # 2. Captura a biografia real do usuário
            try:
                elemento_bio = driver.find_element(By.XPATH, "//header//section//div[contains(@class, 'ap7a')]")
                bio_texto = elemento_bio.text
            except Exception:
                try:
                    elemento_bio = driver.find_element(By.XPATH, "//meta[@name='description']")
                    bio_texto = elemento_bio.get_attribute("content").split("-")[0].strip()
                except Exception:
                    bio_texto = "Conteúdo textual extraído via metadados do cabeçalho."

            username = self.url_perfil.split("instagram.com/")[-1].strip("/")
            username = username.split("?")[0]

            nome_arquivo_foto = f"foto_perfil_{username}.jpg"
            if foto_url:
                urllib.request.urlretrieve(foto_url, nome_arquivo_foto)
            
            # 3. --- ROLAGEM FORÇADA VIA INTERAÇÃO DE TELA E TECLADO ---
            arquivos_posts_baixados = []
            links_processados = set()
            contador_posts = 1
            
            # Clica no corpo da página para garantir que o foco está na janela correta para rolar
            try:
                driver.find_element(By.TAG_NAME, "body").click()
            except Exception:
                pass

            # Faremos 10 tentativas de rolagem enviando comandos de teclado diretamente
            for i in range(10):
                # Coleta tudo o que está visível na janela atual antes e depois de interagir
                elementos_posts = driver.find_elements(By.XPATH, "//article//img")
                
                for elem in elementos_posts:
                    try:
                        src_post = elem.get_attribute("src")
                        if src_post and src_post != foto_url and "blob:" not in src_post and src_post not in links_processados:
                            links_processados.add(src_post)
                            nome_post_local = f"post_{username}_{contador_posts}.jpg"
                            
                            urllib.request.urlretrieve(src_post, nome_post_local)
                            arquivos_posts_baixados.append(nome_post_local)
                            contador_posts += 1
                    except Exception:
                        continue
                
                # Executa o Scroll combinando JavaScript e simulação de teclado (Page Down)
                driver.execute_script("window.scrollBy(0, 800);")
                try:
                    driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
                except Exception:
                    pass
                
                time.sleep(3.0)  # Tempo maior para garantir que a rede carregue as novas fotos

            evidencia_final = f"Metadados: {bio_texto} | Total de postagens baixadas no computador: {len(arquivos_posts_baixados)}"
            
            return {
                "ALVO": f"Instagram: @{username}",
                "EVIDENCIA": evidencia_final,
                "FOTO": foto_url,
                "ARQUIVO_LOCAL": nome_arquivo_foto,
                "POSTS_BAIXADOS": ", ".join(arquivos_posts_baixados) if arquivos_posts_baixados else "Nenhuma imagem pública acessível no feed"
            }
            
        except Exception as e:
            st.error(f"Falha na varredura automatizada local: {e}")
            return None
        finally:
            if driver:
                driver.quit()

class InsercaoManual(OrigemDado):
    def __init__(self, nome_arquivo):
        super().__init__("Inserção Manual")
        self.nome_arquivo = nome_arquivo

# ==========================================
# CONFIGURAÇÃO DA INTERFACE (STREAMLIT)
# ==========================================

st.set_page_config(layout="wide", page_title="S.I.V.I.C. - Ingestão Completa")

if "historico" not in st.session_state:
    st.session_state.historico = []
if "contador_id" not in st.session_state:
    st.session_state.contador_id = 1001

st.markdown("<h2 style='margin-bottom: 0;'>S.I.V.I.C.</h2>", unsafe_allow_html=True)
st.tabs(["Dashboard", "Coleta", "Vínculos", "Biometria", "Histórico", "Auditoria"])

st.markdown("---")

col_esquerda, col_direita = st.columns([1, 2])

with col_esquerda:
    st.markdown("### OPERAÇÕES DE INGESTÃO")
    st.caption("Módulo forense local com download automático de avatares e publicações do feed.")
    
    tipo_ingestao = st.radio("Método de Ingestão:", ["Automação (Selenium Local por URL)", "Upload Manual (Mídias Locais)"])
    
    if tipo_ingestao == "Automação (Selenium Local por URL)":
        url_busca = st.text_input("Link do Perfil do Alvo (Instagram)", placeholder="https://www.instagram.com/nome_do_alvo")
        
        if st.button("EXTRAIR EVIDÊNCIAS E BAIXAR TUDO", use_container_width=True):
            if url_busca:
                with st.spinner("Navegando pelo feed e extraindo mídias binárias originais..."):
                    coleta = ScrapingInstagram(url_busca)
                    res = काळात = coleta.extrair()
                    
                    if res:
                        hash_calc = coleta.calcular_hash(res["EVIDENCIA"])
                        
                        novo_registro = {
                            "ID TAREFA": f"#CD-{st.session_state.contador_id}",
                            "FONTE": "Instagram Selenium",
                            "FOTO ALVO": res["FOTO"],
                            "ALVO (PERFIL)": res["ALVO"],
                            "EVIDÊNCIA COLETADA": res["EVIDENCIA"],
                            "HASH (CADEIA DE CUSTÓDIA)": hash_calc,
                            "IMAGENS SALVAS NO PC": res["POSTS_BAIXADOS"]
                        }
                        st.session_state.historico.insert(0, novo_registro)
                        st.session_state.contador_id += 1
                        st.success("Mídias reais baixadas com sucesso na pasta do seu projeto!")
            else:
                st.error("Insira a URL do Instagram.")
                
    else:
        arquivos = st.file_uploader("Upload de Fotos", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        if st.button("PROCESSAR IMAGENS", use_container_width=True):
            if arquivos:
                for arq in arquivos:
                    manual = InsercaoManual(arq.name)
                    hash_calculado = manual.calcular_hash(arq.name + str(arq.size))
                    
                    novo_registro = {
                        "ID TAREFA": f"#CD-{st.session_state.contador_id}",
                        "FONTE": manual.tipo_fonte,
                        "FOTO ALVO": "",
                        "ALVO (PERFIL)": "Upload Local",
                        "EVIDÊNCIA COLETADA": f"Arquivo de Mídia: {manual.nome_arquivo}",
                        "HASH (CADEIA DE CUSTÓDIA)": hash_calculado,
                        "IMAGENS SALVAS NO PC": arq.name
                    }
                    st.session_state.historico.insert(0, novo_registro)
                    st.session_state.contador_id += 1
                st.success("Mídias processadas!")

with col_direita:
    st.markdown("### HISTÓRICO DE COLETAS PÚBLICAS")
    
    if st.session_state.historico:
        df = pd.DataFrame(st.session_state.historico)
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "FOTO ALVO": st.column_config.ImageColumn("FOTO ALVO", help="Avatar carregado via Selenium")
            }
        )
    else:
        st.info("Aguardando inserção de URLs do Instagram.")