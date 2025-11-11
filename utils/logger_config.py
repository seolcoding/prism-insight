"""
구조화된 로깅 설정 모듈

JSON 형식의 구조화된 로그를 생성하여 분석 및 모니터링을 용이하게 합니다.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """JSON 형식 로그 포매터"""

    def format(self, record: logging.LogRecord) -> str:
        """로그를 JSON 형식으로 변환"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 추가 컨텍스트 정보
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'stock_code'):
            log_data["stock_code"] = record.stock_code
        if hasattr(record, 'action'):
            log_data["action"] = record.action
        if hasattr(record, 'duration'):
            log_data["duration_ms"] = record.duration

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """컬러 터미널 출력 포매터"""

    # ANSI 색상 코드
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def format(self, record: logging.LogRecord) -> str:
        """컬러 포맷 적용"""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{self.BOLD}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(
    name: str,
    log_dir: str = "logs",
    level: int = logging.INFO,
    json_format: bool = False,
    console_output: bool = True
) -> logging.Logger:
    """
    구조화된 로거 설정

    Args:
        name: 로거 이름
        log_dir: 로그 파일 저장 디렉토리
        level: 로그 레벨
        json_format: JSON 형식 사용 여부
        console_output: 콘솔 출력 여부

    Returns:
        설정된 로거
    """
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 기존 핸들러 제거 (중복 방지)
    logger.handlers.clear()

    # 로그 디렉토리 생성
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 파일 핸들러 (일별 로테이션)
    file_handler = TimedRotatingFileHandler(
        filename=log_path / f"{name}.log",
        when="midnight",
        interval=1,
        backupCount=30,  # 30일 보관
        encoding="utf-8"
    )
    file_handler.setLevel(level)

    if json_format:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

    logger.addHandler(file_handler)

    # 에러 전용 파일 핸들러
    error_handler = RotatingFileHandler(
        filename=log_path / f"{name}_error.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)

    if json_format:
        error_handler.setFormatter(JSONFormatter())
    else:
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            'Module: %(module)s, Function: %(funcName)s, Line: %(lineno)d\n'
            '%(message)s\n'
        ))

    logger.addHandler(error_handler)

    # 콘솔 핸들러
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        console_handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

        logger.addHandler(console_handler)

    return logger


class LogContext:
    """로그 컨텍스트 관리자"""

    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds() * 1000

        # 로그 레코드에 컨텍스트 추가
        extra = {**self.context, 'duration': duration}

        if exc_type is None:
            self.logger.info(
                f"작업 완료: {self.context.get('action', 'unknown')}",
                extra=extra
            )
        else:
            self.logger.error(
                f"작업 실패: {self.context.get('action', 'unknown')} - {exc_val}",
                extra=extra,
                exc_info=(exc_type, exc_val, exc_tb)
            )
            return False  # 예외 전파

        return True


def log_function_call(logger: logging.Logger):
    """함수 호출 로깅 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"호출: {func.__name__}(args={args}, kwargs={kwargs})")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"완료: {func.__name__} -> {result}")
                return result
            except Exception as e:
                logger.error(f"오류: {func.__name__} - {e}", exc_info=True)
                raise
        return wrapper
    return decorator


# 사용 예시
if __name__ == '__main__':
    # 일반 로깅
    logger = setup_logger("test_app", json_format=False)
    logger.info("일반 정보 로그")
    logger.warning("경고 로그")
    logger.error("에러 로그")

    # JSON 로깅
    json_logger = setup_logger("test_json", json_format=True, console_output=False)
    json_logger.info("JSON 형식 로그", extra={
        'user_id': 123,
        'stock_code': '005930',
        'action': 'evaluate'
    })

    # 컨텍스트 관리자 사용
    with LogContext(logger, action="test_operation", user_id=456):
        import time
        time.sleep(0.1)
        logger.info("작업 진행 중")

    print("\n✅ 로그 파일 생성 완료")
    print(f"   - logs/test_app.log")
    print(f"   - logs/test_app_error.log")
    print(f"   - logs/test_json.log")
