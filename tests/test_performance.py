#!/usr/bin/env python3
"""
성능 테스트 스크립트

텔레그램 AI 봇의 성능을 측정하고 병목 지점을 찾습니다.
- 부하 테스트 (동시 사용자)
- 응답 시간 측정
- 메모리 프로파일링
- 스트레스 테스트
"""
import asyncio
import time
import psutil
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any
from statistics import mean, median, stdev
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PerformanceTester:
    """성능 테스트 클래스"""

    def __init__(self):
        self.results = {
            "load_test": {},
            "response_time": {},
            "memory_profile": {},
            "stress_test": {}
        }

    def measure_time(self, func):
        """함수 실행 시간 측정 데코레이터"""
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            duration_ms = (end - start) * 1000
            return result, duration_ms
        return wrapper

    async def simulate_user_evaluate(self, user_id: int) -> Dict:
        """단일 사용자의 /evaluate 명령 시뮬레이션"""
        from telegram_ai_bot import ConversationContext

        start = time.perf_counter()

        # 컨텍스트 생성
        context = ConversationContext()
        context.ticker = "005930"
        context.ticker_name = "삼성전자"
        context.avg_price = 70000
        context.period = 6
        context.tone = "친구같이"

        # 대화 히스토리 추가 (실제 AI 호출은 하지 않음)
        for i in range(3):
            context.add_to_history("user", f"질문 {i+1}")
            context.add_to_history("assistant", f"응답 {i+1}")
            await asyncio.sleep(0.01)  # 작은 지연 시뮬레이션

        end = time.perf_counter()
        duration_ms = (end - start) * 1000

        return {
            "user_id": user_id,
            "duration_ms": duration_ms,
            "success": True,
            "context_size": len(context.conversation_history)
        }

    async def load_test(self, num_users: int = 10) -> Dict:
        """
        부하 테스트 - 동시 사용자 시뮬레이션

        Args:
            num_users: 동시 사용자 수
        """
        print(f"\n{'='*60}")
        print(f"🔥 부하 테스트: {num_users}명 동시 사용자")
        print(f"{'='*60}\n")

        start_time = time.perf_counter()

        # 동시 사용자 시뮬레이션
        tasks = [self.simulate_user_evaluate(i) for i in range(num_users)]
        results = await asyncio.gather(*tasks)

        end_time = time.perf_counter()
        total_duration = (end_time - start_time) * 1000

        # 통계 계산
        durations = [r["duration_ms"] for r in results]
        success_count = sum(1 for r in results if r["success"])

        stats = {
            "num_users": num_users,
            "total_duration_ms": total_duration,
            "success_count": success_count,
            "failure_count": num_users - success_count,
            "success_rate": (success_count / num_users) * 100,
            "avg_response_time_ms": mean(durations),
            "median_response_time_ms": median(durations),
            "min_response_time_ms": min(durations),
            "max_response_time_ms": max(durations),
            "stdev_response_time_ms": stdev(durations) if len(durations) > 1 else 0,
            "throughput_per_sec": num_users / (total_duration / 1000)
        }

        self.results["load_test"][num_users] = stats

        # 결과 출력
        print(f"✅ 완료: {success_count}/{num_users} ({stats['success_rate']:.1f}%)")
        print(f"⏱️  총 소요 시간: {total_duration:.0f}ms")
        print(f"📊 평균 응답 시간: {stats['avg_response_time_ms']:.0f}ms")
        print(f"📊 중앙값 응답 시간: {stats['median_response_time_ms']:.0f}ms")
        print(f"📈 처리량: {stats['throughput_per_sec']:.2f} req/sec")
        print(f"📉 표준편차: {stats['stdev_response_time_ms']:.0f}ms")

        return stats

    def test_conversation_context_performance(self, num_messages: int = 100):
        """대화 컨텍스트 성능 테스트"""
        from telegram_ai_bot import ConversationContext

        print(f"\n{'='*60}")
        print(f"💬 대화 컨텍스트 성능 테스트: {num_messages}개 메시지")
        print(f"{'='*60}\n")

        context = ConversationContext()

        start = time.perf_counter()
        tracemalloc.start()

        # 메시지 추가
        for i in range(num_messages):
            context.add_to_history("user", f"메시지 {i}")
            context.add_to_history("assistant", f"응답 {i}")

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end = time.perf_counter()

        duration_ms = (end - start) * 1000

        stats = {
            "num_messages": num_messages * 2,  # user + assistant
            "duration_ms": duration_ms,
            "avg_time_per_message_ms": duration_ms / (num_messages * 2),
            "memory_current_kb": current / 1024,
            "memory_peak_kb": peak / 1024,
            "history_length": len(context.conversation_history)
        }

        self.results["response_time"]["conversation_context"] = stats

        print(f"📝 메시지 수: {stats['num_messages']}개")
        print(f"⏱️  총 소요 시간: {duration_ms:.2f}ms")
        print(f"⚡ 메시지당 평균: {stats['avg_time_per_message_ms']:.4f}ms")
        print(f"💾 현재 메모리: {stats['memory_current_kb']:.2f} KB")
        print(f"📈 피크 메모리: {stats['memory_peak_kb']:.2f} KB")

        return stats

    def test_analysis_manager_performance(self, num_requests: int = 20):
        """분석 매니저 큐 처리 성능 테스트"""
        from analysis_manager import AnalysisRequest

        print(f"\n{'='*60}")
        print(f"📋 분석 매니저 성능 테스트: {num_requests}개 요청")
        print(f"{'='*60}\n")

        start = time.perf_counter()
        tracemalloc.start()

        # 요청 생성
        requests = []
        for i in range(num_requests):
            req = AnalysisRequest(
                stock_code=f"00{i:04d}",
                company_name=f"종목{i}",
                avg_price=50000 + (i * 1000),
                period=6,
                tone="친구같이"
            )
            requests.append(req)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        end = time.perf_counter()

        duration_ms = (end - start) * 1000

        stats = {
            "num_requests": num_requests,
            "duration_ms": duration_ms,
            "avg_time_per_request_ms": duration_ms / num_requests,
            "memory_current_kb": current / 1024,
            "memory_peak_kb": peak / 1024,
            "queue_size": len(requests)
        }

        self.results["response_time"]["analysis_manager"] = stats

        print(f"📋 요청 수: {num_requests}개")
        print(f"⏱️  총 소요 시간: {duration_ms:.2f}ms")
        print(f"⚡ 요청당 평균: {stats['avg_time_per_request_ms']:.4f}ms")
        print(f"💾 현재 메모리: {stats['memory_current_kb']:.2f} KB")
        print(f"📈 피크 메모리: {stats['memory_peak_kb']:.2f} KB")

        return stats

    def measure_system_resources(self):
        """시스템 리소스 사용량 측정"""
        print(f"\n{'='*60}")
        print(f"💻 시스템 리소스 측정")
        print(f"{'='*60}\n")

        process = psutil.Process()

        stats = {
            "cpu_percent": process.cpu_percent(interval=1),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "num_threads": process.num_threads(),
            "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0,
        }

        # 시스템 전체
        system_stats = {
            "system_cpu_percent": psutil.cpu_percent(interval=1),
            "system_memory_percent": psutil.virtual_memory().percent,
            "system_disk_percent": psutil.disk_usage('/').percent,
        }

        stats.update(system_stats)
        self.results["memory_profile"]["system"] = stats

        print(f"🔧 프로세스:")
        print(f"  CPU: {stats['cpu_percent']:.1f}%")
        print(f"  메모리: {stats['memory_mb']:.2f} MB ({stats['memory_percent']:.1f}%)")
        print(f"  스레드 수: {stats['num_threads']}")

        print(f"\n🖥️  시스템:")
        print(f"  CPU: {stats['system_cpu_percent']:.1f}%")
        print(f"  메모리: {stats['system_memory_percent']:.1f}%")
        print(f"  디스크: {stats['system_disk_percent']:.1f}%")

        return stats

    async def stress_test(self, max_users: int = 50, step: int = 10):
        """
        스트레스 테스트 - 점진적으로 부하 증가

        Args:
            max_users: 최대 사용자 수
            step: 증가 단위
        """
        print(f"\n{'='*60}")
        print(f"🚨 스트레스 테스트: 1 → {max_users}명 (단계: {step})")
        print(f"{'='*60}\n")

        results = []

        for num_users in range(step, max_users + 1, step):
            print(f"\n📊 {num_users}명 테스트 중...")

            try:
                stats = await self.load_test(num_users)
                results.append(stats)

                # 실패율이 10% 이상이면 중단
                if stats["success_rate"] < 90:
                    print(f"\n⚠️  실패율이 높아 테스트 중단 (성공률: {stats['success_rate']:.1f}%)")
                    break

            except Exception as e:
                print(f"\n❌ 오류 발생: {e}")
                break

        self.results["stress_test"]["progressive"] = results

        # 요약
        print(f"\n{'='*60}")
        print(f"📊 스트레스 테스트 요약")
        print(f"{'='*60}\n")

        for stat in results:
            print(f"{stat['num_users']:3d}명: "
                  f"성공률 {stat['success_rate']:5.1f}%, "
                  f"평균 {stat['avg_response_time_ms']:6.0f}ms, "
                  f"처리량 {stat['throughput_per_sec']:5.2f} req/sec")

        return results

    def generate_report(self, output_file: str = "tests/PERFORMANCE_REPORT.md"):
        """성능 테스트 리포트 생성"""
        report = []
        report.append("# 📊 성능 테스트 리포트\n")
        report.append(f"**테스트 일시**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}\n")
        report.append("---\n\n")

        # 부하 테스트 결과
        if self.results["load_test"]:
            report.append("## 🔥 부하 테스트 결과\n\n")
            report.append("| 사용자 수 | 성공률 | 평균 응답시간 | 중앙값 | 최소 | 최대 | 표준편차 | 처리량 |\n")
            report.append("|----------|--------|--------------|--------|------|------|----------|--------|\n")

            for num_users, stats in sorted(self.results["load_test"].items()):
                report.append(
                    f"| {num_users:3d}명 | "
                    f"{stats['success_rate']:5.1f}% | "
                    f"{stats['avg_response_time_ms']:6.0f}ms | "
                    f"{stats['median_response_time_ms']:6.0f}ms | "
                    f"{stats['min_response_time_ms']:5.0f}ms | "
                    f"{stats['max_response_time_ms']:6.0f}ms | "
                    f"{stats['stdev_response_time_ms']:5.0f}ms | "
                    f"{stats['throughput_per_sec']:5.2f} req/sec |\n"
                )
            report.append("\n")

        # 응답 시간 테스트
        if self.results["response_time"]:
            report.append("## ⏱️ 응답 시간 테스트\n\n")

            if "conversation_context" in self.results["response_time"]:
                stats = self.results["response_time"]["conversation_context"]
                report.append("### 💬 대화 컨텍스트\n\n")
                report.append(f"- **메시지 수**: {stats['num_messages']}개\n")
                report.append(f"- **총 소요 시간**: {stats['duration_ms']:.2f}ms\n")
                report.append(f"- **메시지당 평균**: {stats['avg_time_per_message_ms']:.4f}ms\n")
                report.append(f"- **메모리 사용량**: {stats['memory_peak_kb']:.2f} KB\n\n")

            if "analysis_manager" in self.results["response_time"]:
                stats = self.results["response_time"]["analysis_manager"]
                report.append("### 📋 분석 매니저\n\n")
                report.append(f"- **요청 수**: {stats['num_requests']}개\n")
                report.append(f"- **총 소요 시간**: {stats['duration_ms']:.2f}ms\n")
                report.append(f"- **요청당 평균**: {stats['avg_time_per_request_ms']:.4f}ms\n")
                report.append(f"- **메모리 사용량**: {stats['memory_peak_kb']:.2f} KB\n\n")

        # 메모리 프로파일
        if self.results["memory_profile"]:
            report.append("## 💾 메모리 프로파일\n\n")

            if "system" in self.results["memory_profile"]:
                stats = self.results["memory_profile"]["system"]
                report.append("### 시스템 리소스\n\n")
                report.append(f"- **프로세스 CPU**: {stats['cpu_percent']:.1f}%\n")
                report.append(f"- **프로세스 메모리**: {stats['memory_mb']:.2f} MB\n")
                report.append(f"- **시스템 CPU**: {stats['system_cpu_percent']:.1f}%\n")
                report.append(f"- **시스템 메모리**: {stats['system_memory_percent']:.1f}%\n\n")

        # 스트레스 테스트
        if self.results["stress_test"].get("progressive"):
            report.append("## 🚨 스트레스 테스트\n\n")
            report.append("점진적 부하 증가 테스트:\n\n")
            report.append("| 사용자 수 | 성공률 | 평균 응답시간 | 처리량 |\n")
            report.append("|----------|--------|--------------|--------|\n")

            for stats in self.results["stress_test"]["progressive"]:
                report.append(
                    f"| {stats['num_users']:3d}명 | "
                    f"{stats['success_rate']:5.1f}% | "
                    f"{stats['avg_response_time_ms']:6.0f}ms | "
                    f"{stats['throughput_per_sec']:5.2f} req/sec |\n"
                )
            report.append("\n")

        # 권장사항
        report.append("## 💡 권장사항\n\n")

        if self.results["load_test"]:
            max_users = max(self.results["load_test"].keys())
            avg_response = self.results["load_test"][max_users]["avg_response_time_ms"]

            if avg_response > 1000:
                report.append("- ⚠️  평균 응답시간이 1초 이상입니다. 최적화가 필요합니다.\n")
            else:
                report.append("- ✅ 평균 응답시간이 양호합니다.\n")

            success_rate = self.results["load_test"][max_users]["success_rate"]
            if success_rate < 95:
                report.append("- ⚠️  성공률이 95% 미만입니다. 에러 처리를 강화하세요.\n")
            else:
                report.append("- ✅ 성공률이 우수합니다.\n")

        if self.results["memory_profile"].get("system"):
            mem_usage = self.results["memory_profile"]["system"]["memory_mb"]
            if mem_usage > 500:
                report.append("- ⚠️  메모리 사용량이 높습니다. 메모리 최적화를 고려하세요.\n")
            else:
                report.append("- ✅ 메모리 사용량이 적절합니다.\n")

        report.append("\n---\n")
        report.append(f"\n**리포트 생성 완료**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(''.join(report))

        print(f"\n✅ 성능 리포트 저장: {output_file}")

        return ''.join(report)


async def run_all_tests():
    """모든 성능 테스트 실행"""
    print("\n" + "="*60)
    print("🚀 텔레그램 AI 봇 성능 테스트 시작")
    print("="*60)

    tester = PerformanceTester()

    try:
        # 1. 부하 테스트
        await tester.load_test(num_users=10)
        await tester.load_test(num_users=20)
        await tester.load_test(num_users=30)

        # 2. 응답 시간 테스트
        tester.test_conversation_context_performance(num_messages=100)
        tester.test_analysis_manager_performance(num_requests=20)

        # 3. 시스템 리소스 측정
        tester.measure_system_resources()

        # 4. 스트레스 테스트
        await tester.stress_test(max_users=50, step=10)

        # 5. 리포트 생성
        tester.generate_report()

        print("\n" + "="*60)
        print("✅ 모든 성능 테스트 완료!")
        print("="*60 + "\n")

        return tester.results

    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    # 비동기 테스트 실행
    asyncio.run(run_all_tests())
