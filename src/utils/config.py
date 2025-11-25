"""
설정 파일 로더
YAML 설정 파일 로드 및 관리
"""

import yaml
import os
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    YAML 설정 파일 로드
    
    Args:
        config_path: 설정 파일 경로
        
    Returns:
        설정 딕셔너리
    """
    try:
        # 절대 경로 또는 프로젝트 루트 기준 경로 처리
        if not os.path.isabs(config_path):
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "configs" / config_path
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded config from: {config_path}")
        return config or {}
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return {}
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

