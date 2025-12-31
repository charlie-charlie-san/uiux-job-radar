"""求人データモデル定義"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class RawJob:
    """スクレイピングで取得した生の求人データ"""

    source: str  # "herp" | "hrmos"
    company_name: str
    job_title: str
    url: str
    posted_date: date | None = None
    description: str = ""
    location: str = ""
    employment_type: str = ""  # 正社員, 契約社員, 業務委託 など
    raw_html: str = ""  # デバッグ用


@dataclass
class NormJob:
    """正規化・スコアリング済みの求人データ"""

    source: str
    company_name: str
    job_title: str
    url: str
    posted_date: date | None = None
    description: str = ""
    location: str = ""
    employment_type: str = ""

    # スコアリング結果
    score: int = 0  # 0-100
    skills: list[str] = field(default_factory=list)  # 抽出されたスキル/キーワード

    @classmethod
    def from_raw(cls, raw: RawJob) -> "NormJob":
        """RawJobからNormJobを生成（スコア・スキルは未設定）"""
        return cls(
            source=raw.source,
            company_name=raw.company_name,
            job_title=raw.job_title,
            url=raw.url,
            posted_date=raw.posted_date,
            description=raw.description,
            location=raw.location,
            employment_type=raw.employment_type,
        )

