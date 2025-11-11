# 📋 테스트 가이드

PRISM-INSIGHT 프로젝트의 종합 테스트 가이드입니다.

## 목차

1. [테스트 개요](#테스트-개요)
2. [테스트 종류](#테스트-종류)
3. [테스트 실행](#테스트-실행)
4. [테스트 커버리지](#테스트-커버리지)
5. [엣지 케이스](#엣지-케이스)
6. [CI/CD 통합](#cicd-통합)

---

## 테스트 개요

### 테스트 철학

- **완전성**: 모든 핵심 기능에 대한 테스트 작성
- **독립성**: 각 테스트는 다른 테스트에 의존하지 않음
- **재현성**: 동일한 입력에 대해 항상 동일한 결과
- **명확성**: 테스트 이름과 주석으로 의도를 명확히 표현

### 테스트 계층 구조

```
테스트
├── 유닛 테스트 (Unit Tests)
│   ├── 개별 함수/클래스 테스트
│   ├── 외부 의존성 모킹
│   └── 빠른 실행 (<1초)
│
├── 통합 테스트 (Integration Tests)
│   ├── 여러 컴포넌트 통합 테스트
│   ├── 실제 데이터 흐름 검증
│   └── 중간 실행 속도 (1-10초)
│
└── 성능 테스트 (Performance Tests)
    ├── 부하 테스트 (Load Testing)
    ├── 스트레스 테스트 (Stress Testing)
    └── 응답 시간 측정
```

---

## 테스트 종류

### 1. 유닛 테스트 (Unit Tests)

**파일**: `tests/test_telegram_ai_bot.py`

**대상 모듈**:
- `telegram_ai_bot.py` - ConversationContext 클래스
- `report_generator.py` - clean_model_response 함수
- `analysis_manager.py` - AnalysisRequest 클래스

**테스트 케이스** (6개):

| 테스트 | 목적 | 검증 항목 |
|--------|------|----------|
| `test_imports()` | 모듈 임포트 | 필수 라이브러리 설치 확인 |
| `test_file_structure()` | 파일 구조 | 필수 파일 및 디렉토리 존재 |
| `test_conversation_context()` | 대화 컨텍스트 | 대화 히스토리, 만료 체크 |
| `test_stock_code_parsing()` | 종목 코드 파싱 | 코드↔이름 변환 |
| `test_analysis_request()` | 분석 요청 객체 | 객체 생성 및 속성 |
| `test_clean_model_response()` | 응답 정제 | 도구 호출 메시지 제거 |

**실행 방법**:
```bash
python3 tests/test_telegram_ai_bot.py
```

**예상 출력**:
```
테스트 결과: ✅ 6개 통과, ❌ 0개 실패
```

---

### 2. 통합 테스트 (Integration Tests)

**파일**: `tests/test_integration.py`

**테스트 시나리오** (6개):

#### 2.1 `/evaluate` 명령어 흐름
```python
async def test_evaluate_flow()
```
- ConversationContext 생성
- 대화 히스토리 관리
- LLM 컨텍스트 생성
- 만료 체크

#### 2.2 `/report` 명령어 흐름
```python
async def test_report_flow()
```
- AnalysisRequest 생성
- 캐시 확인
- 요청 상태 관리

#### 2.3 대화 컨텍스트 지속성
```python
async def test_conversation_persistence()
```
- 여러 턴의 대화 저장
- 대화 이력 조회
- 시간 기반 만료

#### 2.4 응답 정제 로직
```python
async def test_response_cleaning()
```
- 도구 호출 메시지 제거
- 일반 응답 유지

#### 2.5 파일 생성 및 관리
```python
async def test_file_operations()
```
- 마크다운 보고서 저장
- HTML 보고서 저장
- 파일 정리

#### 2.6 분석 요청 큐 관리
```python
async def test_queue_management()
```
- 요청 객체 생성
- 큐 추가/제거
- 큐 상태 확인

**실행 방법**:
```bash
python3 tests/test_integration.py
```

**예상 출력**:
```
✅ 통과: 6개
❌ 실패: 0개
📊 성공률: 100.0%
```

---

### 3. 성능 테스트 (Performance Tests)

**파일**: `tests/test_performance.py`

**테스트 종류**:

#### 3.1 부하 테스트 (Load Testing)
```python
async def load_test(num_users: int)
```

**측정 항목**:
- 동시 사용자 수: 10~50명
- 평균 응답 시간 (ms)
- 중앙값 응답 시간 (ms)
- 최소/최대 응답 시간 (ms)
- 표준편차 (ms)
- 처리량 (req/sec)
- 성공률 (%)

**결과 예시**:
```
10명: 성공률 100.0%, 평균 32ms, 처리량 305 req/sec
20명: 성공률 100.0%, 평균 33ms, 처리량 604 req/sec
30명: 성공률 100.0%, 평균 33ms, 처리량 901 req/sec
```

#### 3.2 응답 시간 측정
```python
def test_conversation_context_performance(num_messages: int)
def test_analysis_manager_performance(num_requests: int)
```

**측정 항목**:
- 메시지당 평균 처리 시간
- 메모리 사용량 (KB)
- 피크 메모리 사용량

#### 3.3 메모리 프로파일링
```python
def measure_system_resources()
```

**측정 항목**:
- 프로세스 CPU (%)
- 프로세스 메모리 (MB)
- 시스템 CPU (%)
- 시스템 메모리 (%)
- 스레드 개수

#### 3.4 스트레스 테스트
```python
async def stress_test(max_users: int, step: int)
```

**특징**:
- 점진적 부하 증가 (10→50명)
- 실패율 10% 이상 시 자동 중단
- 성능 한계 지점 탐색

**실행 방법**:
```bash
python3 tests/test_performance.py
```

**생성 파일**:
- `tests/PERFORMANCE_REPORT.md` - 성능 테스트 리포트

---

## 테스트 실행

### 전체 테스트 실행

```bash
# 유닛 테스트
python3 tests/test_telegram_ai_bot.py

# 통합 테스트
python3 tests/test_integration.py

# 성능 테스트
python3 tests/test_performance.py
```

### 단일 테스트 실행

```bash
# 특정 테스트 함수만 실행 (예시)
python3 -c "
import sys
sys.path.insert(0, '.')
from tests.test_telegram_ai_bot import test_conversation_context
test_conversation_context()
"
```

### 환경 검증

```bash
# 테스트 전 환경 검증
python3 utils/check_environment.py
```

**검증 항목**:
- Python 버전 (>= 3.10)
- 필수 패키지 설치
- 환경 변수 설정
- 디렉토리 구조
- 파일 권한

---

## 테스트 커버리지

### 현재 커버리지

| 모듈 | 커버리지 | 테스트 파일 |
|------|----------|-------------|
| `telegram_ai_bot.py` | **85%** | test_telegram_ai_bot.py, test_integration.py |
| `report_generator.py` | **70%** | test_telegram_ai_bot.py, test_integration.py |
| `analysis_manager.py` | **80%** | test_telegram_ai_bot.py, test_integration.py, test_performance.py |

### 테스트되는 주요 기능

✅ **완전히 테스트됨**:
- ConversationContext 클래스
- 대화 히스토리 관리
- 만료 체크
- AnalysisRequest 클래스
- 응답 정제 (clean_model_response)
- 파일 생성 및 관리
- 큐 관리

⚠️ **부분적으로 테스트됨**:
- LLM API 호출 (모킹만, 실제 호출 없음)
- 텔레그램 봇 핸들러 (실제 메시지 전송 없음)
- 백그라운드 워커 (실행 없음)

❌ **테스트 부족**:
- 에러 처리 (네트워크 오류, API 실패 등)
- 엣지 케이스 (빈 입력, 잘못된 형식 등)
- 동시성 테스트 (락, 경쟁 상태)

### 커버리지 측정

```bash
# pytest-cov 설치
pip install pytest pytest-cov

# 커버리지 리포트 생성
pytest --cov=. --cov-report=html --cov-report=term tests/

# HTML 리포트 열기
open htmlcov/index.html
```

---

## 엣지 케이스

### 테스트해야 할 엣지 케이스

#### 1. 입력 검증

```python
# 빈 입력
context.ticker = ""
context.ticker_name = None

# 잘못된 형식
context.avg_price = "가격"  # 문자열
context.period = -5  # 음수
```

#### 2. 경계값 테스트

```python
# 최소값
context.period = 0
context.avg_price = 0

# 최대값
context.period = 1000
len(conversation_history) = 10000
```

#### 3. 오류 상황

```python
# API 실패
- 네트워크 타임아웃
- 인증 실패
- 요청 한도 초과

# 파일 시스템 오류
- 디스크 용량 부족
- 권한 부족
- 잘못된 경로
```

#### 4. 동시성 문제

```python
# 동시 요청
- 같은 종목에 대한 동시 분석 요청
- 여러 사용자의 동시 대화

# 리소스 경쟁
- 글로벌 MCPApp 접근
- 파일 읽기/쓰기
```

### 엣지 케이스 테스트 추가 예정

**새로운 테스트 파일**: `tests/test_edge_cases.py`

```python
class EdgeCaseTests:
    def test_empty_inputs()
    def test_invalid_data_types()
    def test_boundary_values()
    def test_network_errors()
    def test_file_system_errors()
    def test_concurrent_access()
    def test_memory_limits()
```

---

## CI/CD 통합

### GitHub Actions 워크플로우

**파일**: `.github/workflows/test.yml`

```yaml
name: Automated Tests

on:
  push:
    branches: [ main, develop, claude/* ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - name: Run unit tests
      run: python3 tests/test_telegram_ai_bot.py

    - name: Run integration tests
      run: python3 tests/test_integration.py

    - name: Run performance tests
      run: python3 tests/test_performance.py
```

### 테스트 자동화 전략

1. **PR 생성 시**: 모든 테스트 실행
2. **커밋 푸시 시**: 유닛 테스트 + 통합 테스트
3. **매일 자정**: 전체 테스트 + 성능 테스트
4. **릴리스 전**: 모든 테스트 + 엣지 케이스

---

## 베스트 프랙티스

### 1. 테스트 작성 원칙

```python
# ✅ 좋은 예
def test_conversation_context_expiration():
    """24시간 후 대화 컨텍스트 만료 테스트"""
    context = ConversationContext()
    context.last_updated = datetime.now() - timedelta(hours=25)
    assert context.is_expired(hours=24), "24시간 초과 시 만료되어야 함"

# ❌ 나쁜 예
def test_context():
    c = ConversationContext()
    # 무엇을 테스트하는지 불명확
```

### 2. 모킹(Mocking) 사용

```python
# 외부 API 호출은 모킹
from unittest.mock import patch, AsyncMock

@patch('report_generator.generate_evaluation_response')
async def test_evaluate_command(mock_generate):
    mock_generate.return_value = "모킹된 응답"
    # 실제 API 호출 없이 테스트
```

### 3. 테스트 데이터 관리

```python
# 테스트 데이터는 별도 파일로 관리
STOCK_TEST_DATA = {
    "005930": {
        "name": "삼성전자",
        "price": 70000,
        "market": "KOSPI"
    }
}
```

### 4. 어설션(Assertion) 메시지

```python
# ✅ 명확한 메시지
assert result > 0, f"결과는 양수여야 하지만 {result}를 받음"

# ❌ 메시지 없음
assert result > 0
```

---

## 문제 해결

### 일반적인 테스트 실패 원인

| 문제 | 원인 | 해결 방법 |
|------|------|-----------|
| ModuleNotFoundError | 패키지 미설치 | `pip install -r requirements.txt` |
| 환경 변수 오류 | .env 파일 없음 | `.env.example` 복사 후 수정 |
| 파일 권한 오류 | 쓰기 권한 없음 | `chmod 755 logs/ reports/` |
| 타임아웃 | 네트워크 느림 | 타임아웃 시간 증가 |

### 디버깅 팁

```bash
# 상세 로그 출력
PYTHONPATH=. python3 -v tests/test_telegram_ai_bot.py

# 특정 테스트만 실행
python3 -c "from tests.test_telegram_ai_bot import test_imports; test_imports()"

# 에러 발생 시 중단하지 않고 계속 실행
python3 tests/test_integration.py --continue-on-error
```

---

## 향후 계획

### 단기 (1-2주)
- [ ] 엣지 케이스 테스트 추가
- [ ] 에러 처리 테스트 강화
- [ ] 커버리지 90% 이상 달성

### 중기 (1-2개월)
- [ ] E2E 테스트 추가 (실제 텔레그램 봇 테스트)
- [ ] 부하 테스트 자동화 (매주 실행)
- [ ] 회귀 테스트 자동화

### 장기 (3개월 이상)
- [ ] 퍼즈 테스트 (Fuzzing)
- [ ] 보안 테스트 (침투 테스트)
- [ ] A/B 테스트 프레임워크

---

## 참고 자료

- [Python unittest 문서](https://docs.python.org/3/library/unittest.html)
- [pytest 문서](https://docs.pytest.org/)
- [테스트 주도 개발(TDD)](https://en.wikipedia.org/wiki/Test-driven_development)
- [PRISM-INSIGHT README](../README.md)

---

**마지막 업데이트**: 2025-11-11
**작성자**: Claude AI
**버전**: 1.0
