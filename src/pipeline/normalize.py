"""求人データ正規化処理"""

import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import RawJob, NormJob

# ============================================================
# 定数定義（調整用）
# ============================================================

# --- スキル辞書（正規化名: [表記ゆれパターン]) ---
SKILL_DICTIONARY: dict[str, list[str]] = {
    "Figma": ["figma", "フィグマ"],
    "Adobe XD": ["adobe xd", "adobexd", "xd"],
    "Sketch": ["sketch", "スケッチ"],
    "デザインシステム": ["デザインシステム", "design system", "designsystem"],
    "UXリサーチ": ["uxリサーチ", "ux research", "uxresearch", "ユーザーリサーチ"],
    "ユーザーインタビュー": ["ユーザーインタビュー", "user interview", "ユーザインタビュー"],
    "プロトタイピング": ["プロトタイピング", "prototyping", "プロトタイプ"],
    "ユーザビリティテスト": ["ユーザビリティテスト", "usability test", "ユーザビリティ"],
    "ペルソナ": ["ペルソナ", "persona"],
    "カスタマージャーニー": ["カスタマージャーニー", "customer journey", "ジャーニーマップ"],
    "Webデザイン": ["webデザイン", "ウェブデザイン", "web design"],
    "モバイルアプリデザイン": ["アプリデザイン", "モバイルデザイン", "app design", "ios design", "android design"],
    "InVision": ["invision", "インビジョン"],
    "Zeplin": ["zeplin", "ゼプリン"],
    "Photoshop": ["photoshop", "フォトショップ", "フォトショ"],
    "Illustrator": ["illustrator", "イラストレーター", "イラレ"],
}

# --- 雇用形態マッピング ---
EMPLOYMENT_TYPE_PATTERNS: dict[str, list[str]] = {
    "正社員": ["正社員", "正規雇用", "permanent"],
    "契約社員": ["契約社員", "有期雇用", "contract"],
    "業務委託": ["業務委託", "フリーランス", "freelance", "委託"],
    "派遣": ["派遣", "派遣社員"],
    "アルバイト": ["アルバイト", "パート", "part-time"],
    "インターン": ["インターン", "intern"],
}

# --- リモートタイプマッピング ---
REMOTE_TYPE_PATTERNS: dict[str, list[str]] = {
    "full_remote": ["フルリモート", "full remote", "fullremote", "完全リモート", "full_remote"],
    "hybrid": ["ハイブリッド", "hybrid", "週2出社", "週3出社", "リモート併用", "一部リモート"],
    "remote_ok": ["リモート可", "リモートワーク可", "在宅勤務可", "テレワーク可"],
    "office": ["出社", "オフィス勤務", "常駐", "オンサイト"],
}

# --- カテゴリ判定キーワード ---
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "uiux": [
        "uiデザイナー", "uxデザイナー", "ui/uxデザイナー", "プロダクトデザイナー",
        "uxリサーチャー", "デザインマネージャー", "uiux", "ui/ux",
    ],
    "graphic": [
        "グラフィックデザイナー", "グラフィック", "バナー", "広告デザイン",
        "dtp", "印刷", "チラシ", "ポスター", "パッケージデザイン",
    ],
    "frontend_like": [
        "フロントエンド", "frontend", "マークアップ", "コーダー",
        "html/css", "webコーダー", "uiエンジニア",
    ],
}

# --- 年収抽出パターン ---
COMP_PATTERNS = [
    # 年収600万〜900万、年収600〜900万円
    r"年収\s*(\d{3,4})\s*万?\s*[〜~～ー−-]\s*(\d{3,4})\s*万",
    # 600万円〜900万円
    r"(\d{3,4})\s*万円?\s*[〜~～ー−-]\s*(\d{3,4})\s*万円?",
    # 月収50万〜80万 → 年収換算
    r"月収?\s*(\d{2,3})\s*万?\s*[〜~～ー−-]\s*(\d{2,3})\s*万",
]


# ============================================================
# 正規化結果（NormJob + 追加フィールド）
# ============================================================

@dataclass
class NormalizedResult:
    """正規化結果（NormJob + 追加情報）"""

    norm_job: NormJob
    category: str  # "uiux" | "graphic" | "frontend_like" | "other"
    remote_type: str  # "full_remote" | "hybrid" | "remote_ok" | "office" | "unknown"
    comp_min: int | None  # 年収下限（万円）
    comp_max: int | None  # 年収上限（万円）


# ============================================================
# 正規化関数
# ============================================================

def _extract_skills(text: str) -> list[str]:
    """テキストからスキルを抽出（表記ゆれ対応）"""
    text_lower = text.lower()
    matched_skills = []

    for skill_name, patterns in SKILL_DICTIONARY.items():
        for pattern in patterns:
            if pattern.lower() in text_lower:
                if skill_name not in matched_skills:
                    matched_skills.append(skill_name)
                break

    return matched_skills


def _infer_employment_type(raw_type: str, description: str) -> str:
    """雇用形態を推定"""
    combined = f"{raw_type} {description}".lower()

    for emp_type, patterns in EMPLOYMENT_TYPE_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in combined:
                return emp_type

    return raw_type if raw_type else "不明"


def _infer_remote_type(location: str, description: str) -> str:
    """リモートタイプを推定"""
    combined = f"{location} {description}".lower()

    for remote_type, patterns in REMOTE_TYPE_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in combined:
                return remote_type

    return "unknown"


def _infer_category(job_title: str, description: str) -> str:
    """カテゴリを推定（uiux/graphic/frontend_like/other）"""
    combined = f"{job_title} {description}".lower()

    # 優先順位: uiux > graphic > frontend_like > other
    for category in ["uiux", "graphic", "frontend_like"]:
        keywords = CATEGORY_KEYWORDS[category]
        for keyword in keywords:
            if keyword.lower() in combined:
                return category

    return "other"


def _extract_compensation(description: str) -> tuple[int | None, int | None]:
    """年収範囲を抽出（万円単位）"""
    for pattern in COMP_PATTERNS:
        match = re.search(pattern, description)
        if match:
            min_val = int(match.group(1))
            max_val = int(match.group(2))

            # 月収の場合は年収に換算（×12）
            if "月収" in pattern or "月" in pattern:
                min_val *= 12
                max_val *= 12

            # 妥当性チェック（100万〜3000万の範囲）
            if 100 <= min_val <= 3000 and 100 <= max_val <= 3000:
                return min_val, max_val

    return None, None


def normalize(raw: RawJob, score: int) -> NormalizedResult:
    """
    RawJobを正規化してNormalizedResultを生成

    Args:
        raw: 生の求人データ
        score: スコアリング結果（0-100）

    Returns:
        正規化結果（NormJob + 追加情報）
    """
    combined_text = f"{raw.job_title} {raw.description}"

    # スキル抽出
    skills = _extract_skills(combined_text)

    # NormJob生成
    norm_job = NormJob(
        source=raw.source,
        company_name=raw.company_name.strip(),
        job_title=raw.job_title.strip(),
        url=raw.url.strip(),
        posted_date=raw.posted_date,
        description=raw.description.strip(),
        location=raw.location.strip(),
        employment_type=_infer_employment_type(raw.employment_type, raw.description),
        score=score,
        skills=skills,
    )

    # 追加情報
    category = _infer_category(raw.job_title, raw.description)
    remote_type = _infer_remote_type(raw.location, raw.description)
    comp_min, comp_max = _extract_compensation(raw.description)

    return NormalizedResult(
        norm_job=norm_job,
        category=category,
        remote_type=remote_type,
        comp_min=comp_min,
        comp_max=comp_max,
    )


# ============================================================
# テスト用
# ============================================================

if __name__ == "__main__":
    test_jobs = [
        RawJob(
            source="herp",
            company_name="株式会社テスト",
            job_title="UI/UXデザイナー",
            url="https://example.com/1",
            description="Figmaを使ったデザインシステムの構築。年収600万〜900万円。フルリモート可。",
            location="東京都渋谷区",
            employment_type="業務委託",
        ),
        RawJob(
            source="hrmos",
            company_name="株式会社テスト2",
            job_title="グラフィックデザイナー",
            url="https://example.com/2",
            description="バナー広告の制作。Photoshop、Illustrator必須。",
            location="東京都港区",
            employment_type="正社員",
        ),
        RawJob(
            source="herp",
            company_name="株式会社テスト3",
            job_title="フロントエンドエンジニア",
            url="https://example.com/3",
            description="React/TypeScriptでのUI実装。週2出社のハイブリッド勤務。",
            location="",
            employment_type="",
        ),
    ]

    print("=== 正規化テスト ===\n")
    for i, raw in enumerate(test_jobs):
        result = normalize(raw, score=50 + i * 10)
        print(f"[{i+1}] {raw.job_title}")
        print(f"    カテゴリ: {result.category}")
        print(f"    リモート: {result.remote_type}")
        print(f"    雇用形態: {result.norm_job.employment_type}")
        print(f"    年収: {result.comp_min}万〜{result.comp_max}万")
        print(f"    スキル: {result.norm_job.skills}")
        print(f"    スコア: {result.norm_job.score}")
        print()

