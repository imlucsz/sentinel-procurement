<div align="center">

# 🛡️ Sentinel Procurement

### Monitoramento de anomalias e disparidades de preços em contratações públicas brasileiras

Uma ferramenta de auditoria cidadã e análise estatística baseada em dados abertos do **Portal Nacional de Contratações Públicas (PNCP)**.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PNCP](https://img.shields.io/badge/Dados-PNCP-1F6FEB?style=for-the-badge)](https://pncp.gov.br/)
[![License](https://img.shields.io/badge/Licença-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## 📖 Sobre o projeto

O **Sentinel Procurement** é um projeto de auditoria cidadã desenvolvido para apoiar a identificação de disparidades e possíveis anomalias nos preços praticados em compras públicas municipais brasileiras.

A proposta é coletar dados públicos do **Portal Nacional de Contratações Públicas (PNCP)**, organizar e normalizar as informações e realizar análises que ajudem a sinalizar valores potencialmente atípicos entre diferentes contratações.

O projeto considera o contexto da **Lei nº 14.133/2021**, a Nova Lei de Licitações e Contratos Administrativos, e prioriza a rastreabilidade e a proveniência dos dados utilizados.

> **Importante:** uma diferença de preço é um sinal para investigação, não uma prova isolada de fraude ou superfaturamento. Os resultados precisam ser interpretados considerando especificações, quantidades, localização, período e condições de cada contratação.

## 🎯 Objetivos

- Coletar dados públicos de contratações disponibilizados pelo PNCP.
- Preservar os dados brutos para permitir rastreabilidade.
- Normalizar descrições e preparar os dados para análise.
- Verificar a integridade e a qualidade das informações coletadas.
- Identificar categorias comparáveis e sinalizar possíveis disparidades de preços.
- Apoiar a transparência e o controle social dos gastos públicos.

## 🔎 Escopo de monitoramento

O escopo proposto contempla diferentes tipos de contratação:

| Tipo | Exemplos de aplicação |
|---|---|
| **Pregão** | Combustíveis, merenda escolar, medicamentos e materiais de escritório. |
| **Concorrência** | Insumos para obras e serviços especiais, como concreto, asfalto e cimento. |
| **Dispensa de licitação por valor** | Análise de contratações diretas para auxiliar na identificação de padrões que mereçam verificação. |

A análise deve respeitar as regras legais aplicáveis à data e ao tipo de contratação. Os limites monetários podem ser atualizados; consulte sempre as fontes oficiais antes de utilizá-los.

## 🧰 Tecnologias e ferramentas

- **Python 3.10 ou superior** — linguagem principal.
- **API do PNCP** — fonte de dados públicos.
- **pip / Poetry** — gerenciamento de dependências.
- **pytest** — execução dos testes automatizados.
- **Git** — controle de versão.

## 🗂️ Estrutura do projeto

```text
imlucsz-sentinel-procurement/
├── README.md
├── pyproject.toml
├── .env.example
├── data/
│   ├── raw/                          # Dados brutos em JSON
│   └── processed/                    # Dados limpos e normalizados
├── src/
│   └── procurement_monitor/
│       ├── config.py                 # Configurações e caminhos
│       ├── clients/
│       │   └── pncp.py               # Cliente HTTP para a API do PNCP
│       ├── ingestion/
│       │   └── collect_contracts.py  # Coleta de dados
│       ├── processing/
│       │   ├── normalize.py           # Normalização textual
│       │   └── quality_report.py     # Relatório de qualidade
│       └── analysis/
│           └── category_discovery.py # Categorias e análise de anomalias
└── tests/
    ├── test_normalize.py
    └── test_quality_report.py
```

*Esta estrutura representa a organização documentada do projeto. Os arquivos e comandos devem corresponder aos existentes no repositório.*

## ⚙️ Instalação e configuração

### 1. Pré-requisitos

- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

### 2. Clone o repositório

```bash
git clone https://github.com/imlucsz/sentinel-procurement.git
cd sentinel-procurement
```

### 3. Crie e ative um ambiente virtual

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instale as dependências

**Com pip:**

```bash
python -m pip install --upgrade pip
pip install -e .
```

**Ou, se o projeto estiver configurado para Poetry:**

```bash
poetry install
```

Use o método compatível com a configuração de dependências presente no `pyproject.toml`.

### 5. Configure as variáveis de ambiente

Se o projeto utilizar variáveis de ambiente, copie o arquivo de exemplo:

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

**Linux / macOS:**

```bash
cp .env.example .env
```

Depois, preencha o `.env` com os valores necessários, conforme a configuração do projeto. **Não publique credenciais ou segredos no repositório.**

## 🚀 Execução dos módulos

Execute os comandos a partir da raiz do projeto e com o ambiente virtual ativado.

### 1. Coleta de dados do PNCP

```bash
python -m src.procurement_monitor.ingestion.collect_contracts
```

O módulo é destinado à coleta de dados e ao armazenamento dos arquivos brutos em `data/raw/`.

### 2. Normalização dos dados

```bash
python -m src.procurement_monitor.processing.normalize
```

Prepara descrições e informações textuais para facilitar a análise, com saída prevista em `data/processed/`.

### 3. Relatório de qualidade

```bash
python -m src.procurement_monitor.processing.quality_report
```

Verifica aspectos de integridade e qualidade dos dados coletados.

### 4. Descoberta de categorias e anomalias

```bash
python -m src.procurement_monitor.analysis.category_discovery
```

Executa a etapa de análise destinada a agrupar categorias e sinalizar possíveis disparidades de preços entre contratações.

> Os comandos acima seguem os módulos descritos na estrutura do projeto. Caso a organização real do pacote seja diferente, ajuste os caminhos de execução conforme o código existente.

## 🧪 Testes

Para executar os testes automatizados:

```bash
pytest
```

Para gerar um relatório de cobertura, caso o plugin `pytest-cov` esteja instalado:

```bash
pytest --cov=src
```

Se necessário, instale as ferramentas de teste:

```bash
pip install pytest pytest-cov
```

## 📊 Interpretação dos resultados

Os resultados devem ser tratados como **indicadores para análise**, não como conclusões definitivas. Para comparar preços de forma responsável, considere fatores como:

- Descrição e especificação do item.
- Unidade de medida e quantidade contratada.
- Data da contratação e condições de mercado.
- Município, região e custos logísticos.
- Condições de entrega, qualidade e prestação do serviço.
- Integridade, cobertura e atualidade dos dados disponíveis.

## 🔗 Fontes oficiais

- [Portal Nacional de Contratações Públicas (PNCP)](https://www.gov.br/pncp/pt-br)
- [Documentação da API do PNCP — Swagger UI](https://pncp.gov.br/api/consulta/swagger-ui/index.html)
- [Manual de Integração do PNCP — versão 2.5](https://pncp.gov.br/manual/pt-br/2.5/)
- [Lei nº 14.133/2021 — Lei de Licitações e Contratos Administrativos](https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm)

## 🤝 Contribuições

Sugestões, relatos de problemas e melhorias são bem-vindos. Para contribuir:

1. Faça um fork do repositório.
2. Crie uma branch para sua alteração.
3. Implemente e teste a mudança.
4. Envie um pull request com uma descrição clara do que foi alterado.

## 📄 Licença

Este projeto declara utilizar a licença [MIT](LICENSE). Consulte o arquivo `LICENSE` na raiz do repositório para verificar os termos aplicáveis.

---

<div align="center">

Desenvolvido por **[Lucas Araújo (imlucsz)](https://github.com/imlucsz)**

</div>
