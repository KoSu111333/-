# mylogger.py 파일 내용

import logging
from logging.handlers import RotatingFileHandler
import sys
import os

class CustomLogger:
    """
    프로젝트 로깅을 위한 맞춤형 클래스.
    모든 로깅 설정을 중앙에서 관리합니다.
    """
    def __init__(self, name="ProjectLogger", log_dir="logs", log_file="project.log", 
                 level=logging.INFO, max_bytes=10*1024*1024, backup_count=5):
        
        # 1. 로그 디렉토리 생성
        os.makedirs(log_dir, exist_ok=True)
        full_log_path = os.path.join(log_dir, log_file)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 중복 핸들러 방지 (한 번만 설정되도록 보장)
        if not self.logger.handlers:
            # 포맷터: 모든 모듈에 적용될 통일된 형식 정의
            formatter = logging.Formatter(
                '[%(asctime)s] %(name)s (L:%(lineno)d) | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # 콘솔 핸들러
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO) 
            console_handler.setFormatter(formatter)

            # 파일 핸들러 (로테이션 포함)
            file_handler = RotatingFileHandler(
                full_log_path, 
                maxBytes=max_bytes, 
                backupCount=backup_count, 
                encoding='utf-8'
            )
            file_handler.setLevel(level) 
            file_handler.setFormatter(formatter)

            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

    def get_logger(self):
        """설정된 로거 객체를 반환합니다."""
        return self.logger

def setup_root_logger():
    """메인 애플리케이션 시작 시 루트 로거를 설정하고 반환하는 함수"""
    # 프로젝트의 루트 로거 이름을 'MyApp'으로 지정
    log_manager = CustomLogger(name="MyApp", log_file="app.log", level=logging.DEBUG)
    return log_manager.get_logger()

# 초기화된 루트 로거를 미리 준비
ROOT_LOGGER = setup_root_logger()