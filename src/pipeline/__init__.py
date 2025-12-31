"""パイプラインモジュール"""

from .score import calculate_score, extract_matched_skills
from .normalize import normalize, NormalizedResult

# LLMスコアリング（オプション）
try:
    from .llm_score import calculate_llm_score, LLMScoreResult
    __all__ = [
        "calculate_score", "extract_matched_skills",
        "normalize", "NormalizedResult",
        "calculate_llm_score", "LLMScoreResult",
    ]
except ImportError:
    __all__ = [
        "calculate_score", "extract_matched_skills",
        "normalize", "NormalizedResult",
    ]

