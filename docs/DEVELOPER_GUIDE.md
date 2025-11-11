# 🔧 개발자 가이드

PRISM-INSIGHT 프로젝트 개발자를 위한 종합 가이드입니다.

## 목차

1. [시작하기](#시작하기)
2. [아키텍처](#아키텍처)
3. [LLM 통합](#llm-통합)
4. [API 레퍼런스](#api-레퍼런스)
5. [개발 워크플로우](#개발-워크플로우)
6. [코드 스타일](#코드-스타일)
7. [문제 해결](#문제-해결)

---

## 시작하기

### 개발 환경 설정

```bash
# 1. 저장소 클론
git clone https://github.com/your-repo/prism-insight.git
cd prism-insight

# 2. Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 API 키 등 설정

# 5. 환경 검증
python3 utils/check_environment.py

# 6. 테스트 실행
python3 tests/test_telegram_ai_bot.py
```

### 필수 도구

- **Python 3.10+**
- **Git**
- **텍스트 에디터**: VS Code, PyCharm 등
- **Docker** (선택사항)

### 권장 VS Code 확장

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "streetsidesoftware.code-spell-checker"
  ]
}
```

---

## 아키텍처

### 전체 시스템 구조

```
┌─────────────────────────────────────────────────────────┐
│                  텔레그램 사용자                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│           Telegram Bot API (python-telegram-bot)        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│               telegram_ai_bot.py                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  ConversationHandler                             │   │
│  │  - /evaluate → CHOOSING_TICKER                   │   │
│  │  - /report → REPORT_CHOOSING_TICKER              │   │
│  │  - /history → HISTORY_CHOOSING_TICKER            │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  ConversationContext (대화 컨텍스트 관리)         │   │
│  │  - ticker, ticker_name, avg_price, period        │   │
│  │  - conversation_history (24시간 유지)            │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              report_generator.py                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  전역 MCPApp 관리                                │   │
│  │  - get_or_create_global_mcp_app()               │   │
│  │  - cleanup_global_mcp_app()                     │   │
│  └──────────────┬───────────────────────────────────┘   │
│                 │                                        │
│                 ▼                                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  MCP Agent (mcp_agent)                          │   │
│  │  ┌─────────────────────────────────────────┐    │   │
│  │  │  Agent                                  │    │   │
│  │  │  - attach_llm(AnthropicAugmentedLLM)   │    │   │
│  │  │  - run_with_tools()                     │    │   │
│  │  └─────────────────────────────────────────┘    │   │
│  └──────────────┬───────────────────────────────────┘   │
│                 │                                        │
│                 ▼                                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  AI 응답 생성                                    │   │
│  │  - generate_evaluation_response()               │   │
│  │  - generate_follow_up_response()                │   │
│  │  - clean_model_response()                       │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│            analysis_manager.py                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  AnalysisRequest (분석 요청 큐)                  │   │
│  │  - stock_code, company_name, chat_id            │   │
│  │  - status: pending → processing → completed     │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  백그라운드 워커 (background_worker)             │   │
│  │  - 큐에서 요청 가져오기                          │   │
│  │  - AI 분석 실행                                  │   │
│  │  - 결과 파일 저장                                │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              파일 시스템                                 │
│  - reports/ (Markdown 보고서)                           │
│  - html_reports/ (HTML 보고서)                          │
│  - logs/ (로그 파일)                                    │
└─────────────────────────────────────────────────────────┘
```

### 주요 컴포넌트

#### 1. telegram_ai_bot.py

**역할**: 텔레그램 봇의 진입점 및 메시지 핸들러

**주요 클래스**:
- `ConversationContext`: 사용자별 대화 상태 관리
- `TelegramAIBot` (선택사항, 현재는 함수 기반)

**핵심 기능**:
```python
# 대화 상태 관리
conversation_contexts: Dict[int, ConversationContext] = {}

# 명령어 핸들러
async def evaluate_command(update, context)
async def report_command(update, context)
async def history_command(update, context)

# 대화 흐름 핸들러
async def choose_ticker(update, context)  # CHOOSING_TICKER
async def enter_avgprice(update, context)  # ENTERING_AVGPRICE
async def enter_period(update, context)    # ENTERING_PERIOD
async def enter_tone(update, context)      # ENTERING_TONE
```

#### 2. report_generator.py

**역할**: LLM을 사용한 AI 응답 생성 및 보고서 관리

**핵심 패턴**: 전역 MCPApp 관리로 프로세스 누적 방지

```python
# 전역 MCPApp 인스턴스 (싱글톤)
_global_mcp_app: Optional[MCPApp] = None
_app_lock = asyncio.Lock()

async def get_or_create_global_mcp_app() -> MCPApp:
    """전역 MCPApp 반환 (없으면 생성)"""
    async with _app_lock:
        if _global_mcp_app is None:
            _global_mcp_app = MCPApp(name="telegram_ai_bot_global")
            await _global_mcp_app.initialize()
        return _global_mcp_app
```

**주요 함수**:
```python
# AI 응답 생성
async def generate_evaluation_response(...)
async def generate_follow_up_response(...)

# 보고서 관리
def save_report(stock_code, company_name, content) -> Path
def save_html_report(stock_code, company_name, content) -> Path
def get_cached_report(stock_code) -> tuple

# 응답 정제
def clean_model_response(response: str) -> str
```

#### 3. analysis_manager.py

**역할**: 백그라운드 분석 작업 큐 관리

**핵심 구조**:
```python
class AnalysisRequest:
    """분석 요청 객체"""
    def __init__(self, stock_code, company_name, chat_id, ...):
        self.id = str(uuid.uuid4())
        self.stock_code = stock_code
        self.company_name = company_name
        self.chat_id = chat_id
        self.status = "pending"  # pending → processing → completed
        self.created_at = datetime.now()

# 글로벌 큐
analysis_queue = Queue()

# 백그라운드 워커
async def background_worker():
    while True:
        request = analysis_queue.get()
        # 분석 실행
        analysis_queue.task_done()
```

---

## LLM 통합

### LLM 아키텍처

PRISM-INSIGHT는 **MCP Agent 프레임워크**를 사용하여 LLM과 통합합니다.

#### MCP (Model Context Protocol)

```python
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
```

### 현재 사용 중인 LLM

**Anthropic Claude Sonnet 4.5**

```python
# report_generator.py:465-475
mcp_app = await get_or_create_global_mcp_app()
agent = Agent(name="telegram_bot_agent", mcp_app=mcp_app)

# LLM 연결
llm = await agent.attach_llm(AnthropicAugmentedLLM)

# 요청 실행
response = await llm.run_with_tools(
    instructions=prompt,
    request_params=RequestParams(...)
)
```

### LLM 변경 방법

MCP Agent는 다양한 LLM 백엔드를 지원합니다:

#### 1. OpenAI로 변경

```python
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

# report_generator.py에서 변경
llm = await agent.attach_llm(OpenAIAugmentedLLM)
```

**필요한 환경 변수**:
```bash
OPENAI_API_KEY=sk-...
```

#### 2. Google Gemini로 변경

```python
from mcp_agent.workflows.llm.augmented_llm_google import GoogleAugmentedLLM

llm = await agent.attach_llm(GoogleAugmentedLLM)
```

**필요한 환경 변수**:
```bash
GOOGLE_API_KEY=...
```

#### 3. 커스텀 LLM 추가

```python
from mcp_agent.workflows.llm.augmented_llm import AugmentedLLM, RequestParams

class CustomLLM(AugmentedLLM):
    """커스텀 LLM 구현"""

    async def run_with_tools(
        self,
        instructions: str,
        request_params: RequestParams
    ) -> str:
        # 커스텀 LLM 호출 로직
        response = await your_llm_client.generate(instructions)
        return response
```

**사용**:
```python
llm = await agent.attach_llm(CustomLLM)
```

### LLM 프롬프트 최적화

#### 평가 프롬프트 구조

```python
# report_generator.py:477-510
prompt = f"""
당신은 주식 투자 전문가입니다.

**종목 정보**:
- 종목명: {ticker_name} ({ticker})
- 평균 매수가: {avg_price:,}원
- 보유 기간: {period}개월
- 매매 배경: {background}

**요청사항**:
사용자의 투자 상황을 평가하고 조언을 제공하세요.

**톤**: {tone}
"""
```

#### 후속 질문 프롬프트

```python
# report_generator.py:540-570
prompt = f"""
**대화 컨텍스트**:
{context.get_context_for_llm()}

**새로운 질문**:
{user_question}

**요청사항**:
위 컨텍스트를 참고하여 사용자의 질문에 답변하세요.
"""
```

### LLM 요청 파라미터

```python
from mcp_agent.workflows.llm.augmented_llm import RequestParams

request_params = RequestParams(
    model="claude-sonnet-4.5",
    temperature=0.7,         # 창의성 (0.0-1.0)
    max_tokens=4000,         # 최대 토큰 수
    top_p=0.9,               # 샘플링 확률
    # ... 기타 파라미터
)
```

**파라미터 설명**:
- `temperature`: 낮을수록 일관성, 높을수록 창의적
- `max_tokens`: 응답 길이 제한
- `top_p`: 누적 확률 샘플링 (0.9 권장)

---

## API 레퍼런스

### ConversationContext

**위치**: `telegram_ai_bot.py:74-110`

```python
class ConversationContext:
    """사용자별 대화 컨텍스트 관리"""

    def __init__(self):
        self.message_id: Optional[int] = None
        self.chat_id: Optional[int] = None
        self.user_id: Optional[int] = None
        self.ticker: Optional[str] = None
        self.ticker_name: Optional[str] = None
        self.avg_price: Optional[float] = None
        self.period: Optional[int] = None
        self.tone: Optional[str] = None
        self.background: Optional[str] = None
        self.conversation_history: List[Dict] = []
        self.created_at: datetime = datetime.now()
        self.last_updated: datetime = datetime.now()

    def add_to_history(self, role: str, content: str):
        """대화 히스토리에 메시지 추가"""

    def get_context_for_llm(self) -> str:
        """LLM용 컨텍스트 문자열 생성"""

    def is_expired(self, hours: int = 24) -> bool:
        """컨텍스트 만료 여부 확인"""
```

**예제**:
```python
context = ConversationContext()
context.ticker = "005930"
context.ticker_name = "삼성전자"
context.avg_price = 70000
context.period = 6
context.tone = "친구같이"

# 대화 추가
context.add_to_history("user", "앞으로 전망은?")
context.add_to_history("assistant", "긍정적입니다.")

# LLM용 컨텍스트 가져오기
llm_context = context.get_context_for_llm()

# 만료 확인
if context.is_expired(hours=24):
    print("컨텍스트 만료됨")
```

---

### AnalysisRequest

**위치**: `analysis_manager.py:23-50`

```python
class AnalysisRequest:
    """분석 요청 객체"""

    def __init__(
        self,
        stock_code: str,
        company_name: str,
        chat_id: int = None,
        avg_price: float = None,
        period: int = None,
        tone: str = None,
        background: str = None,
        message_id: int = None
    ):
        self.id: str = str(uuid.uuid4())
        self.stock_code: str = stock_code
        self.company_name: str = company_name
        self.chat_id: int = chat_id
        self.avg_price: float = avg_price
        self.period: int = period
        self.tone: str = tone
        self.background: str = background
        self.message_id: int = message_id
        self.status: str = "pending"
        self.created_at: datetime = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
```

**예제**:
```python
from analysis_manager import AnalysisRequest, analysis_queue

# 요청 생성
request = AnalysisRequest(
    stock_code="005930",
    company_name="삼성전자",
    chat_id=123456789,
    message_id=987654321
)

# 큐에 추가
analysis_queue.put(request)

# 상태 확인
print(f"상태: {request.status}")  # "pending"
```

---

### generate_evaluation_response

**위치**: `report_generator.py:445-520`

```python
async def generate_evaluation_response(
    ticker: str,
    ticker_name: str,
    avg_price: float,
    period: int,
    tone: str,
    background: str,
    report_path: str = None
) -> str:
    """
    종목 평가 AI 응답 생성

    Args:
        ticker: 종목 코드
        ticker_name: 종목 이름
        avg_price: 평균 매수가
        period: 보유 기간 (개월)
        tone: 피드백 스타일/톤
        background: 매매 배경/히스토리
        report_path: 보고서 파일 경로 (선택)

    Returns:
        AI 응답 문자열
    """
```

**예제**:
```python
response = await generate_evaluation_response(
    ticker="005930",
    ticker_name="삼성전자",
    avg_price=70000,
    period=6,
    tone="친구같이",
    background="단기 스윙 매매"
)

print(response)
```

---

### generate_follow_up_response

**위치**: `report_generator.py:523-590`

```python
async def generate_follow_up_response(
    context: ConversationContext,
    user_question: str
) -> str:
    """
    후속 질문에 대한 AI 응답 생성

    Args:
        context: 대화 컨텍스트
        user_question: 사용자 질문

    Returns:
        AI 응답 문자열
    """
```

**예제**:
```python
context = conversation_contexts[user_id]

# 사용자 질문 추가
context.add_to_history("user", "앞으로 전망은?")

# AI 응답 생성
response = await generate_follow_up_response(
    context=context,
    user_question="앞으로 전망은?"
)

# 응답 추가
context.add_to_history("assistant", response)
```

---

### clean_model_response

**위치**: `report_generator.py:593-620`

```python
def clean_model_response(response: str) -> str:
    """
    AI 모델 응답에서 불필요한 부분 제거

    Args:
        response: AI 모델의 원본 응답

    Returns:
        정제된 응답
    """
```

**예제**:
```python
raw_response = """
[Calling tool get_stock_ohlcv...]
[Calling tool perplexity_ask...]
삼성전자는 현재 좋은 상승세를 보이고 있습니다.
"""

cleaned = clean_model_response(raw_response)
print(cleaned)
# 출력: "삼성전자는 현재 좋은 상승세를 보이고 있습니다."
```

---

## 개발 워크플로우

### Git 브랜치 전략

```
main (프로덕션)
  │
  ├─── develop (개발)
  │     │
  │     ├─── feature/evaluate-command
  │     ├─── feature/report-generation
  │     └─── bugfix/context-expiration
  │
  └─── hotfix/critical-bug
```

### 커밋 메시지 컨벤션

```
<타입>: <제목>

<본문>

<푸터>
```

**타입**:
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `test`: 테스트 추가/수정
- `refactor`: 코드 리팩토링
- `chore`: 기타 변경사항

**예시**:
```
feat: Add conversation context expiration check

- Add is_expired() method to ConversationContext
- Set default expiration to 24 hours
- Add unit tests for expiration logic

Closes #123
```

### 코드 리뷰 체크리스트

- [ ] 코드 스타일 준수 (PEP 8)
- [ ] 타입 힌트 추가
- [ ] 유닛 테스트 작성
- [ ] 문서 업데이트
- [ ] 에러 처리 추가
- [ ] 로깅 추가

---

## 코드 스타일

### PEP 8 준수

```bash
# 코드 포맷팅
black telegram_ai_bot.py

# 린팅
flake8 telegram_ai_bot.py
pylint telegram_ai_bot.py
```

### 타입 힌트

```python
# ✅ 좋은 예
from typing import Optional, List, Dict

def get_user_context(user_id: int) -> Optional[ConversationContext]:
    """사용자 컨텍스트 조회"""
    return conversation_contexts.get(user_id)

async def generate_response(
    ticker: str,
    price: float
) -> str:
    """AI 응답 생성"""
    pass

# ❌ 나쁜 예
def get_user_context(user_id):
    return conversation_contexts.get(user_id)
```

### 문서화

```python
def complex_function(param1: str, param2: int) -> Dict:
    """
    함수 설명을 한 줄로 작성

    더 자세한 설명이 필요하면 여기에 작성합니다.
    여러 줄에 걸쳐 작성할 수 있습니다.

    Args:
        param1: 첫 번째 파라미터 설명
        param2: 두 번째 파라미터 설명

    Returns:
        반환값 설명

    Raises:
        ValueError: 발생 가능한 예외 설명

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        {'key': 'value'}
    """
    pass
```

---

## 문제 해결

### 일반적인 문제

#### 1. MCPApp 초기화 실패

**증상**:
```
ERROR - 전역 MCPApp 초기화 실패
```

**원인**:
- mcp_agent 패키지 미설치
- 환경 변수 누락

**해결**:
```bash
pip install mcp-agent
export ANTHROPIC_API_KEY=sk-ant-...
```

#### 2. 대화 컨텍스트 손실

**증상**: 사용자의 이전 대화가 기억되지 않음

**원인**: 컨텍스트가 24시간 후 만료됨

**해결**:
```python
# 만료 시간 연장
context.is_expired(hours=48)  # 48시간으로 변경
```

#### 3. 파일 저장 오류

**증상**:
```
PermissionError: [Errno 13] Permission denied: 'reports/...'
```

**해결**:
```bash
chmod 755 reports/
chmod 755 html_reports/
```

### 디버깅 팁

```python
# 로깅 레벨 변경
logging.basicConfig(level=logging.DEBUG)

# 상세 로그
logger.debug(f"Context: {context.__dict__}")
logger.debug(f"Request params: {request_params}")

# 예외 추적
try:
    result = await some_function()
except Exception as e:
    logger.exception("상세 오류 정보:")
    raise
```

---

## 참고 자료

- [Python 공식 문서](https://docs.python.org/3/)
- [python-telegram-bot 문서](https://python-telegram-bot.readthedocs.io/)
- [MCP Agent 문서](https://github.com/anthropics/mcp-agent)
- [Anthropic API 문서](https://docs.anthropic.com/)

---

**마지막 업데이트**: 2025-11-11
**작성자**: Claude AI
**버전**: 1.0
