"""UI/UXマッチ度スコアリング"""

import re
import sys
from pathlib import Path

# src/models.py をインポートできるようにパス追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import RawJob

# ============================================================
# スコアリング重み定数（調整用）
# ============================================================

# --- 加点: 職種キーワード ---
TITLE_POSITIVE_KEYWORDS: dict[str, int] = {
    "UIデザイナー": 30,
    "UXデザイナー": 30,
    "UI/UXデザイナー": 35,
    "プロダクトデザイナー": 30,
    "UXリサーチャー": 25,
    "デザインマネージャー": 20,
    "デザインリード": 20,
    "シニアデザイナー": 15,
    "デザイナー": 10,  # 汎用（他にマッチしない場合）
}

# --- 加点: スキル/ツールキーワード（description内） ---
SKILL_POSITIVE_KEYWORDS: dict[str, int] = {
    "Figma": 15,
    "デザインシステム": 12,
    "UXリサーチ": 10,
    "ユーザーインタビュー": 8,
    "プロトタイピング": 8,
    "ユーザビリティ": 8,
    "ペルソナ": 5,
    "カスタマージャーニー": 5,
    "Adobe XD": 5,
    "Sketch": 5,
    "InVision": 3,
    "Zeplin": 3,
}

# --- 加点: 雇用形態 ---
EMPLOYMENT_TYPE_SCORES: dict[str, int] = {
    "業務委託": 10,
    "契約社員": 5,
    "正社員": 0,
}

# --- 加点: リモート ---
REMOTE_POSITIVE_KEYWORDS: list[tuple[str, int]] = [
    ("フルリモート", 8),
    ("full_remote", 8),
    ("リモート可", 5),
    ("hybrid", 3),
    ("在宅勤務", 3),
]

# --- 減点: 非UI/UX寄りキーワード ---
NEGATIVE_KEYWORDS: dict[str, int] = {
    # 広告/グラフィック系
    "バナー": -15,
    "広告デザイン": -15,
    "グラフィックデザイナー": -12,
    "DTP": -10,
    "印刷": -8,
    "チラシ": -8,
    "LP制作": -5,
    # 実装寄り
    "TypeScript": -5,
    "フロントエンド実装": -5,
    "コーディング": -5,
    "マークアップ": -3,
}

# スコア上下限
SCORE_MIN = 0
SCORE_MAX = 100

# ベーススコア（全求人の出発点）
BASE_SCORE = 20


# ============================================================
# スコアリング関数
# ============================================================


def _match_keywords(text: str, keywords: dict[str, int]) -> int:
    """テキスト内のキーワードマッチで得点を計算"""
    score = 0
    text_lower = text.lower()
    matched = set()

    for keyword, points in keywords.items():
        # 大文字小文字無視でマッチ
        if keyword.lower() in text_lower and keyword not in matched:
            score += points
            matched.add(keyword)

    return score


def _check_remote(location: str, description: str) -> int:
    """リモート関連の加点を計算"""
    score = 0
    combined = f"{location} {description}".lower()

    for keyword, points in REMOTE_POSITIVE_KEYWORDS:
        if keyword.lower() in combined:
            score += points
            break  # 最初にマッチしたもののみ

    return score


def _check_employment_type(employment_type: str) -> int:
    """雇用形態による加点"""
    for emp_type, points in EMPLOYMENT_TYPE_SCORES.items():
        if emp_type in employment_type:
            return points
    return 0


def calculate_score(job: RawJob) -> int:
    """
    RawJobからUI/UXマッチ度スコア（0-100）を算出

    Args:
        job: スクレイピングで取得した生の求人データ

    Returns:
        0〜100のスコア（高いほどUI/UX案件として魅力的）
    """
    score = BASE_SCORE

    # 1. 職種タイトルによる加点
    score += _match_keywords(job.job_title, TITLE_POSITIVE_KEYWORDS)

    # 2. スキル/ツールキーワードによる加点
    combined_text = f"{job.job_title} {job.description}"
    score += _match_keywords(combined_text, SKILL_POSITIVE_KEYWORDS)

    # 3. 雇用形態による加点
    score += _check_employment_type(job.employment_type)

    # 4. リモートによる加点
    score += _check_remote(job.location, job.description)

    # 5. 減点キーワード
    score += _match_keywords(combined_text, NEGATIVE_KEYWORDS)  # 負の値が返る

    # 範囲クリップ
    return max(SCORE_MIN, min(SCORE_MAX, score))


def extract_matched_skills(job: RawJob) -> list[str]:
    """
    求人からマッチしたスキルキーワードを抽出

    Args:
        job: 求人データ

    Returns:
        マッチしたスキルキーワードのリスト
    """
    combined_text = f"{job.job_title} {job.description}".lower()
    matched = []

    for keyword in SKILL_POSITIVE_KEYWORDS:
        if keyword.lower() in combined_text:
            matched.append(keyword)

    return matched


# ============================================================
# テスト用
# ============================================================

if __name__ == "__main__":
    # 簡易テスト
    test_jobs = [
        RawJob(
            source="herp",
            company_name="株式会社テスト",
            job_title="UI/UXデザイナー",
            url="https://example.com/1",
            description="Figmaを使ったデザインシステムの構築",
            location="フルリモート",
            employment_type="業務委託",
        ),
        RawJob(
            source="hrmos",
            company_name="株式会社テスト2",
            job_title="グラフィックデザイナー",
            url="https://example.com/2",
            description="バナー広告の制作",
            location="東京都渋谷区",
            employment_type="正社員",
        ),
        RawJob(
            source="herp",
            company_name="株式会社テスト3",
            job_title="フロントエンドエンジニア",
            url="https://example.com/3",
            description="TypeScriptでのUI実装",
            location="hybrid",
            employment_type="正社員",
        ),
    ]

    print("=== スコアリングテスト ===\n")
    for job in test_jobs:
        score = calculate_score(job)
        skills = extract_matched_skills(job)
        print(f"職種: {job.job_title}")
        print(f"  スコア: {score}")
        print(f"  スキル: {skills}")
        print()

