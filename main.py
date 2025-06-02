import os
import json
import io
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

from src.functions import image_pil_to_parts, get_gemini_plant_disease_response

load_dotenv()

app = FastAPI(
    title="API de Detecção de Doenças de Plantas com Gemini",
    version="1.0.1", # Versão atualizada
    description="Uma API para analisar imagens de plantas e detectar doenças usando a IA do Google Gemini."
)

# Configurar CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substitua "*" por uma lista de origens permitidas
    allow_credentials=True,
    allow_methods=["POST", "GET"], 
    allow_headers=["*"],
)

# ---- Configuração do Modelo Gemini ----
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("ERRO CRÍTICO: Chave da API Gemini (GEMINI_API_KEY) não encontrada nas variáveis de ambiente.")
    raise RuntimeError("Chave da API Gemini (GEMINI_API_KEY) não encontrada. Defina-a no arquivo .env.")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    MODEL_GEMINI = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
    print("Modelo Gemini configurado com sucesso.")
except Exception as e:
    print(f"ERRO CRÍTICO: Falha ao configurar ou carregar o modelo Gemini: {e}")
    raise RuntimeError(f"Falha ao configurar ou carregar o modelo Gemini: {e}")


# ---- Modelos Pydantic para Validação de Resposta ----
class DiseaseInfo(BaseModel):
    planta_saudavel: bool
    nome_doenca_praga: str
    descricao: str
    sugestoes_tratamento: List[str] # CORRIGIDO: Espera uma lista de strings

class ErrorResponse(BaseModel):
    detail: str

# ---- Endpoints da API ----

@app.get("/", summary="Endpoint Raiz", description="Mensagem de boas-vindas da API.")
async def read_root():
    return {"message": "Bem-vindo à API de Detecção de Doenças de Plantas! Use o endpoint POST /predict para analisar uma imagem."}

@app.post(
    "/predict/",
    summary="Analisa uma imagem de planta para doenças",
    description="Envia uma imagem de planta para o Google Gemini para análise de doenças. Retorna um JSON com os detalhes.",
    response_model=DiseaseInfo, 
    responses={ 
        400: {"model": ErrorResponse, "description": "Requisição inválida (ex: arquivo não é imagem)"},
        500: {"model": ErrorResponse, "description": "Erro interno do servidor"},
        502: {"model": ErrorResponse, "description": "Erro na resposta da IA ou ao comunicar com a API do Gemini"}
    }
)
async def predict_plant_disease(
    file: UploadFile = File(..., description="Arquivo de imagem da planta (formatos suportados: PNG, JPG, JPEG, WEBP).")
):
    allowed_mime_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo inválido: '{file.content_type}'. Permitidos: {', '.join(allowed_mime_types)}"
        )

    try:
        image_bytes_content = await file.read()
        pil_image = Image.open(io.BytesIO(image_bytes_content))
        
        image_parts_for_gemini = image_pil_to_parts(pil_image=pil_image, mime_type=file.content_type)
        
        gemini_response_text = get_gemini_plant_disease_response(
            model=MODEL_GEMINI,
            image_parts=image_parts_for_gemini
        )
        
        try:
            if gemini_response_text.startswith("```json"):
                json_str = gemini_response_text[len("```json"):-len("```")].strip()
            elif gemini_response_text.startswith("```"):
                 json_str = gemini_response_text[len("```"):-len("```")].strip()
            else:
                json_str = gemini_response_text.strip()
            
            parsed_response_data = json.loads(json_str)
            # FastAPI validará parsed_response_data contra o response_model=DiseaseInfo
            # Se a validação falhar aqui (ex: sugestoes_tratamento não for uma lista),
            # o FastAPI levantará um ResponseValidationError automaticamente.
            return parsed_response_data

        except json.JSONDecodeError:
            print(f"AVISO: Gemini não retornou um JSON válido. Resposta: {gemini_response_text}")
            raise HTTPException(
                status_code=502,
                detail="A IA não retornou uma resposta JSON válida. Por favor, tente novamente ou ajuste o prompt."
            )
        # O erro de validação do Pydantic (ResponseValidationError) será tratado pelo FastAPI automaticamente
        # se parsed_response_data não corresponder a DiseaseInfo.

    except ValueError as ve: # Captura o ValueError de image_pil_to_parts
        print(f"ERRO no processamento da imagem: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"ERRO INESPERADO no endpoint /predict/: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ocorreu um erro interno inesperado ao processar a imagem: {type(e).__name__}."
        )
    finally:
        if file: # Garante que o arquivo existe antes de tentar fechar
            await file.close()

# Bloco para rodar o servidor Uvicorn diretamente (opcional, mais comum via CLI)
if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor Uvicorn para desenvolvimento em http://localhost:8000")
    print("Acesse a documentação interativa da API em http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) # Alterado de "api_main:app" para "main:app"