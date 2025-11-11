#!/usr/bin/env python3
"""
통합 테스트 (Integration Tests)

전체 시스템의 통합을 테스트합니다.
실제 API 호출은 모킹(mocking)하여 안전하게 테스트합니다.
"""
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class IntegrationTests:
    """통합 테스트 클래스"""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    async def test_evaluate_flow(self):
        """
        /evaluate 명령어 전체 흐름 테스트
        """
        print("=" * 60)
        print("통합 테스트 1: /evaluate 명령어 흐름")
        print("=" * 60)

        try:
            from telegram_ai_bot import ConversationContext
            from report_generator import generate_evaluation_response

            # 1. ConversationContext 생성
            context = ConversationContext()
            context.ticker = "005930"
            context.ticker_name = "삼성전자"
            context.avg_price = 70000
            context.period = 6
            context.tone = "친구같이"
            context.background = "단기 스윙"

            print("✓ ConversationContext 생성 성공")

            # 2. 대화 히스토리 추가
            context.add_to_history("assistant", "첫 번째 응답")
            context.add_to_history("user", "추가 질문")
            assert len(context.conversation_history) == 2
            print("✓ 대화 히스토리 관리 성공")

            # 3. LLM 컨텍스트 생성
            llm_context = context.get_context_for_llm()
            assert "삼성전자" in llm_context
            assert "70,000" in llm_context
            print("✓ LLM 컨텍스트 생성 성공")

            # 4. 만료 체크
            assert not context.is_expired(hours=24)
            print("✓ 만료 체크 성공")

            print("\n✅ /evaluate 흐름 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ /evaluate 흐름 테스트 실패: {e}\n")
            self.failed += 1
            return False

    async def test_report_flow(self):
        """
        /report 명령어 전체 흐름 테스트
        """
        print("=" * 60)
        print("통합 테스트 2: /report 명령어 흐름")
        print("=" * 60)

        try:
            from analysis_manager import AnalysisRequest
            from report_generator import get_cached_report

            # 1. AnalysisRequest 생성
            request = AnalysisRequest(
                stock_code="005930",
                company_name="삼성전자",
                chat_id=123456789,
                message_id=987654321
            )

            assert request.stock_code == "005930"
            assert request.status == "pending"
            print("✓ AnalysisRequest 생성 성공")

            # 2. 캐시 확인 (없어야 정상)
            is_cached, content, file, html = get_cached_report("005930")
            print(f"✓ 캐시 확인 성공 (캐시 존재: {is_cached})")

            # 3. 요청 상태 변경
            request.status = "completed"
            assert request.status == "completed"
            print("✓ 요청 상태 관리 성공")

            print("\n✅ /report 흐름 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ /report 흐름 테스트 실패: {e}\n")
            self.failed += 1
            return False

    async def test_conversation_persistence(self):
        """
        대화 컨텍스트 지속성 테스트
        """
        print("=" * 60)
        print("통합 테스트 3: 대화 컨텍스트 지속성")
        print("=" * 60)

        try:
            from telegram_ai_bot import ConversationContext

            # 1. 여러 대화 추가
            context = ConversationContext()
            context.ticker = "035720"
            context.ticker_name = "카카오"
            context.avg_price = 50000
            context.period = 3
            context.tone = "전문가처럼"

            # 2. 여러 턴의 대화 시뮬레이션
            for i in range(5):
                context.add_to_history("user", f"질문 {i+1}")
                context.add_to_history("assistant", f"응답 {i+1}")

            assert len(context.conversation_history) == 10
            print(f"✓ {len(context.conversation_history)}턴 대화 저장 성공")

            # 3. 컨텍스트 조회
            llm_context = context.get_context_for_llm()
            assert "카카오" in llm_context
            assert "질문 5" in llm_context
            print("✓ 대화 이력 조회 성공")

            # 4. 시간 기반 만료 확인
            from datetime import timedelta
            context.last_updated = datetime.now() - timedelta(hours=25)
            assert context.is_expired(hours=24)
            print("✓ 시간 기반 만료 확인 성공")

            print("\n✅ 대화 컨텍스트 지속성 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 대화 컨텍스트 지속성 테스트 실패: {e}\n")
            self.failed += 1
            return False

    async def test_response_cleaning(self):
        """
        응답 정제 로직 테스트
        """
        print("=" * 60)
        print("통합 테스트 4: 응답 정제 로직")
        print("=" * 60)

        try:
            from report_generator import clean_model_response

            # 1. 도구 호출 메시지 포함된 응답
            dirty_response = """[Calling tool get_stock_ohlcv...]
[Calling tool perplexity_ask...]
이제 수집한 정보를 바탕으로 평가를 해보겠습니다.

삼성전자는 현재 좋은 상승세를 보이고 있습니다."""

            cleaned = clean_model_response(dirty_response)

            # 도구 호출 메시지가 제거되었는지 확인
            assert "[Calling tool" not in cleaned
            assert "삼성전자는" in cleaned
            print("✓ 도구 호출 메시지 제거 성공")

            # 2. 일반 응답 (변경 없음)
            normal_response = "이것은 일반 응답입니다."
            cleaned_normal = clean_model_response(normal_response)
            assert cleaned_normal == normal_response.strip()
            print("✓ 일반 응답 유지 성공")

            print("\n✅ 응답 정제 로직 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 응답 정제 로직 테스트 실패: {e}\n")
            self.failed += 1
            return False

    async def test_file_operations(self):
        """
        파일 생성 및 관리 테스트
        """
        print("=" * 60)
        print("통합 테스트 5: 파일 생성 및 관리")
        print("=" * 60)

        try:
            from report_generator import save_report, save_html_report
            from pathlib import Path

            # 1. 마크다운 보고서 저장
            test_content = "# 테스트 보고서\n\n이것은 테스트입니다."
            md_path = save_report("000000", "테스트종목", test_content)
            assert md_path.exists()
            print(f"✓ 마크다운 보고서 저장 성공: {md_path.name}")

            # 2. HTML 보고서 저장
            html_path = save_html_report("000000", "테스트종목", test_content)
            assert html_path.exists()
            print(f"✓ HTML 보고서 저장 성공: {html_path.name}")

            # 3. 파일 정리
            md_path.unlink()
            html_path.unlink()
            print("✓ 테스트 파일 정리 성공")

            print("\n✅ 파일 생성 및 관리 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 파일 생성 및 관리 테스트 실패: {e}\n")
            self.failed += 1
            return False

    async def test_queue_management(self):
        """
        분석 요청 큐 관리 테스트
        """
        print("=" * 60)
        print("통합 테스트 6: 분석 요청 큐 관리")
        print("=" * 60)

        try:
            from analysis_manager import AnalysisRequest, analysis_queue

            # 1. 요청 객체 생성
            requests = []
            for i in range(3):
                request = AnalysisRequest(
                    stock_code=f"00000{i}",
                    company_name=f"테스트종목{i}",
                    chat_id=123456789 + i
                )
                requests.append(request)

            print(f"✓ {len(requests)}개 요청 객체 생성 성공")

            # 2. 큐가 비어있는지 확인
            assert analysis_queue.empty()
            print("✓ 큐 초기화 확인")

            # 3. 요청 큐에 추가
            for request in requests:
                analysis_queue.put(request)
            print(f"✓ {len(requests)}개 요청 큐에 추가 성공")

            # 4. 큐에서 가져오기
            retrieved_count = 0
            while not analysis_queue.empty():
                analysis_queue.get()
                analysis_queue.task_done()
                retrieved_count += 1

            assert retrieved_count == len(requests)
            print(f"✓ {retrieved_count}개 요청 큐에서 처리 성공")

            print("\n✅ 분석 요청 큐 관리 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 분석 요청 큐 관리 테스트 실패: {e}\n")
            self.failed += 1
            return False

    def print_summary(self):
        """테스트 결과 요약"""
        print("\n" + "=" * 60)
        print("통합 테스트 결과 요약")
        print("=" * 60)
        print(f"✅ 통과: {self.passed}개")
        print(f"❌ 실패: {self.failed}개")
        print(f"📊 성공률: {self.passed / (self.passed + self.failed) * 100:.1f}%")
        print("=" * 60 + "\n")

        if self.failed == 0:
            print("🎉 모든 통합 테스트 통과!")
            return 0
        else:
            print("⚠️ 일부 테스트 실패")
            return 1

    async def run_all_tests(self):
        """모든 통합 테스트 실행"""
        print("\n" + "=" * 60)
        print("PRISM-INSIGHT 통합 테스트 시작")
        print("=" * 60 + "\n")

        # 모든 테스트 실행
        tests = [
            self.test_evaluate_flow,
            self.test_report_flow,
            self.test_conversation_persistence,
            self.test_response_cleaning,
            self.test_file_operations,
            self.test_queue_management,
        ]

        for test in tests:
            try:
                await test()
            except Exception as e:
                print(f"❌ 테스트 중 예외 발생: {e}\n")
                self.failed += 1

        # 결과 요약
        return self.print_summary()


async def main():
    """메인 실행 함수"""
    tester = IntegrationTests()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())
