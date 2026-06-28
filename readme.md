# S.I.V.I.C. - Sistema Inteligente de Vínculos e Identificação Criminal

O **S.I.V.I.C.** é um protótipo de sistema de inteligência voltado para órgãos de segurança pública e polícia judiciária. O objetivo do sistema é otimizar investigações criminais por meio da ingestão automatizada de dados públicos, mapeamento de vínculos em grafos de relacionamento e verificação biométrica facial com garantia de cadeia de custódia.

Este repositório contém o protótipo executável do **Módulo de Ingestão e Ingestão de Dados**, desenvolvido como um MVP (Minimum Viable Product) utilizando Python e a biblioteca Streamlit.

---

## 🚀 Funcionalidades do Módulo de Ingestão

* **Automação (Scraping):** Simulação de extração automatizada de dados de perfis públicos de redes sociais (Instagram, Facebook e YouTube) sem interação ativa com as plataformas.
* **Inserção Manual:** Upload múltiplo de mídias locais (arquivos JPG/PNG) para processamento offline.
* **Garantia de Cadeia de Custódia:** Geração automática de uma assinatura digital única (Código Hash SHA-256) sobre cada dado ou arquivo que entra no sistema, assegurando a integridade e imutabilidade das evidências.
* **Segregação de Fontes:** Identificação clara e transparente no relatório entre dados coletados via automação e inserções manuais.
* **Exportação Auditável:** Geração de relatórios consolidados em formato estruturado protegidos para anexação aos autos de inquéritos policiais.

---

## 🛠️ Arquitetura de Software e OO

O sistema foi desenhado seguindo os princípios de Orientação a Objetos (OO). A estrutura do módulo de ingestão baseia-se em herança e polimorfismo para separar as origens dos dados:

* **`OrigemDado` (Classe Abstrata):** Classe base que define os atributos comuns de auditoria (`tipo_fonte`, `data_ingestao`, `hash_validacao`) e o método genérico `calcular_hash()`.
* **`Scraping` (Classe Filha):** Especialização para coletas em redes sociais, gerenciando parâmetros como `url_alvo` e `profundidade`.
* **`InsercaoManual` (Classe Filha):** Especialização para arquivos locais, gerenciando o payload de imagens (`nome_arquivo`).

---

## 📦 Como Rodar o Projeto Localmente

### Pré-requisitos
Certifique-se de ter o **Python 3.x** instalado em sua máquina.

### 1. Clonar o Repositório
```bash
git clone [https://github.com/renanfonseca/sivic-prototipo.git](https://github.com/renanfonseca/sivic-prototipo.git)
cd sivic-prototipo