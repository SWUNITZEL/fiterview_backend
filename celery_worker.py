#!/usr/bin/env python3
"""
Celery 워커 실행 스크립트
"""
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.celery_app import celery_app

if __name__ == '__main__':
    celery_app.start()
