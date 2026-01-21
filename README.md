# 🎯 AI 모의면접 시스템 (AI Mock Interview System)

파이썬 기반 웹 AI 모의면접 시스템입니다. OpenAI GPT를 활용하여 실시간으로 면접 질문을 생성하고, 답변에 대한 피드백을 제공합니다.

## ✨ 주요 기능

- **AI 기반 질문 생성**: 직무와 경력 수준에 맞는 맞춤형 면접 질문 자동 생성
- **실시간 답변 평가**: AI가 답변을 분석하고 즉각적인 피드백 제공
- **다양한 직무 지원**: 소프트웨어 엔지니어, 프론트엔드/백엔드 개발자, 데이터 사이언티스트 등
- **경력 수준별 질문**: 주니어, 중급, 시니어 수준에 맞는 질문 제공
- **면접 결과 리포트**: 전체 면접 내용과 피드백을 한눈에 확인

## 🛠️ 기술 스택

- **Backend**: Python 3.x, FastAPI
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **AI**: OpenAI GPT-3.5-turbo
- **기타**: python-dotenv (환경변수 관리)

## 📋 사전 요구사항

- Python 3.8 이상
- OpenAI API 키

## 🚀 설치 및 실행

### 1. 저장소 클론

```bash
git clone https://github.com/rockettchoi/AI_Interview_System.git
cd AI_Interview_System
```

### 2. 가상 환경 생성 및 활성화

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 API 키를 설정합니다:

```bash
cp .env.example .env
```

`.env` 파일을 편집하여 실제 값을 입력합니다:

```
OPENAI_API_KEY=your_actual_openai_api_key_here
FLASK_SECRET_KEY=your_random_secret_key_here
FLASK_DEBUG=True  # 개발 환경에서만 True, 프로덕션에서는 False로 설정
```

### 5. 애플리케이션 실행

```bash
python app.py
```

브라우저에서 `http://localhost:5000`으로 접속합니다.

## 📖 사용 방법

1. **면접 시작**: 메인 페이지에서 지원 직무와 경력 수준을 선택하고 "면접 시작" 버튼을 클릭합니다.

2. **질문 답변**: AI가 생성한 질문에 대해 텍스트 박스에 답변을 입력하고 "답변 제출" 버튼을 클릭합니다.

3. **피드백 확인**: AI가 답변을 평가하고 피드백을 제공합니다. 피드백을 확인한 후 "다음 질문" 버튼을 클릭합니다.

4. **결과 확인**: 5개의 질문에 모두 답변하면 "결과 보기" 버튼이 나타납니다. 클릭하여 전체 면접 내용과 피드백을 확인합니다.

## 📁 프로젝트 구조

```
AI_Interview_System/
├── app.py                 # FastAPI 애플리케이션 메인 파일
├── requirements.txt       # Python 의존성 패키지
├── .env.example          # 환경 변수 예시 파일
├── .gitignore            # Git 제외 파일 목록
├── README.md             # 프로젝트 문서
├── static/               # 정적 파일
│   ├── css/
│   │   └── style.css     # 스타일시트
│   └── js/
│       └── main.js       # JavaScript 로직
└── templates/            # HTML 템플릿
    ├── index.html        # 메인 페이지
    ├── results.html      # 결과 페이지
    └── error.html        # 오류 페이지
```

## 🔑 주요 API 엔드포인트

- `GET /` - 메인 페이지
- `POST /start_interview` - 면접 시작 및 첫 질문 생성
- `POST /submit_answer` - 답변 제출 및 평가
- `GET /results` - 면접 결과 페이지

## ⚙️ 설정

### OpenAI API 키 발급

1. [OpenAI 플랫폼](https://platform.openai.com/)에 가입합니다.
2. API Keys 섹션에서 새 API 키를 생성합니다.
3. 생성된 키를 `.env` 파일의 `OPENAI_API_KEY`에 설정합니다.

## 🔒 보안 고려사항

- `.env` 파일은 절대 Git에 커밋하지 마세요 (`.gitignore`에 포함됨)
- 프로덕션 환경에서는 강력한 SECRET_KEY를 사용하세요
- API 키는 안전하게 보관하고 공개하지 마세요

## 🚀 향후 개선 계획

- [ ] 데이터베이스 연동 (면접 기록 영구 저장)
- [ ] 사용자 인증 및 계정 관리
- [ ] 음성 인식 및 TTS 기능
- [ ] 더 다양한 직무 및 질문 카테고리
- [ ] 면접 통계 및 분석 기능
- [ ] 다국어 지원

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 👥 기여

기여는 언제나 환영합니다! 이슈를 등록하거나 Pull Request를 보내주세요.

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.
