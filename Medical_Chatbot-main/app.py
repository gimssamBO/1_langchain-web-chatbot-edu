import os
import csv
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from datetime import datetime
import openai
from dotenv import load_dotenv
from streamlit_geolocation import streamlit_geolocation

<<<<<<< HEAD
# -----------------------------------------------------------------------------
# [환경 설정 및 예외 처리 1]
# 시스템 환경변수에 잘못 지정된 SSL CERT 경로가 있을 경우 
# httpx 통신 시 FileNotFoundError가 발생하는 문제를 방지하기 위해 해당 변수를 삭제합니다.
# -----------------------------------------------------------------------------
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]
if "REQUESTS_CA_BUNDLE" in os.environ:
    del os.environ["REQUESTS_CA_BUNDLE"]

# -----------------------------------------------------------------------------
# [LangChain 모듈 임포트]
# 버퍼 오버플로우(TP_NUM_C_BUFS) 방지를 위해 C++ 기반 UnstructuredFileLoader 대신 
# 순수 파이썬 기반의 TextLoader를 사용합니다.
# -----------------------------------------------------------------------------
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, CacheBackedEmbeddings
from langchain.vectorstores import FAISS
from langchain.storage import LocalFileStore
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda

# .env 파일에 저장된 환경 변수(API 키 등)를 로드합니다.
load_dotenv()

# -----------------------------------------------------------------------------
# [환경 설정 및 예외 처리 2]
# API 키를 OPENAI_API_KEY 또는 API_KEY 변수명에서 안전하게 가져와 os.environ에 등록합니다.
# -----------------------------------------------------------------------------
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
os.environ["OPENAI_API_KEY"] = API_KEY if API_KEY else ""
=======
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_classic.storage import LocalFileStore
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# 환경 변수를 로드합니다.
load_dotenv(override=True) #(현재 env로 덮어쓰기 파라미터)
load_dotenv()

# API 키를 환경 변수에서 가져옵니다. = 아래 주석 처리
# API_KEY = os.getenv("API_KEY")
# os.environ["OPENAI_API_KEY"] = API_KEY 
>>>>>>> 98cb368fc704f444e2c8a7e9b840f0cda7ce3237

# -----------------------------------------------------------------------------
# [RAG 파이프라인 및 VectorDB 구축]
# -----------------------------------------------------------------------------
# 1. OpenAI 대화형 언어 모델(LLM) 객체 생성 (gpt-4o-mini 모델 적용)
llm = ChatOpenAI(
    model='gpt-4o-mini',
    temperature=0.1,  # 답변의 일관성을 위해 낮게 설정
)

# 2. 임베딩 결과를 디스크에 로컬 저장(캐싱)할 디렉터리 지정
cache_dir = LocalFileStore("./.cache/practice/")

# 3. 텍스트 분할기(Text Splitter) 설정 (줄바꿈 기준, 600자 단위, 100자 중복)
splitter = CharacterTextSplitter.from_tiktoken_encoder(
    separator="\n",
    chunk_size=600,
    chunk_overlap=100,
)

# 4. 참고 문서(refer.txt) 읽어오기 (인코딩 utf-8 지정)
loader = TextLoader("./refer.txt", encoding="utf-8")
docs = loader.load_and_split(text_splitter=splitter)

# 5. 최신 임베딩 모델(text-embedding-3-small) 객체 생성
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 6. 임베딩 재계산을 줄이기 위한 캐시 기반 임베딩 처리
cached_embeddings = CacheBackedEmbeddings.from_bytes_store(embeddings, cache_dir)

# 7. FAISS VectorDB 생성 및 문서 벡터 인덱싱
vectorstore = FAISS.from_documents(docs, cached_embeddings)

# 8. 유사도 기반 문서 검색기(Retriever) 객체 생성
retriever = vectorstore.as_retriever()

# -----------------------------------------------------------------------------
# [Streamlit 세션 상태 초기화]
# -----------------------------------------------------------------------------
# 앱이 리로드되어도 이전 대화 내역이 유지되도록 세션 상태에 저장 공간을 만듭니다.
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------------------------------------------------------
# [RAG 질의응답 처리 함수]
# -----------------------------------------------------------------------------
def ask_gpt(user_question):
    """사용자의 질문과 관련 문서를 검색해 프롬프트로 결합한 후 LLM의 답변을 반환합니다."""
    
    # System, Human 메시지로 구성된 프롬프트 템플릿 정의
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            당신은 의사입니다. 응급 상황에 대한 조치 내용은 첨부된 문서를 참조하여 대답합니다. 
            의료와 관련된 질문에 친절히 대답하며, 심각하거나 큰 질병이 우려되는 상황에서는 병원 방문을 권유하세요:
            \n\n
            {context}",
            """
        ),
        ("human", "{question}"),
    ])

    # LCEL(LangChain Expression Language) 체인 구성
    # 1) context: retriever를 통해 질문에 부합하는 참고문서 검색
    # 2) question: RunnablePassthrough를 통해 사용자 질문 원본 그대로 전달
    chain = (
        {
            "context": retriever,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
    )
    
    # 체인 실행 및 답변 텍스트 추출
    result = chain.invoke(user_question)
    return result.content

# -----------------------------------------------------------------------------
# [Folium 지도 생성 함수]
# -----------------------------------------------------------------------------
def create_map(df_hospitals, my_locations):
    """내 위치 좌표와 필터링된 주변 병원 목록 데이터를 받아 Folium 지도를 생성합니다."""
    
    latitude, longitude = my_locations
    # 내 위치 좌표를 중심으로 지도 객체 생성 (확대 레벨 12)
    m = folium.Map(location=[latitude, longitude], zoom_start=12)
    
    # 주변 병원 데이터프레임의 각 행을 순회하며 마커 추가
    for index, row in df_hospitals.iterrows():
        folium.Marker(
            [row['위도'], row['경도']],
            tooltip=row['기관명'],  # 마우스 호버 시 병원 이름 표시
        ).add_to(m)
        
    # 내 위치를 빨간색 아이콘 마커로 지도에 추가
    folium.Marker(
        [latitude, longitude],
        tooltip='내 위치',
        icon=folium.map.Icon('red')
    ).add_to(m)

    return m

# -----------------------------------------------------------------------------
# [메인 애플리케이션 실행]
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. 의료기관 통합 CSV 데이터 로드 (인덱스 칼럼 지정)
    df_hospitals = pd.read_csv('의료기관통합.csv', index_col=0)
    
    # 2. Streamlit 웹 페이지 기본 레이아웃 및 타이틀 설정
    st.set_page_config(layout="wide", page_title="LLM기반의 의료 상담 앱")
    st.title('LLM기반의 의료 상담 앱')

    # 3. 사용자 증상 입력 텍스트 상자
    question = st.text_input("증상을 입력하세요", "")

    # 4. 분석 시작 버튼 클릭 이벤트 처리
    if st.button('AI 분석 답변 생성 시작'):
        if question:
            # RAG 체인을 호출하여 AI 답변 생성
            answer = ask_gpt(question)
            
            # 대화 내역 세션 상태에 저장
            st.session_state.chat_history.append(f"질문: {question}")
            st.session_state.chat_history.append(f"답변: {answer}")
            
            # 이전 및 현재 대화 내역을 화면에 출력
            for message in st.session_state.chat_history:
                st.text(message)
        else:
            st.error("질문을 제공해주세요.")  # 미입력 시 에러 메시지 출력

    # 5. 사용자 위치 기반 주변 병원 추천 섹션
    st.write("#### 현재 위치를 기준으로 주변 병원을 추천드리겠습니다.")
    
    # 브라우저 위도/경도 위치 정보 취득 컴포넌트
    location = streamlit_geolocation()
    
    locations = location['latitude'], location['longitude']
    
    # 위치 정보 추출 범위 설정 (임계값 th = 0.1, 약 10km 범위)
    th = 0.1
    
    # 위도 데이터가 정상적으로 수집된 경우 지도를 렌더링
    if location['latitude']:
        print(location['latitude'])
        try: 
            # 내 위도/경도 기준 오차 범위(th) 내에 있는 병원만 필터링
            df_hospitals = df_hospitals.loc[
                (abs(df_hospitals['위도'] - location['latitude']) < th) & 
                (abs(df_hospitals['경도'] - location['longitude']) < th)
            ]
            # 지도 생성 및 Streamlit 화면에 표시
            map = create_map(df_hospitals, locations)
            folium_static(map)
        except:
<<<<<<< HEAD
            st.write("위치 정보를 가져올 수 없습니다. 위치 서비스가 활성화되어 있는지 확인하세요.")
=======
           st.write("위치 정보를 가져올 수 없습니다. 위치 서비스가 활성화되어 있는지 확인하세요.")
>>>>>>> 98cb368fc704f444e2c8a7e9b840f0cda7ce3237
