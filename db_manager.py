import json
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Case(Base):
    __tablename__ = "cases"
    db_id = Column(Integer, primary_key=True, index=True)
    id = Column(Integer)
    caseNm = Column(String)
    caseTitle = Column(Text)
    courtType = Column(String)
    courtNm = Column(String)
    judmnAdjuDe = Column(String)
    caseNo = Column(String)
    
    jdgmn = Column(Text)
    jdgmnQuestion = Column(Text)
    jdgmnAnswer = Column(Text)
    summary = Column(String)
    summary_pass = Column(String)
    keyword_tagg = Column(String)
    reference_rules = Column(Text)
    reference_court_case = Column(Text)
    class_name = Column(String)
    instance_name = Column(String)

class JudgmentInfo(Base):
    __tablename__ = 'judgment_info'

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    question = Column(Text)
    answer = Column(String)

# 데이터베이스 연결 설정
engine = create_engine('sqlite:///legal_cases.db')
Base.metadata.create_all(engine)
SessionMaker = sessionmaker(bind=engine)
session = SessionMaker()

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    try:
        case = Case(
            id=data['info']['id'],
            caseNm=data['info']['caseNm'],
            caseTitle=data['info']['caseTitle'],
            courtType=data['info']['courtType'],
            courtNm=data['info']['courtNm'],
            judmnAdjuDe=data['info']['judmnAdjuDe'],
            caseNo=data['info']['caseNo'],
            jdgmn=data['jdgmn'],
            jdgmnQuestion=data['jdgmnInfo'][0]['question'],
            jdgmnAnswer=data['jdgmnInfo'][0] ['answer'],

            summary= data['Summary'][0]['summ_contxt'],
            summary_pass = data['Summary'][0]['summ_pass'],
            keyword_tagg= data['keyword_tagg'][0]['keyword'],
            reference_rules=data['Reference_info']['reference_rules'],
            reference_court_case=data['Reference_info']['reference_court_case'],
            class_name=data['Class_info']['class_name'],
            instance_name=data['Class_info']['instance_name']
        )
        
        session.add(case)
        
        for judgment_info in data['jdgmnInfo']:
            judgment = JudgmentInfo(
                case_id=case.id,
                question=judgment_info['question'],
                answer=judgment_info['answer']
            )
            session.add(judgment)
        
        session.commit()
        print(f"파일 {file_path}의 데이터가 성공적으로 저장되었습니다.")
    
    except Exception as e:
        session.rollback()
        print(f"파일 {file_path} 처리 중 오류 발생: {str(e)}")
    
    finally:
        session.close()
        
def process_directory(directory_path):
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                process_file(file_path)


def load(filepath):
    # 지정된 디렉토리의 모든 JSON 파일을 불러오기
    process_directory(filepath)


def print_case_data(case):
    print(f"Case ID: {case.id}")
    print(f"Case Title: {case.caseTitle}")
    print(f"Court Type: {case.courtType}")
    print(f"Court Name: {case.courtNm}")
    print(f"Keyword Tagg: {case.keyword_tagg}")

    print(f"Judgment Date: {case.judmnAdjuDe}")
    print(f"Case Number: {case.caseNo}")
    print(f"Reference Rules: {case.reference_rules}")
    print(f"Reference Court Case: {case.reference_court_case}")
    print(f"Class Name: {case.class_name}")
    print(f"Instance Name: {case.instance_name}")
    
    # 관련된 JudgmentInfo 출력
    judgments = session.query(JudgmentInfo).filter(JudgmentInfo.case_id == case.id).all()
    for judgment in judgments:
        print(f"  Question: {judgment.question}")
        print(f"  Answer: {judgment.answer}")
    print("\n")
#load('C:\\Users\\admin\\Downloads\\proj_mini\\TL')

specific_cases = session.query(Case).filter(Case.keyword_tagg == '무효심판청구').all()
print("대법원 케이스:")
for case in specific_cases:
    print_case_data(case)

session.close()