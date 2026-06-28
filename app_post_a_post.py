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
from selenium.webdriver.common.keys import Keys

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
    def __init__(self, url_perfil, pasta_destino):
        super().__init__("Coleta Automatizada")
        self.url_perfil = url_perfil
        self.pasta_destino = pasta_destino

    def extrair(self):
        raise NotImplementedError("Cada plataforma deve implementar seu método.")

class ScrapingInstagram(Scraping):
    def __init__(self, url_perfil, pasta_destino, driver_compartilhado=None):
        super().__init__(url_perfil, pasta_destino)
        self.driver = driver_compartilhado

    def extrair(self):
        try:
            if not os.path.exists(self.pasta_destino):
                os.makedirs(self.pasta_destino)

            driver = self.driver
            wait = WebDriverWait(driver, 12)
            
            if driver.current_url != self.url_perfil:
                driver.get(self.url_perfil)
                time.sleep(3)

            # --- CONTRA STORIES ABERTOS ---
            try:
                botao_fechar_story = driver.find_element(By.XPATH, "//*[@aria-label='Fechar' or @aria-label='Close']|//*[local-name()='svg' and @aria-label='Fechar']/..")
                botao_fechar_story.click()
                time.sleep(1.5)
            except Exception:
                pass

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
                    bio_texto = "Conteúdo textual extraído via metadados sob sessão ativa."

            username = self.url_perfil.split("instagram.com/")[-1].strip("/")
            username = username.split("?")[0]

            nome_arquivo_foto = os.path.join(self.pasta_destino, f"foto_perfil_{username}.jpg")
            if foto_url:
                urllib.request.urlretrieve(foto_url, nome_arquivo_foto)
            
            # 3. --- EXTRAÇÃO DE IMAGENS E LINKS DOS POSTS ---
            links_posts_alvo = []
            links_processados = set()
            contador_posts = 1
            
            st.info("🔍 Mapeando a estrutura do feed e links das mídias...")
            
            for scroll in range(5):
                elementos_links = driver.find_elements(By.XPATH, "//main//a[contains(@href, '/p/')]")
                
                for el in elementos_links:
                    try:
                        link_href = el.get_attribute("href")
                        elemento_img = el.find_element(By.TAG_NAME, "img")
                        src_post = elemento_img.get_attribute("src")
                        
                        if src_post and src_post != foto_url and "blob:" not in src_post and src_post not in links_processados:
                            links_processados.add(src_post)
                            links_posts_alvo.append((link_href, src_post))
                            
                            nome_post_local = os.path.join(self.pasta_destino, f"post_{username}_{contador_posts}.jpg")
                            urllib.request.urlretrieve(src_post, nome_post_local)
                            contador_posts += 1
                    except Exception:
                        continue
                
                driver.execute_script("window.scrollBy(0, 1200);")
                time.sleep(2.5)

            # 4. --- MINERAÇÃO FORENSE DE COMENTÁRIOS ---
            st.info(f"💬 Iniciando extração de comentários de {len(links_posts_alvo)} posts localizados...")
            total_comentarios_coletados = 0
            
            for index, (link_completo, _) in enumerate(links_posts_alvo, start=1):
                try:
                    driver.get(link_completo)
                    time.sleep(3)
                    
                    elementos_comentarios = driver.find_elements(By.XPATH, "//ul[contains(@class, 'a9z0')]//div[contains(@class, 'a9z1')]//span")
                    
                    if not elementos_comentarios:
                        elementos_comentarios = driver.find_elements(By.XPATH, "//article//span[text()]/..")
                    
                    comentarios_texto = []
                    for c in elementos_comentarios:
                        txt = c.text.strip()
                        if txt and len(txt) > 1 and txt not in comentarios_texto:
                            comentarios_texto.append(txt)
                    
                    if comentarios_texto:
                        nome_txt_comentarios = os.path.join(self.pasta_destino, f"comentarios_post_{username}_{index}.txt")
                        with open(nome_txt_comentarios, "w", encoding="utf-8") as f:
                            f.write(f"--- COMENTÁRIOS DO POST {index} ({link_completo}) ---\n")
                            f.write(f"Coletado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                            for idx, com_raw in enumerate(comentarios_texto, start=1):
                                f.write(f"[{idx}] {com_raw}\n")
                        
                        total_comentarios_coletados += len(comentarios_texto)
                except Exception:
                    continue

            evidencia_final = f"Metadados: {bio_texto} | Posts baixados: {len(links_posts_alvo)} | Total de comentários catalogados: {total_comentarios_coletados}"
            
            return {
                "ALVO": f"Instagram: @{username}",
                "EVIDENCIA": evidencia_final,
                "FOTO": foto_url,
                "POSTS_BAIXADOS": f"{len(links_posts_alvo)} mídias e relatórios de comentários salvos com sucesso em: {self.pasta_destino}"
            }
            
        except Exception as e:
            st.error(f"Falha na varredura automatizada local: {e}")
            return None

class InsercaoManual(OrigemDado):
    def __init__(self, nome_arquivo):
        super().__init__("Inserção Manual")
        self.nome_arquivo = nome_arquivo

# ==========================================
# CONFIGURAÇÃO DA INTERFACE (STREAMLIT)
# ==========================================

st.set_page_config(layout="wide", page_title="S.I.V.I.C. - Ingestão de Metadados")

if "historico" not in st.session_state:
    st.session_state.historico = []
if "contador_id" not in st.session_state:
    st.session_state.contador_id = 1001
if "driver_ativo" not in st.session_state:
    st.session_state.driver_ativo = None

st.markdown("<h2 style='margin-bottom: 0;'>S.I.V.I.C.</h2>", unsafe_allow_html=True)
st.tabs(["Dashboard", "Coleta", "Vínculos", "Biometria", "Histórico", "Auditoria"])

st.markdown("---")

col_esquerda, col_direita = st.columns([1, 2])

with col_esquerda:
    st.markdown("### OPERAÇÕES DE INGESTÃO")
    st.caption("Módulo avançado para extração simultânea de arquivos binários e dados textuais.")
    
    tipo_ingestao = st.radio("Método de Ingestão:", ["Automação (Selenium Local por URL)", "Upload Manual (Mídias Locais)"])
    
    if tipo_ingestao == "Automação (Selenium Local por URL)":
        url_busca = st.text_input("Link do Perfil do Alvo (Instagram)", placeholder="https://www.instagram.com/nome_do_alvo")
        
        caminho_computador = st.text_input(
            "Pasta do PC onde deseja salvar as fotos:", 
            value=r"C:\projetos\UFRN\SIVIC\sivic_app\midias_coletadas"
        )
        
        # PASSO 1: Iniciar e abrir o navegador para login
        if st.button("PASSO 1: ABRIR NAVEGADOR PARA AUTENTICAÇÃO", use_container_width=True):
            if url_busca:
                try:
                    if st.session_state.driver_ativo:
                        st.session_state.driver_ativo.quit()
                        
                    chrome_options = Options()
                    chrome_options.add_argument("--start-maximized")
                    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                    
                    pasta_perfil_robo = os.path.join(os.getcwd(), "perfil_robo_chrome")
                    chrome_options.add_argument(f"--user-data-dir={pasta_perfil_robo}")
                    
                    driver = webdriver.Chrome(options=chrome_options)
                    driver.get(url_busca)
                    
                    st.session_state.driver_ativo = driver
                    st.info("👉 Janela aberta! Faça seu login normalmente. Quando estiver vendo o perfil do alvo com as mídias carregadas, clique no Passo 2.")
                except Exception as e:
                    st.error(f"Erro ao iniciar navegador: {e}")
            else:
                st.error("Insira a URL do alvo.")
        
        # PASSO 2: Iniciar extração profunda de posts e comentários
        if st.button("PASSO 2: CONTA LOGADA, INICIAR EXTRAÇÃO EM MASSA", use_container_width=True, type="primary"):
            if st.session_state.driver_ativo and url_busca and caminho_computador:
                with st.spinner("Varrendo o feed e extraindo comentários de cada post. Aguarde..."):
                    coleta = ScrapingInstagram(url_busca, caminho_computador, st.session_state.driver_ativo)
                    res = coleta.extrair()
                    
                    if res:
                        hash_calc = coleta.calcular_hash(res["EVIDENCIA"])
                        
                        novo_registro = {
                            "ID TAREFA": f"#CD-{st.session_state.contador_id}",
                            "FONTE": "Instagram OSINT (Posts + Comentários)",
                            "FOTO ALVO": res["FOTO"],
                            "ALVO (PERFIL)": res["ALVO"],
                            "EVIDÊNCIA COLETADA": res["EVIDENCIA"],
                            "HASH (CADEIA DE CUSTÓDIA)": hash_calc,
                            "LOCAL DE SALVAMENTO": res["POSTS_BAIXADOS"]
                        }
                        st.session_state.historico.insert(0, novo_registro)
                        st.session_state.contador_id += 1
                        st.success(f"Extração Completa! Fotos e relatórios salvos em: {caminho_computador}")
                        
                        st.session_state.driver_ativo.quit()
                        st.session_state.driver_ativo = None
            else:
                st.error("Abra o navegador pelo Passo 1 antes de iniciar o Passo 2.")
                
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
                        "LOCAL DE SALVAMENTO": "Upload Manual via Web"
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
        st.info("Aguardando ativação do fluxo assistido.")