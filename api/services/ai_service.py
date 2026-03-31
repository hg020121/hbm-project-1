# api/services/ai_service.py
# OpenAI GPT 연동 서비스
# pjt-main.py + template/rag_internal-dbms_vdb_open_llm.py 기반

from dotenv import load_dotenv
import os, json, base64, tempfile
from typing import Optional, List
from openai import AsyncOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage
from pypdf import PdfReader

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL     = os.getenv("CHAT_MODEL", "gpt-4o")
EMBED_MODEL    = os.getenv("EMBED_MODEL", "text-embedding-3-small")
FAISS_DIR      = os.getenv("FAISS_DIR", "faiss_store")
CHUNK_SIZE     = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP  = int(os.getenv("CHUNK_OVERLAP", "150"))

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# 전역 벡터스토어 캐시 (pjt-main.py 방식)
VECTORSTORE: Optional[FAISS] = None


# ============================
# Phase 2-1: 공정 파라미터 AI 추천
# ============================
async def recommend_process_params(
    lot_id: str,
    current_viscosity: float,
    current_cte: float,
    current_stack_seq: int,
    current_void: Optional[float],
    similar_lots: List[dict],
    stack_history: List[dict],
) -> dict:
    """
    현재 LOT 정보 + 과거 유사 LOT 공정 데이터 → GPT → 압력/온도 추천
    """
    similar_text = ""
    for lot in similar_lots[:5]:
        stk_summary = ", ".join([
            f"seq{s['seq']}: pressure={s['pressure']}MPa void={s['void']}"
            for s in lot.get("stackings", [])
        ])
        similar_text += (
            f"- LOT {lot['lot_id']}: viscosity={lot['viscosity']}, cte={lot['cte']}, "
            f"stacking=[{stk_summary}], 최종결과={lot['final_result']}, 최종void={lot['final_void']}\n"
        )

    history_text = ""
    for h in stack_history:
        history_text += f"- seq{h['seq']}: pressure={h['pressure']}MPa, void={h['void']}\n"

    prompt = f"""당신은 HBM 반도체 MR-MUF 공정 전문가 AI입니다.
현재 LOT 정보와 과거 유사 LOT 데이터를 바탕으로 다음 공정 파라미터를 추천해주세요.

## 현재 LOT 정보
- LOT ID: {lot_id}
- 소재 점도(viscosity): {current_viscosity} Pa·s
- 소재 열팽창계수(CTE): {current_cte} ppm/°C
- 현재 stacking 단계: {current_stack_seq}번째
- 현재 void 비율: {current_void if current_void else '측정 전'}

## 현재 LOT 공정 이력
{history_text if history_text else '아직 공정 이력 없음'}

## 유사 소재 과거 LOT 공정 데이터
{similar_text if similar_text else '유사 LOT 없음'}

## 요청
위 데이터를 분석하여 다음 형식으로 JSON만 반환하세요 (다른 텍스트 없이):
{{
  "recommend_pressure": <숫자, MPa 단위>,
  "recommend_temp": <숫자, °C 단위>,
  "reason": "<추천 근거 2-3문장, 한국어>",
  "risk_level": "<LOW|MEDIUM|HIGH>",
  "void_prediction": <예측 void 비율 숫자>
}}"""

    response = await client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        result = json.loads(raw)
    except Exception:
        result = {
            "recommend_pressure": 2.20,
            "recommend_temp": 252.0,
            "reason": "데이터 파싱 오류로 기본값 제공",
            "risk_level": "MEDIUM",
            "void_prediction": 0.10,
        }
    return result


# ============================
# Phase 2-2: 챗봇 (공정/품질 역할 구분)
# ============================
async def chat_with_context(
    message: str,
    role: str,
    lot_context: Optional[dict] = None,
    rag_context: Optional[str] = None,
) -> str:
    """
    역할(공정연구원/품질조사원)에 맞는 챗봇 응답
    lot_context: 특정 LOT 정보, rag_context: PDF 논문 검색 결과
    """
    if role == "engineer":
        system_prompt = (
            "당신은 HBM 반도체 MR-MUF 공정 전문가입니다. "
            "공정연구원의 질문에 stacking 압력, reflow 온도, void 관리 등 "
            "공정 파라미터 최적화 관점에서 전문적으로 답변하세요. "
            "한국어로 답변하세요."
        )
    else:
        system_prompt = (
            "당신은 HBM 반도체 품질 분석 전문가입니다. "
            "품질조사원의 질문에 void 분석, 수율, 불량 원인, "
            "품질 기준 등의 관점에서 전문적으로 답변하세요. "
            "한국어로 답변하세요."
        )

    user_content = message
    if lot_context:
        user_content = f"[LOT 컨텍스트]\n{json.dumps(lot_context, ensure_ascii=False)}\n\n[질문]\n{message}"
    if rag_context:
        user_content += f"\n\n[관련 논문 발췌]\n{rag_context}"

    response = await client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


# ============================
# Phase 2-3: GPT Vision 이미지 분석
# ============================
async def analyze_process_image(image_bytes: bytes, lot_id: Optional[str] = None) -> dict:
    """
    SAM 검사 이미지 → GPT Vision → void 분석 및 공정 권고
    """
    b64_image = base64.b64encode(image_bytes).decode("utf-8")

    prompt = f"""이 이미지는 HBM 반도체 MR-MUF 공정의 SAM(Scanning Acoustic Microscopy) 검사 이미지입니다.
{f'LOT ID: {lot_id}' if lot_id else ''}

다음 항목을 분석하여 JSON 형식으로만 반환하세요:
{{
  "void_estimate": <void 면적 비율 추정값 0~1, 숫자>,
  "layer_voids": [<L1 void 0~1>, <L2 void 0~1>, <L3 void 0~1>, <L4 void 0~1>, <L5 void 0~1>, <L6 void 0~1>, <L7 void 0~1>, <L8 void 0~1>, <L9 void 0~1>, <L10 void 0~1>],
  "defect_locations": "<결함 위치 설명>",
  "severity": "<GOOD|WARNING|CRITICAL>",
  "analysis": "<이미지 분석 결과 2-3문장, 한국어>",
  "recommendation": "<공정 개선 권고사항 2-3문장, 한국어>"
}}
layer_voids는 L1(하단)부터 L10(상단)까지 각 층의 void 비율입니다. 이미지에서 층별 void 분포를 추정하여 반환하세요."""

    response = await client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
            ],
        }],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        result = json.loads(raw)
    except Exception:
        result = {
            "void_estimate": 0.05,
            "defect_locations": "분석 실패",
            "severity": "WARNING",
            "analysis": "이미지 분석 중 오류가 발생했습니다.",
            "recommendation": "이미지를 다시 업로드해주세요.",
            "layer_voids": [],
        }

    # layer_voids가 없거나 비어있으면 void_estimate 기반으로 생성
    if not result.get("layer_voids"):
        import math
        base = float(result.get("void_estimate") or 0.05)
        result["layer_voids"] = [
            round(max(0.001, min(0.99, base * (0.5 + math.sin(i * 0.9 + 0.5) * 0.5 + 0.3))), 4)
            for i in range(10)
        ]

    return result


# ============================
# Phase 2-4: PDF RAG (pjt-main.py 방식)
# ============================
def _load_pdf_text(file_path: str) -> str:
    reader = PdfReader(file_path)
    return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])


async def upload_pdf_to_vectorstore(file_bytes: bytes, filename: str) -> dict:
    """PDF 업로드 → 텍스트 추출 → FAISS 벡터화 (pjt-main.py 방식)"""
    global VECTORSTORE

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    text = _load_pdf_text(tmp_path)
    os.unlink(tmp_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    docs = splitter.create_documents([text])

    embeddings = OpenAIEmbeddings(model=EMBED_MODEL, api_key=OPENAI_API_KEY)

    if VECTORSTORE is None:
        VECTORSTORE = FAISS.from_documents(docs, embeddings)
    else:
        new_vs = FAISS.from_documents(docs, embeddings)
        VECTORSTORE.merge_from(new_vs)

    os.makedirs(FAISS_DIR, exist_ok=True)
    VECTORSTORE.save_local(FAISS_DIR)

    return {"filename": filename, "chunks": len(docs), "message": f"{len(docs)}개 청크 벡터화 완료"}


async def query_rag(question: str, top_k: int = 3) -> dict:
    """FAISS 검색 → GPT 답변 (pjt-main.py 방식)"""
    global VECTORSTORE

    if VECTORSTORE is None:
        embeddings = OpenAIEmbeddings(model=EMBED_MODEL, api_key=OPENAI_API_KEY)
        if os.path.exists(FAISS_DIR):
            VECTORSTORE = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
        else:
            return {"question": question, "answer": "업로드된 논문이 없습니다. PDF를 먼저 업로드해주세요.", "sources": []}

    related_docs = VECTORSTORE.similarity_search(question, k=top_k)
    context = "\n\n".join([doc.page_content for doc in related_docs])
    sources = [doc.page_content[:100] + "..." for doc in related_docs]

    prompt = f"""당신은 HBM 반도체 공정 논문 기반 연구 보조 AI입니다.
아래 논문 발췌 내용을 바탕으로 질문에 답변하세요.
발췌 내용에 없는 정보는 '논문에서 해당 내용을 찾을 수 없습니다'라고 답변하세요.

[논문 발췌]
{context}

[질문]
{question}"""

    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0.3, api_key=OPENAI_API_KEY)
    response = llm.invoke([HumanMessage(content=prompt)]).content

    return {"question": question, "answer": response, "sources": sources}
