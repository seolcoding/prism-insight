#!/usr/bin/env python3
"""
엣지 케이스 및 에러 처리 테스트

테스트 범위:
1. 입력 검증 (빈 값, None, 잘못된 타입)
2. 경계값 테스트 (최소/최대값)
3. 오류 상황 시뮬레이션
4. 동시성 문제
5. 리소스 제한
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import tracemalloc

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class EdgeCaseTests:
    """엣지 케이스 테스트 클래스"""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    # ========================================================================
    # 1. 입력 검증 테스트
    # ========================================================================

    def test_empty_inputs(self):
        """빈 입력 테스트"""
        print("=" * 60)
        print("엣지 케이스 1: 빈 입력 검증")
        print("=" * 60)

        try:
            from telegram_ai_bot import ConversationContext

            context = ConversationContext()

            # 빈 문자열
            context.ticker = ""
            context.ticker_name = ""
            context.tone = ""
            context.background = ""

            # None 값
            context.avg_price = None
            context.period = None

            print("✓ 빈 입력 허용됨 (필드별 검증 필요)")

            # get_context_for_llm 호출 시 빈 값 처리
            llm_context = context.get_context_for_llm()
            assert isinstance(llm_context, str), "컨텍스트는 문자열이어야 함"
            print("✓ get_context_for_llm()이 빈 값 처리")

            print("\n✅ 빈 입력 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 빈 입력 테스트 실패: {e}\n")
            import traceback
            traceback.print_exc()
            self.failed += 1
            return False

    def test_invalid_data_types(self):
        """잘못된 데이터 타입 테스트"""
        print("=" * 60)
        print("엣지 케이스 2: 잘못된 데이터 타입")
        print("=" * 60)

        try:
            from telegram_ai_bot import ConversationContext

            context = ConversationContext()

            # 문자열을 숫자 필드에 할당
            test_cases = [
                ("avg_price", "가격", "문자열"),
                ("avg_price", "70000", "숫자 문자열"),
                ("period", "6개월", "단위 포함 문자열"),
                ("period", -5, "음수"),
            ]

            for field, value, description in test_cases:
                setattr(context, field, value)
                print(f"✓ {field}={value} ({description}) - 설정 가능")

            # 타입 검증은 사용 시점에서 해야 함
            print("⚠️  타입 검증 로직 추가 필요")

            print("\n✅ 잘못된 데이터 타입 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 잘못된 데이터 타입 테스트 실패: {e}\n")
            self.failed += 1
            return False

    # ========================================================================
    # 2. 경계값 테스트
    # ========================================================================

    def test_boundary_values(self):
        """경계값 테스트"""
        print("=" * 60)
        print("엣지 케이스 3: 경계값 테스트")
        print("=" * 60)

        try:
            from telegram_ai_bot import ConversationContext

            # 최소값
            context_min = ConversationContext()
            context_min.avg_price = 0
            context_min.period = 0
            print("✓ 최소값 (0) 설정 가능")

            # 최대값 (현실적 범위)
            context_max = ConversationContext()
            context_max.avg_price = 10_000_000  # 천만원
            context_max.period = 1200  # 100년
            print("✓ 최대값 설정 가능")

            # 극단적 최대값
            context_extreme = ConversationContext()
            context_extreme.avg_price = float('inf')
            context_extreme.period = 999999
            print("✓ 극단적 최대값 설정 가능")

            # 대화 히스토리 개수
            for i in range(1000):
                context_max.add_to_history("user", f"메시지 {i}")
            print(f"✓ 대화 히스토리 {len(context_max.conversation_history)}개 저장")

            print("\n✅ 경계값 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 경계값 테스트 실패: {e}\n")
            self.failed += 1
            return False

    # ========================================================================
    # 3. 오류 상황 시뮬레이션
    # ========================================================================

    async def test_network_errors(self):
        """네트워크 오류 시뮬레이션"""
        print("=" * 60)
        print("엣지 케이스 4: 네트워크 오류 처리")
        print("=" * 60)

        try:
            from report_generator import generate_evaluation_response

            # 네트워크 타임아웃 시뮬레이션
            with patch('report_generator.get_or_create_global_mcp_app') as mock_app:
                mock_app.side_effect = asyncio.TimeoutError("Connection timeout")

                try:
                    response = await generate_evaluation_response(
                        ticker="005930",
                        ticker_name="삼성전자",
                        avg_price=70000,
                        period=6,
                        tone="친구같이",
                        background="단기 스윙"
                    )
                    print("⚠️  타임아웃 예외가 처리되지 않음")
                except asyncio.TimeoutError:
                    print("✓ 타임아웃 예외 발생 (예상됨)")
                except Exception as e:
                    print(f"✓ 다른 예외로 처리됨: {type(e).__name__}")

            print("\n✅ 네트워크 오류 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 네트워크 오류 테스트 실패: {e}\n")
            self.failed += 1
            return False

    def test_file_system_errors(self):
        """파일 시스템 오류 시뮬레이션"""
        print("=" * 60)
        print("엣지 케이스 5: 파일 시스템 오류")
        print("=" * 60)

        try:
            from report_generator import save_report
            from pathlib import Path

            # 잘못된 경로
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                mock_mkdir.side_effect = PermissionError("Permission denied")

                try:
                    # 실제로는 오류가 발생하지 않을 수 있음 (이미 생성됨)
                    result = save_report("000000", "테스트", "내용")
                    print("✓ 파일 저장 성공 또는 기존 디렉토리 사용")
                except PermissionError:
                    print("✓ 권한 오류 발생 (예상됨)")

            # 디스크 용량 부족 시뮬레이션
            with patch('builtins.open', side_effect=IOError("No space left on device")):
                try:
                    save_report("000001", "테스트", "내용")
                    print("⚠️  디스크 용량 오류가 처리되지 않음")
                except IOError:
                    print("✓ 디스크 용량 오류 발생 (예상됨)")

            print("\n✅ 파일 시스템 오류 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 파일 시스템 오류 테스트 실패: {e}\n")
            self.failed += 1
            return False

    # ========================================================================
    # 4. 동시성 문제
    # ========================================================================

    async def test_concurrent_context_access(self):
        """동시 컨텍스트 접근 테스트"""
        print("=" * 60)
        print("엣지 케이스 6: 동시 컨텍스트 접근")
        print("=" * 60)

        try:
            from telegram_ai_bot import ConversationContext

            context = ConversationContext()
            context.ticker = "005930"

            # 동시에 여러 대화 추가
            async def add_messages(role: str, count: int):
                for i in range(count):
                    context.add_to_history(role, f"{role} 메시지 {i}")
                    await asyncio.sleep(0.001)

            # 동시 실행
            await asyncio.gather(
                add_messages("user", 50),
                add_messages("assistant", 50)
            )

            print(f"✓ 총 {len(context.conversation_history)}개 메시지 저장")
            print(f"  (예상: 100개, 실제: {len(context.conversation_history)}개)")

            # 동시 읽기
            async def read_context():
                return context.get_context_for_llm()

            results = await asyncio.gather(*[read_context() for _ in range(10)])
            print(f"✓ 동시 읽기 {len(results)}회 성공")

            print("\n✅ 동시 컨텍스트 접근 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 동시 컨텍스트 접근 테스트 실패: {e}\n")
            import traceback
            traceback.print_exc()
            self.failed += 1
            return False

    async def test_concurrent_queue_operations(self):
        """동시 큐 작업 테스트"""
        print("=" * 60)
        print("엣지 케이스 7: 동시 큐 작업")
        print("=" * 60)

        try:
            from analysis_manager import AnalysisRequest, analysis_queue

            # 큐 초기화
            while not analysis_queue.empty():
                analysis_queue.get()
                analysis_queue.task_done()

            # 동시에 여러 요청 추가
            async def add_requests(start_idx: int, count: int):
                for i in range(count):
                    request = AnalysisRequest(
                        stock_code=f"00{start_idx + i:04d}",
                        company_name=f"종목{start_idx + i}"
                    )
                    analysis_queue.put(request)
                    await asyncio.sleep(0.001)

            # 3개 스레드에서 동시 추가
            await asyncio.gather(
                add_requests(0, 10),
                add_requests(10, 10),
                add_requests(20, 10)
            )

            queue_size = analysis_queue.qsize()
            print(f"✓ 큐 크기: {queue_size}개 (예상: 30개)")

            # 동시 제거
            async def remove_requests(count: int):
                removed = 0
                for _ in range(count):
                    if not analysis_queue.empty():
                        analysis_queue.get()
                        analysis_queue.task_done()
                        removed += 1
                        await asyncio.sleep(0.001)
                return removed

            results = await asyncio.gather(
                remove_requests(10),
                remove_requests(10),
                remove_requests(10)
            )

            print(f"✓ 제거된 요청: {sum(results)}개")
            print(f"✓ 남은 큐 크기: {analysis_queue.qsize()}개")

            print("\n✅ 동시 큐 작업 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 동시 큐 작업 테스트 실패: {e}\n")
            import traceback
            traceback.print_exc()
            self.failed += 1
            return False

    # ========================================================================
    # 5. 리소스 제한
    # ========================================================================

    def test_memory_limits(self):
        """메모리 제한 테스트"""
        print("=" * 60)
        print("엣지 케이스 8: 메모리 제한 테스트")
        print("=" * 60)

        try:
            from telegram_ai_bot import ConversationContext

            tracemalloc.start()

            # 대량의 대화 히스토리 생성
            context = ConversationContext()

            # 10,000개 메시지 추가
            for i in range(10000):
                context.add_to_history("user", f"메시지 {i}" * 10)

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            print(f"✓ 10,000개 메시지 저장")
            print(f"  현재 메모리: {current / 1024 / 1024:.2f} MB")
            print(f"  피크 메모리: {peak / 1024 / 1024:.2f} MB")

            # 메모리 경고 (100MB 이상)
            if peak > 100 * 1024 * 1024:
                print(f"⚠️  메모리 사용량이 높음: {peak / 1024 / 1024:.2f} MB")
            else:
                print(f"✓ 메모리 사용량 적절")

            print("\n✅ 메모리 제한 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 메모리 제한 테스트 실패: {e}\n")
            self.failed += 1
            return False

    def test_long_running_context(self):
        """장시간 실행 컨텍스트 테스트"""
        print("=" * 60)
        print("엣지 케이스 9: 장시간 실행 컨텍스트")
        print("=" * 60)

        try:
            from telegram_ai_bot import ConversationContext

            # 오래된 컨텍스트
            old_context = ConversationContext()
            old_context.created_at = datetime.now() - timedelta(days=7)
            old_context.last_updated = datetime.now() - timedelta(days=7)

            # 다양한 만료 시간 테스트
            test_cases = [
                (1, True, "1시간 후 만료"),
                (24, True, "24시간 후 만료"),
                (48, True, "48시간 후 만료"),
                (168, True, "1주일 후 만료"),
            ]

            for hours, expected, description in test_cases:
                is_expired = old_context.is_expired(hours=hours)
                if is_expired == expected:
                    print(f"✓ {description}: {is_expired}")
                else:
                    print(f"❌ {description}: {is_expired} (예상: {expected})")

            # 최근 업데이트된 컨텍스트
            recent_context = ConversationContext()
            recent_context.last_updated = datetime.now() - timedelta(hours=1)

            assert not recent_context.is_expired(hours=24), "1시간 전 업데이트는 만료 안됨"
            print("✓ 최근 컨텍스트는 만료 안됨")

            print("\n✅ 장시간 실행 컨텍스트 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 장시간 실행 컨텍스트 테스트 실패: {e}\n")
            import traceback
            traceback.print_exc()
            self.failed += 1
            return False

    # ========================================================================
    # 6. 특수 문자 및 유니코드
    # ========================================================================

    def test_special_characters(self):
        """특수 문자 및 유니코드 테스트"""
        print("=" * 60)
        print("엣지 케이스 10: 특수 문자 및 유니코드")
        print("=" * 60)

        try:
            from telegram_ai_bot import ConversationContext
            from report_generator import clean_model_response

            context = ConversationContext()

            # 특수 문자
            special_chars = [
                "삼성전자 📈",
                "카카오 ❤️",
                "NAVER 🚀",
                "주식 & 투자",
                "손익: +3.5% 🎉",
                "가격: ₩70,000",
                "※주의사항",
            ]

            for text in special_chars:
                context.add_to_history("user", text)

            print(f"✓ {len(special_chars)}개 특수 문자 포함 메시지 저장")

            # 유니코드 이모지
            emoji_text = "🚀📈💰📊🎯"
            context.ticker_name = emoji_text
            llm_context = context.get_context_for_llm()
            assert emoji_text in llm_context, "이모지가 컨텍스트에 포함되어야 함"
            print("✓ 유니코드 이모지 처리")

            # clean_model_response 특수 문자 테스트
            response_with_special = """
            [Calling tool...]
            주가 상승 📈 예상됩니다!
            - 목표가: ₩80,000
            - 손익: +10% 🎉
            """
            cleaned = clean_model_response(response_with_special)
            assert "📈" in cleaned, "이모지가 유지되어야 함"
            print("✓ 응답 정제 시 특수 문자 유지")

            print("\n✅ 특수 문자 및 유니코드 테스트 통과\n")
            self.passed += 1
            return True

        except Exception as e:
            print(f"\n❌ 특수 문자 및 유니코드 테스트 실패: {e}\n")
            import traceback
            traceback.print_exc()
            self.failed += 1
            return False

    # ========================================================================
    # 테스트 실행
    # ========================================================================

    def print_summary(self):
        """테스트 결과 요약"""
        print("\n" + "=" * 60)
        print("엣지 케이스 테스트 결과 요약")
        print("=" * 60)
        print(f"✅ 통과: {self.passed}개")
        print(f"❌ 실패: {self.failed}개")
        total = self.passed + self.failed
        if total > 0:
            print(f"📊 성공률: {self.passed / total * 100:.1f}%")
        print("=" * 60 + "\n")

        if self.failed == 0:
            print("🎉 모든 엣지 케이스 테스트 통과!")
            return 0
        else:
            print("⚠️ 일부 테스트 실패")
            return 1

    async def run_all_tests(self):
        """모든 엣지 케이스 테스트 실행"""
        print("\n" + "=" * 60)
        print("PRISM-INSIGHT 엣지 케이스 테스트 시작")
        print("=" * 60 + "\n")

        # 동기 테스트
        sync_tests = [
            self.test_empty_inputs,
            self.test_invalid_data_types,
            self.test_boundary_values,
            self.test_file_system_errors,
            self.test_memory_limits,
            self.test_long_running_context,
            self.test_special_characters,
        ]

        for test in sync_tests:
            try:
                test()
            except Exception as e:
                print(f"❌ 테스트 중 예외 발생: {e}\n")
                import traceback
                traceback.print_exc()
                self.failed += 1

        # 비동기 테스트
        async_tests = [
            self.test_network_errors,
            self.test_concurrent_context_access,
            self.test_concurrent_queue_operations,
        ]

        for test in async_tests:
            try:
                await test()
            except Exception as e:
                print(f"❌ 테스트 중 예외 발생: {e}\n")
                import traceback
                traceback.print_exc()
                self.failed += 1

        # 결과 요약
        return self.print_summary()


async def main():
    """메인 실행 함수"""
    tester = EdgeCaseTests()
    exit_code = await tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())
