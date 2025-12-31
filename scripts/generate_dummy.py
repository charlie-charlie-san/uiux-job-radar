#!/usr/bin/env python3
"""ダミー求人データ生成スクリプト"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

# === 設定 ===
NUM_JOBS = 100
UIUX_RATIO = 0.6  # UI/UX求人の割合
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "out" / "jobs_raw.jsonl"

# === マスターデータ ===

COMPANIES = [
    "株式会社メルカリ",
    "株式会社サイバーエージェント",
    "LINE株式会社",
    "株式会社ディー・エヌ・エー",
    "株式会社リクルート",
    "株式会社SmartHR",
    "株式会社LayerX",
    "株式会社UPSIDER",
    "Sansan株式会社",
    "freee株式会社",
    "株式会社マネーフォワード",
    "株式会社プレイド",
    "株式会社Speee",
    "株式会社ビズリーチ",
    "株式会社ラクス",
    "株式会社ヤプリ",
    "株式会社カミナシ",
    "株式会社estie",
    "株式会社タイミー",
    "株式会社10X",
    "STORES株式会社",
    "note株式会社",
    "株式会社Luup",
    "株式会社アンドパッド",
    "株式会社hacomono",
]

# 直近30日以内に多く求人を出す「増加カテゴリ」企業
HOT_COMPANIES = [
    "株式会社SmartHR",
    "株式会社LayerX",
    "株式会社タイミー",
    "株式会社10X",
    "株式会社hacomono",
]

# UI/UX系職種
UIUX_JOB_TITLES = [
    "UIデザイナー",
    "UXデザイナー",
    "UI/UXデザイナー",
    "プロダクトデザイナー",
    "シニアUIデザイナー",
    "シニアUXデザイナー",
    "リードプロダクトデザイナー",
    "UXリサーチャー",
    "デザインマネージャー",
    "デザインシステムエンジニア",
]

# 非UI/UX職種
OTHER_JOB_TITLES = [
    "フロントエンドエンジニア",
    "バックエンドエンジニア",
    "SRE",
    "データエンジニア",
    "プロダクトマネージャー",
    "カスタマーサクセス",
    "セールス",
    "マーケティング担当",
    "経理担当",
    "人事担当",
]

# スキル/ツール（出現確率付き）
SKILLS_PROBABILITY = {
    # UI/UX系: (確率, UI/UX求人のみか)
    "Figma": (0.85, True),
    "Adobe XD": (0.30, True),
    "Sketch": (0.20, True),
    "デザインシステム": (0.35, True),
    "UXリサーチ": (0.25, True),
    "ユーザーインタビュー": (0.20, True),
    "プロトタイピング": (0.50, True),
    "Webデザイン": (0.40, True),
    "モバイルアプリデザイン": (0.35, True),
    # 汎用系
    "HTML/CSS": (0.40, False),
    "JavaScript": (0.35, False),
    "React": (0.30, False),
    "TypeScript": (0.25, False),
}

REMOTE_TYPES = ["full_remote", "hybrid", "office"]
REMOTE_WEIGHTS = [0.35, 0.45, 0.20]

EMPLOYMENT_TYPES = ["正社員", "契約社員", "業務委託"]
EMPLOYMENT_WEIGHTS = [0.70, 0.15, 0.15]

LOCATIONS = [
    "東京都渋谷区",
    "東京都港区",
    "東京都千代田区",
    "東京都新宿区",
    "東京都品川区",
    "大阪府大阪市",
    "福岡県福岡市",
    "フルリモート",
]

SOURCES = ["herp", "hrmos"]


def random_date(is_hot_company: bool) -> str:
    """日付を生成。HOT企業は直近30日寄り"""
    today = date.today()
    if is_hot_company:
        # 直近30日以内（70%が直近14日）
        if random.random() < 0.7:
            days_ago = random.randint(0, 14)
        else:
            days_ago = random.randint(15, 30)
    else:
        # 通常: 0〜90日前
        days_ago = random.randint(0, 90)

    return (today - timedelta(days=days_ago)).isoformat()


def random_compensation() -> tuple[int | None, int | None]:
    """年収範囲を生成（万円単位）"""
    if random.random() < 0.15:
        return None, None  # 非公開

    base = random.choice([400, 450, 500, 550, 600, 650, 700, 800, 900, 1000])
    comp_min = base
    comp_max = base + random.choice([100, 150, 200, 300, 400])
    return comp_min, comp_max


def generate_skills(is_uiux: bool) -> list[str]:
    """スキルリストを生成"""
    skills = []
    for skill, (prob, uiux_only) in SKILLS_PROBABILITY.items():
        if uiux_only and not is_uiux:
            continue
        if random.random() < prob:
            skills.append(skill)
    return skills


def generate_description(job_title: str, skills: list[str]) -> str:
    """簡易的な求人説明文を生成"""
    skill_text = "、".join(skills[:3]) if skills else "各種ツール"
    return f"{job_title}として、{skill_text}を活用したプロダクト開発に携わっていただきます。"


def generate_job(job_id: int) -> dict:
    """1件の求人データを生成"""
    is_uiux = random.random() < UIUX_RATIO
    company = random.choice(COMPANIES)
    is_hot = company in HOT_COMPANIES

    job_title = random.choice(UIUX_JOB_TITLES if is_uiux else OTHER_JOB_TITLES)
    skills = generate_skills(is_uiux)
    comp_min, comp_max = random_compensation()

    return {
        "id": f"job_{job_id:04d}",
        "source": random.choice(SOURCES),
        "company_name": company,
        "job_title": job_title,
        "url": f"https://example.com/jobs/{job_id}",
        "posted_or_updated_at": random_date(is_hot),
        "description": generate_description(job_title, skills),
        "location": random.choice(LOCATIONS),
        "remote_type": random.choices(REMOTE_TYPES, weights=REMOTE_WEIGHTS)[0],
        "employment_type": random.choices(EMPLOYMENT_TYPES, weights=EMPLOYMENT_WEIGHTS)[0],
        "comp_min": comp_min,
        "comp_max": comp_max,
        "skills": skills,
    }


def main():
    """メイン処理"""
    random.seed(42)  # 再現性のため固定シード

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    jobs = [generate_job(i) for i in range(NUM_JOBS)]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for job in jobs:
            f.write(json.dumps(job, ensure_ascii=False) + "\n")

    print(f"✅ {len(jobs)}件の求人データを生成しました")
    print(f"   出力先: {OUTPUT_PATH}")

    # 統計表示
    uiux_count = sum(
        1
        for j in jobs
        if any(kw in j["job_title"] for kw in ["UI", "UX", "デザイナー", "デザイン"])
    )
    hot_count = sum(1 for j in jobs if j["company_name"] in HOT_COMPANIES)
    recent_count = sum(
        1 for j in jobs if (date.today() - date.fromisoformat(j["posted_or_updated_at"])).days <= 14
    )

    print(f"\n📊 統計:")
    print(f"   UI/UX系求人: {uiux_count}件 ({uiux_count/len(jobs)*100:.0f}%)")
    print(f"   HOT企業の求人: {hot_count}件")
    print(f"   直近14日以内: {recent_count}件")


if __name__ == "__main__":
    main()

