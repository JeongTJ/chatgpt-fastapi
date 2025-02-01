# API 키를 환경변수로 관리하기 위한 설정 파일
from dotenv import load_dotenv

from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from typing import Dict, Any
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

# API 키 정보 로드
load_dotenv()

def prepare_restaurant_documents(docs):
    restaurant_docs = []
    for doc in docs:
        content = doc.page_content
        
        # RSTR_ID 값 추출 - BOM 문자를 명시적으로 처리
        rstr_id = None
        for line in content.split('\n'):
            if line.startswith('\ufeffRSTR_ID:') or line.startswith('RSTR_ID:'):
                rstr_id = int(line.split(':')[1].strip())
                break
        
        # RSTR_ID 줄을 제외한 나머지 내용만 포함
        content_lines = [line for line in content.split('\n') 
                        if not (line.startswith('\ufeffRSTR_ID:') or line.startswith('RSTR_ID:'))]
        filtered_content = '\n'.join(content_lines)
        
        restaurant_docs.append(Document(
            page_content=filtered_content.strip(),
            metadata={'RSTR_ID': rstr_id}
        ))
    
    return restaurant_docs


def process_restaurant_response(retriever_output, llm_response: str) -> Dict[str, Any]:
    """
    LLM 응답에서 언급된 식당의 ID만 추출합니다.
    """
    mentioned_restaurants = {}
    # 검색된 문서들에서 식당 이름과 ID를 매핑
    for doc in retriever_output:
        content = doc.page_content
        rstr_id = doc.metadata['RSTR_ID']
        
        # 식당 이름 추출 (마크다운 첫 번째 헤딩에서)
        for line in content.split('\n'):
            if line.startswith('# '):
                restaurant_name = line.replace('# ', '').strip()
                mentioned_restaurants[restaurant_name] = rstr_id
                break
    
    # LLM 응답에서 언급된 식당 ID만 수집
    response_restaurant_ids = []
    for restaurant_name in mentioned_restaurants.keys():
        if restaurant_name in llm_response:
            response_restaurant_ids.append(mentioned_restaurants[restaurant_name])
    
    return {
        "answer": llm_response,
        "restaurant_ids": response_restaurant_ids
    }
# 벡터스토어 생성

class RagChain:
    def __init__(self, retriever, response_chain):
        self.retriever = retriever
        self.response_chain = response_chain

    def final_processor(self, input_dict):
        question = input_dict["question"]
        docs = self.retriever.get_relevant_documents(question)
        response = self.response_chain.invoke(input_dict)
        return process_restaurant_response(docs, response)
    
    def make_chain(self, retrieval_chain):
        return retrieval_chain | self.final_processor

def hello(user_request):
    # CSV 로더 생성
    loader = CSVLoader(file_path="./data/food/test/test.csv")

    # 데이터 로드
    docs = loader.load()
    restaurant_docs = prepare_restaurant_documents(docs)
    vectorstore = FAISS.from_documents(
        documents=restaurant_docs, 
        embedding=OpenAIEmbeddings()
    )

    # 검색기(retriever) 생성
    retriever = vectorstore.as_retriever()
    # 프롬프트 템플릿 정의 - 여러 식당을 추천하도록
    # restaurant_finder_template = """
    # 당신은 레스토랑 추천 AI입니다. 주어진 맥락을 바탕으로 사용자의 질문에 답변해주세요.

    # 다음은 레스토랑에 대한 정보입니다:
    # {restaurant_info}

    # 사용자 질문: {user_request}

    # 다음 지침을 따라 답변해주세요:
    # 1. 조건에 맞는 식당을 2-3개 추천해주세요.
    # 2. 각 식당의 이름을 정확히 큰따옴표로 감싸서 언급해주세요. (예: "더밥하우스")
    # 3. 각 식당의 주요 특징을 간단히 설명해주세요.

    # 레스토랑 정보를 바탕으로 사용자의 질문에 답변해주세요.
    # """

    # prompt = PromptTemplate.from_template(restaurant_finder_template)

    # LLM 설정
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2)
    # RAG 체인 생성
    # rag_chain = (
    #     {
    #         "restaurant_info": retriever,
    #         "user_request": RunnablePassthrough()
    #     }
    #     | prompt
    #     | llm
    #     | StrOutputParser()
    # )


    # 프롬프트 템플릿 수정 - 여러 식당을 추천하도록
    restaurant_finder_template = """
    당신은 레스토랑 추천 AI입니다. 주어진 맥락을 바탕으로 사용자의 질문에 답변해주세요.

    다음은 레스토랑에 대한 정보입니다:
    {restaurant_info}

    사용자 질문: {user_request}

    다음 지침을 따라 답변해주세요:
    1. 조건에 맞는 식당을 2-3개 추천해주세요.
    2. 각 식당의 이름을 정확히 큰따옴표로 감싸서 언급해주세요. (예: "더밥하우스")
    3. 각 식당의 주요 특징을 간단히 설명해주세요.

    레스토랑 정보를 바탕으로 사용자의 질문에 답변해주세요.
    """

    prompt = PromptTemplate.from_template(restaurant_finder_template)

    # 나머지 체인 구성 코드는 동일...


    # 검색 체인 구성
    retrieval_chain = RunnableParallel(
        {"context": retriever, "question": RunnablePassthrough()}
    )

    # 응답 생성 체인
    response_chain = (
        {
            "restaurant_info": lambda x: x["context"],
            "user_request": lambda x: x["question"]
        }
        | prompt 
        | llm 
        | StrOutputParser()
    )

    # 최종 체인 구성

    # rag_chain = retrieval_chain | final_processor
    rrr = RagChain(retriever, response_chain)
    rag_chain = rrr.make_chain(retrieval_chain)

    # 테스트
    # user_request = "부산에서 네이버평점이 좋은 맛집을 추천해주세요."
    result = rag_chain.invoke(user_request)

    print("사용자에게 보여줄 답변:")
    print(result["answer"])
    print("\n백엔드에 전달할 식당 ID:")
    print(result["restaurant_ids"])
    return result