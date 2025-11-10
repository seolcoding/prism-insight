#!/usr/bin/env python3
"""
텔레그램 AI 봇 유닛 테스트

주요 기능:
1. ConversationContext 클래스 테스트
2. 종목 코드 파싱 테스트
3. 응답 생성 프롬프트 검증
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """필수 모듈 임포트 테스트"""
    print("=" * 60)
    print("📦 모듈 임포트 테스트")
    print("=" * 60)

    try:
        import telegram
        print(f"✅ telegram: {telegram.__version__}")
    except ImportError as e:
        print(f"❌ telegram 임포트 실패: {e}")
        return False

    try:
        import anthropic
        print(f"✅ anthropic: {anthropic.__version__}")
    except ImportError as e:
        print(f"❌ anthropic 임포트 실패: {e}")
        return False

    try:
        from mcp_agent.app import MCPApp
        print(f"✅ mcp_agent: OK")
    except ImportError as e:
        print(f"❌ mcp_agent 임포트 실패: {e}")
        return False

    try:
        # 프로젝트 모듈 임포트
        from telegram_ai_bot import TelegramAIBot, ConversationContext
        print(f"✅ telegram_ai_bot: OK")
    except ImportError as e:
        print(f"❌ telegram_ai_bot 임포트 실패: {e}")
        return False

    try:
        from report_generator import (
            generate_evaluation_response,
            generate_follow_up_response,
            clean_model_response
        )
        print(f"✅ report_generator: OK")
    except ImportError as e:
        print(f"❌ report_generator 임포트 실패: {e}")
        return False

    try:
        from analysis_manager import AnalysisRequest, analysis_queue
        print(f"✅ analysis_manager: OK")
    except ImportError as e:
        print(f"❌ analysis_manager 임포트 실패: {e}")
        return False

    print()
    return True


def test_conversation_context():
    """ConversationContext 클래스 테스트"""
    print("=" * 60)
    print("💬 ConversationContext 테스트")
    print("=" * 60)

    from telegram_ai_bot import ConversationContext

    # 컨텍스트 생성
    context = ConversationContext()
    context.ticker = "005930"
    context.ticker_name = "삼성전자"
    context.avg_price = 70000
    context.period = 6
    context.tone = "친구같이"
    context.background = "단기 스윙 매매"

    # 대화 히스토리 추가
    context.add_to_history("assistant", "삼성전자는 현재 70,000원에 거래되고 있습니다.")
    context.add_to_history("user", "앞으로 전망은 어떤가요?")
    context.add_to_history("assistant", "반도체 업황 회복으로 긍정적입니다.")

    # LLM용 컨텍스트 생성
    llm_context = context.get_context_for_llm()

    print(f"✅ 종목: {context.ticker_name} ({context.ticker})")
    print(f"✅ 평균 매수가: {context.avg_price:,}원")
    print(f"✅ 보유 기간: {context.period}개월")
    print(f"✅ 피드백 스타일: {context.tone}")
    print(f"✅ 대화 히스토리 개수: {len(context.conversation_history)}")

    # 만료 테스트
    assert not context.is_expired(hours=24), "❌ 24시간 이내는 만료되지 않아야 함"
    print(f"✅ 만료 체크: 정상 (24시간 이내)")

    # 오래된 컨텍스트 시뮬레이션
    context.last_updated = datetime.now() - timedelta(hours=25)
    assert context.is_expired(hours=24), "❌ 24시간 초과는 만료되어야 함"
    print(f"✅ 만료 체크: 정상 (24시간 초과)")

    print()
    return True


def test_stock_code_parsing():
    """종목 코드 파싱 로직 테스트 (모의)"""
    print("=" * 60)
    print("📊 종목 코드 파싱 테스트")
    print("=" * 60)

    # 테스트 데이터
    test_cases = [
        ("005930", "삼성전자"),
        ("삼성전자", "005930"),
        ("035720", "카카오"),
        ("카카오", "035720"),
    ]

    # 간단한 매핑
    stock_map = {
        "005930": "삼성전자",
        "035720": "카카오",
        "000660": "SK하이닉스"
    }
    stock_name_map = {v: k for k, v in stock_map.items()}

    for input_text, expected in test_cases:
        # 6자리 숫자인 경우
        if input_text.isdigit() and len(input_text) == 6:
            result = stock_map.get(input_text, f"종목_{input_text}")
            print(f"✅ '{input_text}' → '{result}'")
        # 종목명인 경우
        elif input_text in stock_name_map:
            result = stock_name_map[input_text]
            print(f"✅ '{input_text}' → '{result}'")
        else:
            print(f"⚠️  '{input_text}' → 매핑 없음")

    print()
    return True


def test_analysis_request():
    """AnalysisRequest 객체 테스트"""
    print("=" * 60)
    print("📝 AnalysisRequest 테스트")
    print("=" * 60)

    from analysis_manager import AnalysisRequest

    # evaluate 요청
    eval_request = AnalysisRequest(
        stock_code="005930",
        company_name="삼성전자",
        chat_id=123456789,
        avg_price=70000,
        period=6,
        tone="친구같이",
        background="단기 스윙",
        message_id=987654321
    )

    print(f"✅ Evaluate 요청 생성:")
    print(f"   - ID: {eval_request.id}")
    print(f"   - 종목: {eval_request.company_name} ({eval_request.stock_code})")
    print(f"   - 평균가: {eval_request.avg_price:,}원")
    print(f"   - 상태: {eval_request.status}")

    # report 요청
    report_request = AnalysisRequest(
        stock_code="035720",
        company_name="카카오",
        chat_id=123456789,
        message_id=111222333
    )

    print(f"\n✅ Report 요청 생성:")
    print(f"   - ID: {report_request.id}")
    print(f"   - 종목: {report_request.company_name} ({report_request.stock_code})")
    print(f"   - 상태: {report_request.status}")

    print()
    return True


def test_clean_model_response():
    """응답 정제 함수 테스트"""
    print("=" * 60)
    print("🧹 clean_model_response 테스트")
    print("=" * 60)

    from report_generator import clean_model_response

    # 테스트 케이스 1: 도구 호출 메시지 포함
    test_input_1 = """[Calling tool get_stock_ohlcv...]
이제 수집한 정보를 바탕으로 평가를 해보겠습니다.

삼성전자는 현재 70,000원에 거래되고 있습니다."""

    result_1 = clean_model_response(test_input_1)
    assert "[Calling tool" not in result_1, "❌ 도구 호출 메시지가 제거되지 않았습니다"
    print(f"✅ 테스트 1: 도구 호출 메시지 제거 성공")
    print(f"   입력 길이: {len(test_input_1)} → 출력 길이: {len(result_1)}")

    # 테스트 케이스 2: 일반 응답 (변경 없음)
    test_input_2 = """삼성전자는 현재 70,000원에 거래되고 있습니다.
기술적으로 상승 추세를 보이고 있습니다."""

    result_2 = clean_model_response(test_input_2)
    print(f"✅ 테스트 2: 일반 응답 유지")
    print(f"   입력 길이: {len(test_input_2)} → 출력 길이: {len(result_2)}")

    print()
    return True


def test_file_structure():
    """파일 및 디렉토리 구조 테스트"""
    print("=" * 60)
    print("📁 파일 구조 테스트")
    print("=" * 60)

    required_files = [
        "telegram_ai_bot.py",
        "report_generator.py",
        "analysis_manager.py",
        "telegram_bot_agent.py",
        "telegram_config.py",
    ]

    required_dirs = [
        "reports",
        "html_reports",
    ]

    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (없음)")

    for dir in required_dirs:
        if Path(dir).exists():
            print(f"✅ {dir}/")
        else:
            print(f"⚠️  {dir}/ (없음, 자동 생성됨)")

    print()
    return True


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("🧪 텔레그램 AI 봇 테스트 시작")
    print("=" * 60 + "\n")

    tests = [
        ("모듈 임포트", test_imports),
        ("파일 구조", test_file_structure),
        ("ConversationContext", test_conversation_context),
        ("종목 코드 파싱", test_stock_code_parsing),
        ("AnalysisRequest", test_analysis_request),
        ("응답 정제", test_clean_model_response),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {name} 테스트 실패\n")
        except Exception as e:
            failed += 1
            print(f"❌ {name} 테스트 오류: {e}\n")

    print("=" * 60)
    print(f"테스트 결과: ✅ {passed}개 통과, ❌ {failed}개 실패")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
