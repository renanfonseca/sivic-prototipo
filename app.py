import streamlit as st
import pandas as pd
import hashlib
import json
from datetime import datetime
import urllib.request

# ==========================================
# MODELAGEM DE CLASSES (ORIENTAÇÃO A OBJETOS)
# ==========================================

class OrigemDado:
    def __init__(self, tipo_fonte):
        self.tipo_fonte = tipo_fonte
        self.data_ingestao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.hash_validacao = ""

    def calcular_hash(self, conteudo: str) -> str:
        # Garante a integridade da Cadeia de Custódia computando o Hash legítimo do dado
        sha256 = hashlib.sha256()
        sha256.update(conteudo.encode('utf-8'))
        self.hash_validacao = sha256.hexdigest()[:12]
        return self.hash_validacao

class ScrapingRedeSocial(OrigemDado):
    def __init__(self, termo_alvo):
        super().__init__("Coleta Automatizada")
        self.termo_alvo = termo_alvo

    def executar_raspagem_rede_social(self):
        """Dispara requisição HTTP real para extrair postagens e usuários reais de fontes públicas"""
        dados_coletados = []
        try:
            # Formata o termo de busca para pesquisar em toda a rede social
            termo_enc = urllib.parse.quote(self.termo_alvo)
            url_api = f"https://www.reddit.com/search.json?q={termo_enc}&limit=5"
            
            # Define um User-Agent para a rede social não bloquear a requisição do servidor
            headers = {'User-Agent': 'SIVIC-Intelligence-Bot/1.0 (Academic Investigation Project)'}
            req = urllib.request.Request(url_api, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                json_data = json.loads(response.read().decode('utf-8'))
            
            # Navega na estrutura de dados do JSON da rede social
            posts = json_data.get("data", {}).get("children", [])
            
            for post in posts:
                data_post = post.get("data", {})
                usuario = data_post.get("author")
                texto = data_post.get("title")
                url_midia = data_post.get("url")
                subreddit = data_post.get("subreddit_name_prefixed")
                
                dados_coletados.append({
                    "PERFIL_ALVO": f"u/{usuario}",
                    "CONTEUDO": f"[{subreddit}] {texto}",
                    "URL_EVIDENCIA": url_midia
                })
        except Exception as e:
            st.error(f"Erro de comunicação com os servidores da rede social: {e}")
        
        return dados_coletados

class InsercaoManual(OrigemDado):
    def __init__(self, nome_arquivo):
        super().__init__("Inserção Manual")
        self.nome_arquivo = nome_arquivo

# ==========================================
# CONFIGURAÇÃO DA INTERFACE (STREAMLIT)
# ==========================================

st.set_page_config(layout="wide", page_title="S.I.V.I.C. - Ingestão Investigativa")

if "historico" not in st.session_state:
    st.session_state.historico = []
if "contador_id" not in st.session_state:
    st.session_state.contador_id = 1001

st.markdown("<h2 style='margin-bottom: 0;'>S.I.V.I.C.</h2>", unsafe_allow_html=True)
abas = ["Dashboard", "Coleta", "Vínculos", "Biometria", "Histórico", "Auditoria"]
st.tabs(abas)

st.markdown("---")

col_esquerda, col_direita = st.columns([1, 2])

with col_esquerda:
    st.markdown("### COLETA DE DADOS ALVO")
    st.caption("Extração automatizada de perfis e evidências digitais em redes abertas.")
    
    tipo_ingestao = st.radio("Método de Ingestão:", ["Automação (Scraping de Rede Social)", "Upload Manual (Mídias Locais)"])
    
    if tipo_ingestao == "Automação (Scraping de Rede Social)":
        termo_busca = st.text_input("Identificador / Termo de Investigação", placeholder="Ex: Nome de usuário, apelido, link ou grupo")
        
        if st.button("INICIAR RASPAGEM EM REDE SOCIAL", use_container_width=True):
            if termo_busca:
                with st.spinner("Conectando à rede externa e quebrando payload de dados..."):
                    coleta = ScrapingRedeSocial(termo_busca)
                    resultados = list(coleta.executar_raspagem_rede_social())
                    
                    if resultados:
                        for res in resultados:
                            # Passa a URL da evidência para a regra de negócio da classe pai computar o Hash
                            hash_calc = coleta.calcular_hash(res["URL_EVIDENCIA"])
                            
                            novo_registro = {
                                "ID TAREFA": f"#CD-{st.session_state.contador_id}",
                                "FONTE": coleta.tipo_fonte,
                                "ALVO (PERFIL)": res["PERFIL_ALVO"],
                                "EVIDÊNCIA COLETADA": res["CONTEUDO"],
                                "HASH (CADEIA DE CUSTÓDIA)": hash_calc,
                                "STATUS": "CONCLUÍDO"
                            }
                            st.session_state.historico.insert(0, novo_registro)
                            st.session_state.contador_id += 1
                        st.success(f"Sucesso! {len(resultados)} postagens e perfis reais indexados.")
                    else:
                        st.warning("Nenhuma evidência pública localizada para este alvo.")
            else:
                st.error("Insira o identificador do alvo para a varredura.")
                
    else:
        arquivos = st.file_uploader("Selecione arquivos de evidência criminal (Fotos de Inteligência)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        
        if st.button("PROCESSAR IMAGENS", use_container_width=True):
            if arquivos:
                for arq in arquivos:
                    manual = InsercaoManual(arq.name)
                    hash_calculado = manual.calcular_hash(arq.name + str(arq.size))
                    
                    novo_registro = {
                        "ID TAREFA": f"#CD-{st.session_state.contador_id}",
                        "FONTE": manual.tipo_fonte,
                        "ALVO (PERFIL)": "Upload Local",
                        "EVIDÊNCIA COLETADA": f"Arquivo de Mídia: {manual.nome_arquivo}",
                        "HASH (CADEIA DE CUSTÓDIA)": hash_calculado,
                        "STATUS": "CONCLUÍDO"
                    }
                    st.session_state.historico.insert(0, novo_registro)
                    st.session_state.contador_id += 1
                st.success(f"{len(arquivos)} arquivo(s) acoplados à cadeia de custódia!")
            else:
                st.error("Selecione ao menos um arquivo válido.")

with col_direita:
    st.markdown("### HISTÓRICO DE COLETAS PÚBLICAS")
    st.caption("Central de custódia e persistência de dados brutos coletados.")
    
    if st.session_state.historico:
        df = pd.DataFrame(st.session_state.historico)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.download_button(
            label="EXPORTAR RELATÓRIO DE EVIDÊNCIAS [CSV]",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='evidencias_sivic.csv',
            mime='text/csv',
        )
    else:
        st.info("Nenhuma evidência capturada até o momento. Utilize o painel esquerdo.")