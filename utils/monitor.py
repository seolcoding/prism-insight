#!/usr/bin/env python3
"""
시스템 모니터링 도구

시스템 상태, 성능, 사용 통계를 모니터링합니다.
"""
import json
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class SystemMonitor:
    """시스템 모니터링 클래스"""

    def __init__(self, stats_file: str = "logs/system_stats.json"):
        self.stats_file = Path(stats_file)
        self.stats_file.parent.mkdir(exist_ok=True)
        self.stats = self.load_stats()

    def load_stats(self) -> Dict:
        """저장된 통계 로드"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {
            "requests": {},
            "errors": {},
            "performance": [],
            "system": []
        }

    def save_stats(self):
        """통계 저장"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

    def record_request(self, endpoint: str, duration_ms: float, success: bool = True):
        """요청 기록"""
        date_key = datetime.now().strftime("%Y-%m-%d")

        if endpoint not in self.stats["requests"]:
            self.stats["requests"][endpoint] = {}

        if date_key not in self.stats["requests"][endpoint]:
            self.stats["requests"][endpoint][date_key] = {
                "count": 0,
                "success": 0,
                "failed": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0
            }

        data = self.stats["requests"][endpoint][date_key]
        data["count"] += 1

        if success:
            data["success"] += 1
        else:
            data["failed"] += 1

        data["total_duration_ms"] += duration_ms
        data["avg_duration_ms"] = data["total_duration_ms"] / data["count"]

        self.save_stats()

    def record_error(self, error_type: str, error_message: str):
        """에러 기록"""
        date_key = datetime.now().strftime("%Y-%m-%d")

        if error_type not in self.stats["errors"]:
            self.stats["errors"][error_type] = {}

        if date_key not in self.stats["errors"][error_type]:
            self.stats["errors"][error_type][date_key] = []

        self.stats["errors"][error_type][date_key].append({
            "timestamp": datetime.now().isoformat(),
            "message": error_message
        })

        self.save_stats()

    def record_system_metrics(self):
        """시스템 메트릭 기록"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
        }

        # 프로세스별 메모리 사용량
        try:
            import os
            process = psutil.Process(os.getpid())
            metrics["process_memory_mb"] = process.memory_info().rss / 1024 / 1024
        except:
            pass

        self.stats["system"].append(metrics)

        # 최근 24시간 데이터만 보관
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.stats["system"] = [
            m for m in self.stats["system"]
            if datetime.fromisoformat(m["timestamp"]) > cutoff_time
        ]

        self.save_stats()

    def get_summary(self, days: int = 7) -> Dict:
        """통계 요약"""
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        summary = {
            "period_days": days,
            "requests_by_endpoint": {},
            "errors_by_type": {},
            "system_avg": {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0
            }
        }

        # 요청 통계
        for endpoint, dates in self.stats["requests"].items():
            total_count = 0
            total_success = 0
            total_failed = 0
            total_duration = 0

            for date_key, data in dates.items():
                if date_key >= cutoff_date:
                    total_count += data["count"]
                    total_success += data["success"]
                    total_failed += data["failed"]
                    total_duration += data["total_duration_ms"]

            if total_count > 0:
                summary["requests_by_endpoint"][endpoint] = {
                    "total": total_count,
                    "success": total_success,
                    "failed": total_failed,
                    "success_rate": (total_success / total_count) * 100,
                    "avg_duration_ms": total_duration / total_count
                }

        # 에러 통계
        for error_type, dates in self.stats["errors"].items():
            total_errors = 0
            for date_key, errors in dates.items():
                if date_key >= cutoff_date:
                    total_errors += len(errors)

            if total_errors > 0:
                summary["errors_by_type"][error_type] = total_errors

        # 시스템 평균
        if self.stats["system"]:
            cpu_avg = sum(m["cpu_percent"] for m in self.stats["system"]) / len(self.stats["system"])
            mem_avg = sum(m["memory_percent"] for m in self.stats["system"]) / len(self.stats["system"])
            disk_avg = sum(m["disk_percent"] for m in self.stats["system"]) / len(self.stats["system"])

            summary["system_avg"] = {
                "cpu_percent": round(cpu_avg, 2),
                "memory_percent": round(mem_avg, 2),
                "disk_percent": round(disk_avg, 2)
            }

        return summary

    def print_summary(self, days: int = 7):
        """통계 요약 출력"""
        summary = self.get_summary(days)

        print(f"\n{'='*60}")
        print(f"시스템 모니터링 요약 (최근 {days}일)")
        print(f"{'='*60}\n")

        # 요청 통계
        if summary["requests_by_endpoint"]:
            print("📊 요청 통계:")
            for endpoint, data in summary["requests_by_endpoint"].items():
                print(f"\n  {endpoint}:")
                print(f"    총 요청: {data['total']}회")
                print(f"    성공: {data['success']}회")
                print(f"    실패: {data['failed']}회")
                print(f"    성공률: {data['success_rate']:.1f}%")
                print(f"    평균 응답시간: {data['avg_duration_ms']:.0f}ms")

        # 에러 통계
        if summary["errors_by_type"]:
            print("\n❌ 에러 통계:")
            for error_type, count in summary["errors_by_type"].items():
                print(f"  {error_type}: {count}회")

        # 시스템 메트릭
        print(f"\n💻 시스템 평균 사용률:")
        print(f"  CPU: {summary['system_avg']['cpu_percent']}%")
        print(f"  메모리: {summary['system_avg']['memory_percent']}%")
        print(f"  디스크: {summary['system_avg']['disk_percent']}%")

        print(f"\n{'='*60}\n")


# 사용 예시
if __name__ == '__main__':
    monitor = SystemMonitor()

    # 샘플 데이터 기록
    print("샘플 데이터 기록 중...\n")

    # 요청 기록
    monitor.record_request("/evaluate", 1200, success=True)
    monitor.record_request("/evaluate", 1500, success=True)
    monitor.record_request("/evaluate", 2000, success=False)
    monitor.record_request("/report", 8000, success=True)
    monitor.record_request("/report", 7500, success=True)

    # 에러 기록
    monitor.record_error("APIError", "OpenAI API timeout")
    monitor.record_error("DatabaseError", "Connection failed")

    # 시스템 메트릭 기록
    monitor.record_system_metrics()

    # 요약 출력
    monitor.print_summary(days=7)

    print(f"✅ 통계 저장 완료: {monitor.stats_file}")
