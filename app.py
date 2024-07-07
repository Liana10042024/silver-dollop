import requests
from flask import Flask, render_template, request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import sessionmaker
from db_manager import Base, Case, engine  # your_models.py에서 정의한 모델을 import
import re
import logging
import json
import os
import requests

app = Flask(__name__)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API 설정
API_KEY = "D/spYGY15giVS64SLvtShZlNHxAbr9eDi1uU1Ca1wrqCiU+0YMwcnFy53naflVlg5wemikAYwiugNoIepbpexQ=="
API_URL = "https://api.odcloud.kr/api/15069932/v1/uddi:3799441a-4012-4caa-9955-b4d20697b555"

# 법률 용어 사전
legal_terms_dict = {}

# 법률 용어 사전 파일은 여기 이 파일에 저장 됩니다
CACHE_FILE = "legal_terms_cache.json"

#법률 용어 가져오기(법률 용어를 서버에 요청해서 가져왔는데, 불러온 거 파일에 저장하게 했음)
def get_legal_terms():
    global legal_terms_dict
    
    #이미 법률 용어 사전이 불러와진 상태라면 
    if legal_terms_dict:
        return legal_terms_dict
    
    #만약 캐시된 법률 데이터가 있다면    
    if os.path.exists(CACHE_FILE):
        logging.info("캐시된 법률 용어 데이터 불러오기")
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            legal_terms_dict = json.load(f)
        logging.info(f"{len(legal_terms_dict)}개의 법률 용어를 캐시에서 불러왔습니다.")
    else:
        #캐시 파일도 없다면
        logging.info("API에서 법률 용어 데이터 가져오기 시작")
        params = {
            "serviceKey": API_KEY,
            "page": 1,
            "perPage": 1000
        }
        #서버에서 가져오는 코드
        response = requests.get(API_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                legal_terms_dict = {item['용어명']: item['설명'] for item in data['data']}
                logging.info(f"{len(legal_terms_dict)}개의 법률 용어를 가져왔습니다.")
                
                # 캐시 파일에 저장
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(legal_terms_dict, f, ensure_ascii=False, indent=2)
                logging.info("법률 용어 데이터를 캐시 파일에 저장했습니다.")
            else:
                logging.error("API 응답에 'data' 키가 없습니다.")
        else:
            logging.error(f"API 요청 실패: 상태 코드 {response.status_code}")
    
    return legal_terms_dict

#데이터베이스 파일 불러오기
def load_cases():
    # 데이터베이스 연결 설정
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    logging.info("데이터베이스에서 판례 데이터 로딩 시작")

    try:
        # 전체 Case 수 조회
        total_cases = session.query(Case).count()
        logging.info(f"총 {total_cases}개의 판례가 데이터베이스에 있습니다.")

        # Case 데이터 로드
        cases = []
        for i, case in enumerate(session.query(Case).yield_per(1000)):
            cases.append(case)
            if (i + 1) % 1000 == 0:
                logging.info(f"{i + 1}/{total_cases} 판례 로드 완료")

        logging.info(f"총 {len(cases)}개의 판례를 로드했습니다.")
        return cases

    except Exception as e:
        logging.error(f"데이터 로드 중 오류 발생: {str(e)}")
        return []

    finally:
        session.close()
        
cases = load_cases()

#???
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform([case.summary for case in cases if case.summary])

#법률 용어 볼드체 처리하기, 
def highlight_legal_terms(text):
    terms = get_legal_terms()
    for term, explanation in terms.items():
        pattern = r'\b' + re.escape(term) + r'\b'
        replacement = f'<span class="legal-term" data-toggle="tooltip" title="{explanation}"><strong>{term}</strong></span>'
        text = re.sub(pattern, replacement, text)
    return text

#유저가 입력한 문장과 비슷한 판례 검색 시작
def find_similar_case(user_input):
    logging.info("유사 판례 검색 시작")
    user_vector = vectorizer.transform([user_input])
    similarities = cosine_similarity(user_vector, tfidf_matrix)
    most_similar_idx = similarities.argmax()
    case = cases[most_similar_idx]
    
    logging.info("법률 용어 하이라이트 처리 중")
    case.processed_summary = highlight_legal_terms(case.summary)
    case.processed_question = highlight_legal_terms(case.jdgmnQuestion if case.jdgmnQuestion else "")
    case.processed_answer = highlight_legal_terms(case.jdgmnAnswer if case.jdgmnAnswer else "")
    
    logging.info("유사 판례 검색 및 처리 완료")
    return case

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input = request.form['situation']
        logging.info("사용자 입력 받음, 유사 판례 검색 시작")
        case = find_similar_case(user_input)
        logging.info("검색 결과 페이지 렌더링")
        return render_template('result.html', case=case)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
    