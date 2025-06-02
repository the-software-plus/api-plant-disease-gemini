# API de Detecção de Doenças em Plantas com Gemini

Esta é uma API desenvolvida em Python com FastAPI que utiliza o modelo multimodal Gemini do Google para analisar imagens de plantas e detectar possíveis doenças. A API retorna informações sobre a saúde da planta, o nome da doença ou praga (se detectada), uma descrição e sugestões de tratamento.

## Funcionalidades

* Recebe uma imagem de planta via upload.
* Interage com a API Google Gemini para análise da imagem.
* Retorna uma resposta JSON estruturada contendo:
    * Status da saúde da planta (`planta_saudavel`: boolean).
    * Nome da doença ou praga (`nome_doenca_praga`: string).
    * Descrição detalhada (`descricao`: string).
    * Sugestões de tratamento práticas (`sugestoes_tratamento`: lista de strings).

## Tecnologias Utilizadas

* **Python 3.9+**
* **FastAPI**: Framework web para construir a API.
* **Uvicorn**: Servidor ASGI para rodar a aplicação FastAPI.
* **Google Gemini API**: Para a inteligência artificial e análise de imagem.
    * `google-generativeai`: Biblioteca cliente Python para a API Gemini.
* **Pillow**: Para manipulação básica de imagens.
* **Pydantic**: Para validação de dados de entrada e saída da API.
* **python-dotenv**: Para gerenciamento de variáveis de ambiente.

## Pré-requisitos

* Python 3.9 ou superior
* `pyenv` (recomendado para gerenciar versões do Python)
* Git
* Uma chave de API do Google Gemini (obtenha no [Google AI Studio](https://aistudio.google.com/))

## Configuração do Ambiente

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/the-software-plus/api-plant-disease-gemini.git
    cd api-plant-disease-gemini
    ```

2.  **Configure a versão do Python (se estiver usando `pyenv`):**
    ```bash
    pyenv install 3.9.13 
    pyenv global 3.9.13 
    ```

3.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

4.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure as variáveis de ambiente:**
    Crie um arquivo chamado `.env` na raiz do projeto e adicione sua chave da API Gemini:
    ```env
    GEMINI_API_KEY="SUA_CHAVE_API_AQUI_DO_GEMINI"
    ```

## Como Executar a Aplicação

1.  Com o ambiente virtual ativado e as dependências instaladas, inicie o servidor FastAPI com Uvicorn:
    ```bash
    uvicorn main:app --reload
    ```
    * `main`: Refere-se ao arquivo `main.py`.
    * `app`: Refere-se à instância `app = FastAPI()` dentro do `main.py`.
    * `--reload`: Faz o servidor reiniciar automaticamente após alterações no código (ótimo para desenvolvimento).

2. A API estará rodando em `http://127.0.0.1:8000`.


## Como Testar via `curl`:
```bash
curl -X POST -F "file=@caminho/para/sua/imagem.jpg" http://localhost:8000/predict/
```

