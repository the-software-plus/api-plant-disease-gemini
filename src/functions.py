# src/functions.py
import io
import json # Importante para criar strings JSON de forma segura
import google.generativeai as genai

def image_pil_to_parts(pil_image, mime_type="image/jpeg"):
    """
    Converte um objeto PIL.Image para o formato de parts esperado pela API Gemini.
    :param pil_image: A imagem no formato PIL.Image (criada a partir do UploadFile no main.py).
    :param mime_type: O tipo MIME da imagem (ex: 'image/jpeg', 'image/png').
    :return: Lista com a parte da imagem para a API Gemini.
    """
    img_byte_arr = io.BytesIO()
    # Determina o formato com base no mime_type
    format_type = 'JPEG' # Padrão para image/jpeg
    if mime_type == 'image/png':
        format_type = 'PNG'
    elif mime_type == 'image/webp':
        format_type = 'WEBP'
    # Adicione outros tipos MIME e formatos PIL correspondentes se necessário

    try:
        pil_image.save(img_byte_arr, format=format_type)
    except Exception as e:
        print(f"Erro ao salvar imagem PIL no buffer de bytes: {e}")
        # Você pode querer levantar uma exceção específica ou retornar None/erro
        raise ValueError(f"Não foi possível processar a imagem para o formato {format_type}") from e
        
    image_bytes = img_byte_arr.getvalue()

    image_parts = [
        {
            'mime_type': mime_type,
            'data': image_bytes
        }
    ]
    return image_parts

def get_gemini_plant_disease_response(model: genai.GenerativeModel, image_parts: list, custom_prompt: str = None):
    """
    Envia as partes da imagem e um prompt focado em doenças de plantas para o Gemini.
    Espera-se que o modelo Gemini retorne uma string JSON.
    :param model: O modelo Gemini configurado (genai.GenerativeModel).
    :param image_parts: As partes da imagem prontas para a API Gemini (saída de image_pil_to_parts).
    :param custom_prompt: Um prompt opcional para guiar a análise. Se None, um prompt padrão será usado.
    :return: O texto da resposta do Gemini (que deve ser uma string JSON, incluindo em casos de erro da IA).
    """
    if not custom_prompt:
        custom_prompt = """
        Analise esta imagem de uma planta. Siga RIGOROSAMENTE as seguintes instruções:
        1. Identifique se a planta parece saudável ou se apresenta sinais de alguma doença ou praga.
        2. Se uma doença ou praga for identificada:
           a. Forneça o NOME COMUM da doença ou praga.
           b. Descreva BREVEMENTE a doença/praga, focando nos sintomas visíveis na imagem, se houver, e suas possíveis causas.
           c. Forneça SUGESTÕES DE TRATAMENTO DETALHADAS E PRÁTICAS. Para cada sugestão, seja específico. Inclua, quando aplicável e de forma genérica (sem marcas específicas, a menos que seja um componente ativo crucial e amplamente conhecido):
              - Tipos de produtos que podem ser usados (ex: fungicidas à base de cobre, sabão inseticida, óleo de neem, inseticidas sistêmicos específicos para o problema).
              - Técnicas de manejo cultural (ex: rotação de culturas, poda sanitária de partes afetadas, ajuste de irrigação/drenagem, remoção e descarte adequado de material vegetal infectado, solarização do solo).
              - Ações preventivas para evitar futuras infestações ou recorrência da doença.
              - Se possível, indique frequência ou momento ideal para as aplicações ou ações.
        3. Se a planta parecer saudável, afirme isso claramente e defina "nome_doenca_praga" como "Nenhuma", e "sugestoes_tratamento" como uma lista vazia ou com uma mensagem de manutenção geral.
        4. Se a imagem não for clara o suficiente, não for de uma planta, ou se você não puder fazer uma avaliação confiável, indique isso no campo "descricao", defina "nome_doenca_praga" como "Não identificado", e "sugestoes_tratamento" como uma lista vazia.

        A SUA RESPOSTA DEVE SER APENAS E EXCLUSIVAMENTE UM OBJETO JSON VÁLIDO.
        NÃO inclua nenhum texto explicativo, introduções, saudações, ou qualquer caractere antes do '{' inicial ou depois do '}' final do objeto JSON.
        O formato JSON OBRIGATÓRIO é:
        {
          "planta_saudavel": true (booleano, true se saudável, false caso contrário),
          "nome_doenca_praga": "String com o nome da doença/praga" (use "Nenhuma" se saudável, "Não identificado" se não for possível determinar),
          "descricao": "String com a descrição detalhada da condição, sintomas, causas, ou motivo da não identificação.",
          "sugestoes_tratamento": ["Lista de strings, onde CADA STRING é uma ação de tratamento ou manejo distinta, detalhada e prática. Ex: 'Aplicar fungicida à base de cobre a cada 15 dias durante o período chuvoso.', 'Realizar poda de limpeza, removendo todos os galhos secos e doentes e queimando-os.'"]
        }
        Certifique-se de que todos os valores de string dentro do JSON estejam entre aspas duplas e que quaisquer aspas duplas dentro dessas strings sejam devidamente escapadas (ex: \\").
        O valor de "planta_saudavel" DEVE ser um booleano literal (true ou false, sem aspas).
        O valor de "sugestoes_tratamento" DEVE ser uma lista de strings.
        """
    
    try:
        # Configurar para esperar uma resposta JSON diretamente do modelo
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        
        response = model.generate_content(
            [custom_prompt, image_parts[0]], # image_parts[0] é o dicionário da imagem
            generation_config=generation_config
        )
        
        # Mesmo com response_mime_type="application/json", verificar safety feedback
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason_msg = f"Conteúdo bloqueado pelo Gemini. Razão: {response.prompt_feedback.block_reason}"
            print(f"AVISO GEMINI: {block_reason_msg}")
            error_data_blocked = {
                "planta_saudavel": False,
                "nome_doenca_praga": "Bloqueado pela IA",
                "descricao": block_reason_msg,
                "sugestoes_tratamento": "Tente uma imagem ou prompt diferente."
            }
            return json.dumps(error_data_blocked)

        # Se response_mime_type="application/json" for respeitado, response.text já é o JSON string
        return response.text

    except Exception as e:
        # Este bloco captura outros erros, como problemas de rede ao chamar a API Gemini,
        # ou se o modelo falhar em gerar conteúdo mesmo com a configuração JSON.
        print(f"ERRO CRÍTICO ao chamar a API Gemini ou processar sua resposta: {type(e).__name__} - {e}")
        
        error_message_content = str(e).replace('"', "'") # Evita aspas duplas na mensagem de erro
        error_data_exception = {
            "planta_saudavel": False,
            "nome_doenca_praga": "Erro na IA",
            "descricao": f"Ocorreu um erro crítico ao comunicar ou processar a resposta da IA: {error_message_content}",
            "sugestoes_tratamento": "Por favor, tente novamente mais tarde ou contate o suporte."
        }
        return json.dumps(error_data_exception)