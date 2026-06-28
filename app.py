import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime


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

class ScrapingOSINT(OrigemDado):
    def __init__(self, url_alvo, profundidade):
        super().__init__("Scraping (OSINT)")
        self.url_alvo = url_alvo
        self.profundidade = profundidade

class InsercaoManual(OrigemDado):
    def __init__(self, nome_arquivo):
        super().__init__("Inserção Manual")
        self.nome_arquivo = nome_arquivo


st.set_page_config(layout="wide", page_title="S.I.V.I.C. - Ingestão")

if "historico" not in st.session_state:
    st.session_state.historico = [
        {"ID": "#CD-9021", "FONTE": "Scraping (OSINT)", "ALVO/ARQUIVO": "https://twitter.com/suspect_alpha", "DATA/HORA": "2023-10-27 14:32:11", "HASH": "a3f5b7c9e1d2", "STATUS": "CONCLUÍDO"},
        {"ID": "#CD-9020", "FONTE": "Scraping (OSINT)", "ALVO/ARQUIVO": "https://facebook.com/public_group_x", "DATA/HORA": "2023-10-27 13:15:00", "HASH": "7e2c9b1a4f8d", "STATUS": "EM ANDAMENTO"},
        {"ID": "#CD-9019", "FONTE": "Inserção Manual", "ALVO/ARQUIVO": "foto_local_suspeito.png", "DATA/HORA": "2023-10-27 10:05:44", "HASH": "92f8a1c3d7e5", "STATUS": "CONCLUÍDO"},
        {"ID": "#CD-9018", "FONTE": "Scraping (OSINT)", "ALVO/ARQUIVO": "http://darknet_forum_xyz.onion", "DATA/HORA": "2023-10-26 23:59:12", "HASH": "000000000000", "STATUS": "FALHA"}
    ]
if "contador_id" not in st.session_state:
    st.session_state.contador_id = 9022

st.markdown("<h2 style='margin-bottom: 0;'>S.I.V.I.C.</h2>", unsafe_allow_html=True)
abas = ["Dashboard", "Coleta", "Vínculos", "Biometria", "Histórico", "Auditoria"]
st.tabs(abas)

st.markdown("---")

col_esquerda, col_direita = st.columns([1, 2])

with col_esquerda:
    st.markdown("### COLETA DE DADOS")
    st.caption("Configure o alvo para extração de dados públicos ou faça a inserção local.")
    
    tipo_ingestao = st.radio("Método de Ingestão:", ["Automação (Scraping/OSINT)", "Upload Manual (Mídias Locais)"])
    
    if tipo_ingestao == "Automação (Scraping/OSINT)":
        url = st.text_input("URL da Rede Social / Alvo", placeholder="https://exemplo.com/perfil")
        profundidade = st.selectbox("Profundidade da Extração", ["Nível 1 (Apenas Perfil)", "Nível 2 (Perfil e Seguidores)"])
        
        if st.button("INICIAR RASPAGEM", use_container_width=True):
            if url:
                coleta = ScrapingOSINT(url, profundidade)
                hash_calculado = coleta.calcular_hash(url)
                
                novo_registro = {
                    "ID": f"#CD-{st.session_state.contador_id}",
                    "FONTE": coleta.tipo_fonte,
                    "ALVO/ARQUIVO": coleta.url_alvo,
                    "DATA/HORA": coleta.data_ingestao,
                    "HASH": hash_calculado,
                    "STATUS": "CONCLUÍDO"
                }
                st.session_state.historico.insert(0, novo_registro)
                st.session_state.contador_id += 1
                st.success("Raspagem concluída com sucesso!")
            else:
                st.error("Insira uma URL válida.")
                
    else:
        arquivos = st.file_uploader("Selecione os arquivos de imagem", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        
        if st.button("PROCESSAR ARQUIVOS", use_container_width=True):
            if arquivos:
                for arq in arquivos:
                    manual = InsercaoManual(arq.name)
                    hash_calculado = manual.calcular_hash(arq.name + str(arq.size))
                    
                    novo_registro = {
                        "ID": f"#CD-{st.session_state.contador_id}",
                        "FONTE": manual.tipo_fonte,
                        "ALVO/ARQUIVO": manual.nome_arquivo,
                        "DATA/HORA": manual.data_ingestao,
                        "HASH": hash_calculado,
                        "STATUS": "CONCLUÍDO"
                    }
                    st.session_state.historico.insert(0, novo_registro)
                    st.session_state.contador_id += 1
                st.success(f"{len(arquivos)} arquivo(s) processados!")
            else:
                st.error("Nenhum arquivo selecionado.")

with col_direita:
    st.markdown("### HISTÓRICO DE COLETAS PÚBLICAS")
    st.caption("Últimas tarefas registradas pelo sistema com blindagem de Cadeia de Custódia.")
    
    df = pd.DataFrame(st.session_state.historico)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.download_button(
        label="EXPORTAR RELATÓRIO [CSV]",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='historico_ingestao_sivic.csv',
        mime='text/csv',
    )