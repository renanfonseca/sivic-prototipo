import streamlit as st
import pandas as pd
import hashlib
import os
import time
from datetime import datetime
import urllib.request

# Imports do Selenium para automação real de navegador
from selenium import webdriver
from selenium.webdriver import Chrome
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
            
            st.info("🔍 Mapeando a estrutura do feed e salvando mídias originais...")
            
            for scroll in range(4):
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

            # 4. --- MINERAÇÃO CIRÚRGICA DE ENGAJAMENTO (COMENTÁRIOS E CURTIDAS) ---
            st.info(f"💬 Analisando interações em {len(links_posts_alvo)} posts localizados...")
            total_comentarios_coletados = 0
            
            for index, (link_completo, _) in enumerate(links_posts_alvo, start=1):
                try:
                    driver.get(link_completo)
                    time.sleep(5) 
                    
                    # Força uma rolagem interna no card para renderizar os dados assíncronos
                    driver.execute_script("window.scrollBy(0, 200);")
                    time.sleep(1.5)

                    # A. Extração do Total de Curtidas do Post
                    texto_curtidas = "Não foi possível extrair (Curtidas ocultas ou carrossel bloqueado)"
                    try:
                        # O Instagram agrupa as curtidas em seções estruturadas abaixo dos botões de interação
                        elemento_curtidas = driver.find_element(By.XPATH, "//article//section[contains(., 'curtida') or contains(., 'like')]//span | //article//section//div[text()]")
                        if elemento_curtidas:
                            texto_curtidas = elemento_curtidas.text.strip()
                    except Exception:
                        try:
                            # Fallback alternativo para o contador de curtidas
                            elemento_curtidas = driver.find_element(By.XPATH, "//a[contains(@href, 'liked_by')]/span")
                            texto_curtidas = elemento_curtidas.text.strip() + " curtidas"
                        except Exception:
                            pass

                    # B. Extração Cirúrgica de Autores e Comentários
                    # Mapeia cada linha de comentário (<li>) dentro da lista principal (<ul>)
                    linhas_comentarios = driver.find_elements(By.XPATH, "//ul//li[contains(@class, '')]")
                    
                    comentarios_estruturados = []
                    for linha in linhas_comentarios:
                        try:
                            # Pega o link do autor do comentário específico (dentro da linha atual)
                            user_elem = linha.find_element(By.XPATH, ".//h3//a | .//h2//a | .//a[contains(@href, '/') and @role='link']")
                            autor_comentario = user_elem.text.strip()
                            
                            # Pega o bloco de texto do comentário associado a esse autor
                            text_elem = linha.find_element(By.XPATH, ".//span[not(ancestor::h3) and not(ancestor::h2)]")
                            texto_comentario = text_elem.text.strip()
                            
                            if autor_comentario and texto_comentario:
                                # Filtra interações falsas do sistema (ex: texto do botão responder)
                                if not any(texto_comentario.startswith(ignorar) for ignorar in ["Ver respostas", "Responder", "Ver tudo"]):
                                    registro = f"Usuário: @{autor_comentario} | Comentou: \"{texto_comentario}\""
                                    if registro not in comentarios_estruturados:
                                        comentarios_estruturados.append(registro)
                        except Exception:
                            continue

                    # Criação do arquivo detalhado de inteligência forense para o post atual
                    nome_txt_comentarios = os.path.join(self.pasta_destino, f"dados_post_{username}_{index}.txt")
                    with open(nome_txt_comentarios, "w", encoding="utf-8") as f:
                        f.write(f"==================================================\n")
                        f.write(f"        S.I.V.I.C. - RELATÓRIO DE INTERAÇÕES\n")
                        f.write(f"==================================================\n")
                        f.write(f"URL da Evidência: {link_completo}\n")
                        f.write(f"Data/Hora da Extração: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Alvo Monitorado: @{username}\n")
                        f.write(f"Métrica de Engajamento: {texto_curtidas}\n")
                        f.write("-" * 50 + "\n\n")
                        f.write(f"--- LISTA DE USUÁRIOS QUE INTERAGIRAM / COMENTARAM ---\n")
                        
                        if comentarios_estruturados:
                            for idx, item in enumerate(comentarios_estruturados, start=1):
                                f.write(f"[{idx}] {item}\n")
                            total_comentarios_coletados += len(comentarios_estruturados)
                        else:
                            f.write("Nenhum comentário textual detectado neste post durante o rastreamento.\n")
                            
                except Exception:
                    continue

            evidencia_final = f"Metadados: {bio_texto} | Mídias extraídas: {len(links_posts_alvo)} | Interações catalogadas no computador."
            
            return {
                "ALVO": f"Instagram: @{username}",
                "EVIDENCIA": evidencia_final,
                "FOTO": foto_url,
                "POSTS_BAIXADOS": f"{len(links_posts_alvo)} posts analisados com sucesso. Verifique os arquivos de imagem e relatórios textuais (.txt) na pasta: {self.pasta_destino}"
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
    st.caption("Módulo forense avançado para mineração de arquivos binários, curtidas e autoria de comentários.")
    
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
                    
                    driver = Chrome(options=chrome_options)
                    driver.get(url_busca)
                    
                    st.session_state.driver_ativo = driver
                    st.info("👉 Janela aberta! Se o Instagram pedir autenticação, conecte na sua conta. Quando as mídias do alvo carregarem na tela, clique no Passo 2.")
                except Exception as e:
                    st.error(f"Erro ao iniciar navegador: {e}")
            else:
                st.error("Insira a URL do alvo.")
        
        # PASSO 2: Iniciar extração profunda de posts, autores e comentários
        if st.button("PASSO 2: CONTA LOGADA, INICIAR EXTRAÇÃO EM MASSA", use_container_width=True, type="primary"):
            if st.session_state.driver_ativo and url_busca and caminho_computador:
                with st.spinner("Navegando pelos posts, extraindo mídias, curtidas e associando autores aos comentários..."):
                    coleta = ScrapingInstagram(url_busca, caminho_computador, st.session_state.driver_ativo)
                    res = coleta.extrair()
                    
                    if res:
                        hash_calc = coleta.calcular_hash(res["EVIDENCIA"])
                        
                        novo_registro = {
                            "ID TAREFA": f"#CD-{st.session_state.contador_id}",
                            "FONTE": "Instagram OSINT (Mídias + Interações)",
                            "FOTO ALVO": res["FOTO"],
                            "ALVO (PERFIL)": res["ALVO"],
                            "EVIDÊNCIA COLETADA": res["EVIDENCIA"],
                            "HASH (CADEIA DE CUSTÓDIA)": hash_calc,
                            "LOCAL DE SALVAMENTO": res["POSTS_BAIXADOS"]
                        }
                        st.session_state.historico.insert(0, novo_registro)
                        st.session_state.contador_id += 1
                        st.success("Dados de engajamento e arquivos originais salvos com sucesso!")
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