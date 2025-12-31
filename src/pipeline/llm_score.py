"""LLMを使った高度なスコアリング"""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Anthropic SDK
try:
    import anthropic
except ImportError:
    anthropic = None

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import RawJob

# ============================================================
# 設定
# ============================================================

# 環境変数またはデフォルト
MODEL_NAME = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
MAX_TOKENS = 500

# プロンプトテンプレート
SCORING_PROMPT = """あなたはUI/UXデザイナーの派遣・業務委託ビジネスの営業支援AIです。
以下の求人情報を分析し、「派遣/業務委託として提案しやすい案件か」を評価してください。

## 求人情報
- 企業名: {company_name}
- 職種: {job_title}
- 雇用形態: {employment_type}
- 勤務地: {location}
- 説明: {description}

## 評価基準
1. **派遣向き度** (0-100): 業務委託・派遣で対応しやすい案件か
   - 高: 即戦力希望、プロジェクト単位、リモートOK、スポット対応可
   - 低: 正社員のみ、長期コミット必須、社内文化重視

2. **緊急度** (0-100): 今すぐ人材が欲しそうか
   - 高: 急募、増員、事業拡大、新規プロジェクト立ち上げ
   - 低: 将来的な採用、ポジション準備中

3. **スキルマッチ度** (0-100): UI/UXデザイナーとしての純度
   - 高: Figma、プロダクトデザイン、UXリサーチ中心
   - 低: グラフィック、バナー、コーディング寄り

## 出力形式（JSON）
```json
{{
  "dispatch_score": <0-100>,
  "urgency_score": <0-100>,
  "skill_match_score": <0-100>,
  "total_score": <0-100>,
  "reason": "<1-2文の日本語で理由>",
  "tags": ["<該当するタグ>"]
}}
```

タグ候補: "即戦力", "リモートOK", "スポット可", "急募", "Figma必須", "デザインシステム", "UXリサーチ", "正社員のみ", "グラフィック寄り", "実装寄り"

JSONのみを出力してください。"""


# ============================================================
# データクラス
# ============================================================

@dataclass
class LLMScoreResult:
    """LLMスコアリング結果"""
    dispatch_score: int  # 派遣向き度
    urgency_score: int  # 緊急度
    skill_match_score: int  # スキルマッチ度
    total_score: int  # 総合スコア
    reason: str  # 理由
    tags: list[str]  # タグ
    raw_response: str = ""  # デバッグ用


# ============================================================
# スコアリング関数
# ============================================================

def _parse_llm_response(response_text: str) -> dict:
    """LLMのレスポンスからJSONを抽出・パース"""
    # コードブロックを除去
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # 最初と最後の```を除去
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # フォールバック: デフォルト値
        return {
            "dispatch_score": 50,
            "urgency_score": 50,
            "skill_match_score": 50,
            "total_score": 50,
            "reason": "解析エラー",
            "tags": [],
        }


def calculate_llm_score(job: RawJob, client: "anthropic.Anthropic | None" = None) -> LLMScoreResult:
    """
    LLMを使って求人をスコアリング
    
    Args:
        job: 求人データ
        client: Anthropicクライアント（省略時は新規作成）
    
    Returns:
        LLMScoreResult
    """
    if anthropic is None:
        raise ImportError("anthropic パッケージがインストールされていません: pip install anthropic")
    
    if client is None:
        client = anthropic.Anthropic()  # 環境変数 ANTHROPIC_API_KEY を使用
    
    # プロンプト生成
    prompt = SCORING_PROMPT.format(
        company_name=job.company_name,
        job_title=job.job_title,
        employment_type=job.employment_type or "不明",
        location=job.location or "不明",
        description=job.description[:1000] if job.description else "説明なし",
    )
    
    # API呼び出し
    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    parsed = _parse_llm_response(response_text)
    
    return LLMScoreResult(
        dispatch_score=parsed.get("dispatch_score", 50),
        urgency_score=parsed.get("urgency_score", 50),
        skill_match_score=parsed.get("skill_match_score", 50),
        total_score=parsed.get("total_score", 50),
        reason=parsed.get("reason", ""),
        tags=parsed.get("tags", []),
        raw_response=response_text,
    )


def calculate_llm_score_batch(
    jobs: list[RawJob],
    limit: int | None = None,
    verbose: bool = True,
) -> list[tuple[RawJob, LLMScoreResult]]:
    """
    複数求人を一括スコアリング
    
    Args:
        jobs: 求人リスト
        limit: 処理件数上限（API節約用）
        verbose: 進捗表示
    
    Returns:
        (RawJob, LLMScoreResult) のリスト
    """
    if anthropic is None:
        raise ImportError("anthropic パッケージがインストールされていません: pip install anthropic")
    
    client = anthropic.Anthropic()
    results = []
    
    target_jobs = jobs[:limit] if limit else jobs
    
    for i, job in enumerate(target_jobs):
        if verbose:
            print(f"  [{i+1}/{len(target_jobs)}] {job.company_name} - {job.job_title}...", end=" ")
        
        try:
            result = calculate_llm_score(job, client)
            results.append((job, result))
            if verbose:
                print(f"✓ スコア: {result.total_score}")
        except Exception as e:
            if verbose:
                print(f"✗ エラー: {e}")
            # エラー時はデフォルト値
            results.append((job, LLMScoreResult(
                dispatch_score=0,
                urgency_score=0,
                skill_match_score=0,
                total_score=0,
                reason=f"APIエラー: {e}",
                tags=[],
            )))
    
    return results


# ============================================================
# テスト用
# ============================================================

if __name__ == "__main__":
    from dotenv import load_dotenv
    
    # .envから環境変数読み込み
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    
    # テスト求人
    test_job = RawJob(
        source="herp",
        company_name="株式会社SmartHR",
        job_title="UI/UXデザイナー（業務委託）",
        url="https://example.com/1",
        description="""
        【募集背景】プロダクト拡大に伴い、デザインチームを増員します。
        
        【業務内容】
        - Figmaを使ったUIデザイン
        - デザインシステムの構築・運用
        - UXリサーチ、ユーザーインタビュー
        
        【必須スキル】
        - Figmaでのデザイン経験3年以上
        - toBプロダクトのデザイン経験
        
        【働き方】フルリモート可、週4日〜相談可
        """,
        location="フルリモート",
        employment_type="業務委託",
    )
    
    print("=== LLMスコアリングテスト ===\n")
    print(f"求人: {test_job.company_name} - {test_job.job_title}\n")
    
    try:
        result = calculate_llm_score(test_job)
        print(f"派遣向き度: {result.dispatch_score}")
        print(f"緊急度: {result.urgency_score}")
        print(f"スキルマッチ度: {result.skill_match_score}")
        print(f"総合スコア: {result.total_score}")
        print(f"理由: {result.reason}")
        print(f"タグ: {result.tags}")
    except Exception as e:
        print(f"エラー: {e}")

