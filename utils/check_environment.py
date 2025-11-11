#!/usr/bin/env python3
"""
환경 설정 검증 스크립트

프로덕션 배포 전 필수 설정 및 의존성을 확인합니다.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

# ANSI 색상 코드
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


class EnvironmentChecker:
    """환경 설정 검증 클래스"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success = []
        self.project_root = Path(__file__).parent.parent

    def check_python_version(self) -> bool:
        """Python 버전 확인"""
        print(f"\n{BOLD}1. Python 버전 확인{RESET}")
        version = sys.version_info
        required_version = (3, 10)

        if version >= required_version:
            msg = f"Python {version.major}.{version.minor}.{version.micro}"
            self.success.append(msg)
            print(f"  {GREEN}✓{RESET} {msg}")
            return True
        else:
            msg = f"Python {version.major}.{version.minor} (최소 3.10 이상 필요)"
            self.errors.append(msg)
            print(f"  {RED}✗{RESET} {msg}")
            return False

    def check_required_files(self) -> bool:
        """필수 파일 존재 확인"""
        print(f"\n{BOLD}2. 필수 파일 확인{RESET}")

        required_files = {
            'telegram_ai_bot.py': '텔레그램 AI 봇 메인 파일',
            'report_generator.py': '보고서 생성 모듈',
            'analysis_manager.py': '분석 관리 모듈',
            'requirements.txt': '의존성 목록',
        }

        all_exist = True
        for file, description in required_files.items():
            file_path = self.project_root / file
            if file_path.exists():
                self.success.append(f"{file} ({description})")
                print(f"  {GREEN}✓{RESET} {file}")
            else:
                self.errors.append(f"{file} 없음 - {description}")
                print(f"  {RED}✗{RESET} {file} (없음)")
                all_exist = False

        return all_exist

    def check_config_files(self) -> bool:
        """설정 파일 확인"""
        print(f"\n{BOLD}3. 설정 파일 확인{RESET}")

        config_files = {
            '.env': '환경 변수 설정',
            'mcp_agent.config.yaml': 'MCP 에이전트 설정',
            'mcp_agent.secrets.yaml': 'MCP 시크릿 설정',
        }

        all_exist = True
        for file, description in config_files.items():
            file_path = self.project_root / file
            if file_path.exists():
                self.success.append(f"{file} ({description})")
                print(f"  {GREEN}✓{RESET} {file}")
            else:
                self.warnings.append(f"{file} 없음 - {description}")
                print(f"  {YELLOW}⚠{RESET} {file} (없음, 예시 파일에서 복사 필요)")
                all_exist = False

        return all_exist

    def check_env_variables(self) -> bool:
        """환경 변수 확인"""
        print(f"\n{BOLD}4. 환경 변수 확인{RESET}")

        # .env 파일 로드
        env_file = self.project_root / '.env'
        env_vars = {}

        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

        required_vars = {
            'TELEGRAM_AI_BOT_TOKEN': '텔레그램 AI 봇 토큰',
            'TELEGRAM_CHANNEL_ID': '텔레그램 채널 ID',
        }

        all_set = True
        for var, description in required_vars.items():
            value = env_vars.get(var) or os.environ.get(var)
            if value and value != 'your_bot_token' and value != 'your_channel_id':
                self.success.append(f"{var} 설정됨")
                print(f"  {GREEN}✓{RESET} {var} (설정됨)")
            else:
                self.warnings.append(f"{var} 미설정 - {description}")
                print(f"  {YELLOW}⚠{RESET} {var} (미설정)")
                all_set = False

        return all_set

    def check_directories(self) -> bool:
        """필수 디렉토리 확인 및 생성"""
        print(f"\n{BOLD}5. 필수 디렉토리 확인{RESET}")

        required_dirs = [
            'reports',
            'html_reports',
            'charts',
            'telegram_messages',
        ]

        all_exist = True
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                self.success.append(f"{dir_name}/ 존재")
                print(f"  {GREEN}✓{RESET} {dir_name}/")
            else:
                dir_path.mkdir(exist_ok=True)
                self.warnings.append(f"{dir_name}/ 생성됨")
                print(f"  {YELLOW}⚠{RESET} {dir_name}/ (생성됨)")

        return True

    def check_python_packages(self) -> bool:
        """Python 패키지 설치 확인"""
        print(f"\n{BOLD}6. Python 패키지 확인{RESET}")

        required_packages = {
            'telegram': 'python-telegram-bot',
            'anthropic': 'Anthropic API',
            'mcp_agent': 'MCP Agent',
            'markdown': 'Markdown 변환',
            'apscheduler': 'APScheduler',
        }

        all_installed = True
        for package, description in required_packages.items():
            try:
                __import__(package)
                self.success.append(f"{package} ({description})")
                print(f"  {GREEN}✓{RESET} {package}")
            except ImportError:
                self.errors.append(f"{package} 미설치 - {description}")
                print(f"  {RED}✗{RESET} {package} (미설치)")
                all_installed = False

        return all_installed

    def check_mcp_servers(self) -> bool:
        """MCP 서버 설치 확인"""
        print(f"\n{BOLD}7. MCP 서버 확인{RESET}")

        # perplexity-ask 디렉토리 확인
        perplexity_dir = self.project_root / 'perplexity-ask'
        if perplexity_dir.exists() and (perplexity_dir / 'node_modules').exists():
            self.success.append('perplexity-ask MCP 서버')
            print(f"  {GREEN}✓{RESET} perplexity-ask")
        else:
            self.warnings.append('perplexity-ask MCP 서버 미설치')
            print(f"  {YELLOW}⚠{RESET} perplexity-ask (npm install 필요)")

        return True

    def check_stock_data(self) -> bool:
        """종목 데이터 파일 확인"""
        print(f"\n{BOLD}8. 종목 데이터 파일 확인{RESET}")

        stock_map_file = self.project_root / 'stock_map.json'
        if stock_map_file.exists():
            self.success.append('stock_map.json 존재')
            print(f"  {GREEN}✓{RESET} stock_map.json")
            return True
        else:
            self.warnings.append('stock_map.json 없음')
            print(f"  {YELLOW}⚠{RESET} stock_map.json (없음, update_stock_data.py 실행 필요)")
            return False

    def print_summary(self):
        """검증 결과 요약 출력"""
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}환경 설정 검증 결과 요약{RESET}")
        print(f"{BOLD}{'='*60}{RESET}\n")

        # 성공 항목
        if self.success:
            print(f"{GREEN}✓ 성공 ({len(self.success)}개){RESET}")
            for item in self.success[:5]:  # 처음 5개만 표시
                print(f"  - {item}")
            if len(self.success) > 5:
                print(f"  ... 외 {len(self.success) - 5}개")

        # 경고 항목
        if self.warnings:
            print(f"\n{YELLOW}⚠ 경고 ({len(self.warnings)}개){RESET}")
            for item in self.warnings:
                print(f"  - {item}")

        # 오류 항목
        if self.errors:
            print(f"\n{RED}✗ 오류 ({len(self.errors)}개){RESET}")
            for item in self.errors:
                print(f"  - {item}")

        print(f"\n{BOLD}{'='*60}{RESET}\n")

        # 최종 판정
        if not self.errors:
            if not self.warnings:
                print(f"{GREEN}{BOLD}🎉 모든 검사 통과! 프로덕션 배포 가능합니다.{RESET}\n")
                return 0
            else:
                print(f"{YELLOW}{BOLD}⚠️  경고 사항이 있습니다. 설정 파일을 확인해주세요.{RESET}\n")
                print(f"{BLUE}다음 명령어로 설정 파일을 생성하세요:{RESET}")
                print(f"  cp .env.example .env")
                print(f"  cp mcp_agent.config.yaml.example mcp_agent.config.yaml")
                print(f"  cp mcp_agent.secrets.yaml.example mcp_agent.secrets.yaml\n")
                return 1
        else:
            print(f"{RED}{BOLD}❌ 오류가 발견되었습니다. 수정이 필요합니다.{RESET}\n")
            print(f"{BLUE}다음 명령어로 패키지를 설치하세요:{RESET}")
            print(f"  pip install -r requirements.txt\n")
            return 2

    def run_all_checks(self) -> int:
        """모든 검사 실행"""
        print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
        print(f"{BOLD}{BLUE}PRISM-INSIGHT 환경 설정 검증{RESET}")
        print(f"{BOLD}{BLUE}{'='*60}{RESET}")

        # 모든 검사 실행
        checks = [
            self.check_python_version,
            self.check_required_files,
            self.check_config_files,
            self.check_env_variables,
            self.check_directories,
            self.check_python_packages,
            self.check_mcp_servers,
            self.check_stock_data,
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                self.errors.append(f"검사 중 오류: {str(e)}")
                print(f"  {RED}✗{RESET} 오류 발생: {e}")

        # 결과 요약
        return self.print_summary()


def main():
    """메인 실행 함수"""
    checker = EnvironmentChecker()
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
