#!/usr/bin/env python3
"""
UI/UX求人レーダー CLI

ダミーデータ → 正規化 → スコア付与 を1コマンドで実行
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# .envファイルから環境変数を読み込み
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from src.models import RawJob, NormJob
from src.pipeline.score import calculate_score, extract_matched_skills
from src.pipeline.normalize import normalize, NormalizedResult

# デフォルトパス
DEFAULT_INPUT = PROJECT_ROOT / "data" / "out" / "jobs_raw.jsonl"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "out" / "jobs_norm.jsonl"

# LLMスコアリング（オプション）
LLM_AVAILABLE = False
try:
    from src.pipeline.llm_score import calculate_llm_score, LLMScoreResult
    import anthropic
    LLM_AVAILABLE = True
except ImportError:
    pass


def load_raw_jobs(input_path: Path) -> list[RawJob]:
    """JSONLファイルからRawJobリストを読み込み"""
    jobs = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
                # JSONからRawJobへマッピング
                posted_date = None
                if data.get("posted_or_updated_at"):
                    try:
                        posted_date = date.fromisoformat(data["posted_or_updated_at"])
                    except ValueError:
                        pass

                raw_job = RawJob(
                    source=data.get("source", "unknown"),
                    company_name=data.get("company_name", ""),
                    job_title=data.get("job_title", ""),
                    url=data.get("url", ""),
                    posted_date=posted_date,
                    description=data.get("description", ""),
                    location=data.get("location", ""),
                    employment_type=data.get("employment_type", ""),
                    raw_html="",
                )
                jobs.append(raw_job)

            except json.JSONDecodeError as e:
                print(f"⚠️  行{line_num}: JSONパースエラー - {e}", file=sys.stderr)

    return jobs


def process_jobs(raw_jobs: list[RawJob], use_llm: bool = False, llm_limit: int | None = None) -> list[dict]:
    """RawJobリストを処理してスコア付き正規化データを生成"""
    results = []
    
    # LLM使用時はクライアントを事前に作成
    llm_client = None
    if use_llm and LLM_AVAILABLE:
        try:
            llm_client = anthropic.Anthropic()
        except Exception as e:
            print(f"⚠️  LLMクライアント初期化エラー: {e}", file=sys.stderr)
            use_llm = False

    for i, raw in enumerate(raw_jobs):
        # 1. ルールベーススコア計算
        rule_score = calculate_score(raw)

        # 2. 正規化
        norm_result = normalize(raw, rule_score)

        # 3. LLMスコアリング（オプション）
        llm_result = None
        if use_llm and llm_client and (llm_limit is None or i < llm_limit):
            try:
                print(f"  🤖 LLM分析中: {raw.company_name[:20]}...", end=" ", flush=True)
                llm_result = calculate_llm_score(raw, llm_client)
                print(f"✓ {llm_result.total_score}点")
            except Exception as e:
                print(f"✗ {e}")

        # 4. 出力用dictに変換
        output = {
            "source": norm_result.norm_job.source,
            "company_name": norm_result.norm_job.company_name,
            "job_title": norm_result.norm_job.job_title,
            "url": norm_result.norm_job.url,
            "posted_date": norm_result.norm_job.posted_date.isoformat() if norm_result.norm_job.posted_date else None,
            "description": norm_result.norm_job.description,
            "location": norm_result.norm_job.location,
            "employment_type": norm_result.norm_job.employment_type,
            "score": norm_result.norm_job.score,
            "skills": norm_result.norm_job.skills,
            "category": norm_result.category,
            "remote_type": norm_result.remote_type,
            "comp_min": norm_result.comp_min,
            "comp_max": norm_result.comp_max,
        }
        
        # LLM結果を追加
        if llm_result:
            output["llm_score"] = llm_result.total_score
            output["llm_dispatch_score"] = llm_result.dispatch_score
            output["llm_urgency_score"] = llm_result.urgency_score
            output["llm_skill_match_score"] = llm_result.skill_match_score
            output["llm_reason"] = llm_result.reason
            output["llm_tags"] = llm_result.tags
            # 総合スコアをLLMスコアで上書き（または加重平均）
            output["score"] = llm_result.total_score
        
        results.append(output)

    return results


def save_results(results: list[dict], output_path: Path) -> None:
    """結果をJSONLファイルに保存"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")


def print_summary(results: list[dict]) -> None:
    """処理結果のサマリーを表示"""
    total = len(results)
    if total == 0:
        print("⚠️  処理対象の求人がありません")
        return

    # スコア統計
    scores = [r["score"] for r in results]
    avg_score = sum(scores) / total
    max_score = max(scores)
    min_score = min(scores)

    # カテゴリ別集計
    category_counts = {}
    for r in results:
        cat = r["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Top5表示
    top5 = sorted(results, key=lambda x: x["score"], reverse=True)[:5]

    print("\n" + "=" * 50)
    print("📊 処理結果サマリー")
    print("=" * 50)
    print(f"総件数: {total}件")
    print(f"スコア: 平均 {avg_score:.1f} / 最高 {max_score} / 最低 {min_score}")
    print()
    print("📁 カテゴリ別:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {count}件 ({count/total*100:.0f}%)")

    print()
    print("🏆 Top 5:")
    for i, job in enumerate(top5, 1):
        print(f"   {i}. [{job['score']}点] {job['company_name']} - {job['job_title']}")

    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="UI/UX求人レーダー: ダミーデータ → 正規化 → スコア付与"
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"入力JSONLファイル (default: {DEFAULT_INPUT})"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"出力JSONLファイル (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        help="上位N件のみ出力（指定しない場合は全件）"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="サマリー表示を抑制"
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="LLMスコアリングを有効化（ANTHROPIC_API_KEY環境変数が必要）"
    )
    parser.add_argument(
        "--llm-limit",
        type=int,
        default=20,
        help="LLMスコアリングの最大件数（API節約用、default: 20）"
    )

    args = parser.parse_args()

    # 入力ファイル確認
    if not args.input.exists():
        print(f"❌ 入力ファイルが見つかりません: {args.input}", file=sys.stderr)
        print("   先に scripts/generate_dummy.py を実行してください", file=sys.stderr)
        sys.exit(1)

    # LLM使用確認
    use_llm = args.llm
    if use_llm:
        if not LLM_AVAILABLE:
            print("⚠️  LLMスコアリングを使用するには anthropic パッケージが必要です")
            print("   pip install anthropic")
            use_llm = False
        elif not os.getenv("ANTHROPIC_API_KEY"):
            print("⚠️  ANTHROPIC_API_KEY 環境変数が設定されていません")
            use_llm = False
        else:
            print(f"🤖 LLMスコアリング有効（上限: {args.llm_limit}件）")

    # 処理実行
    print(f"📥 読み込み中: {args.input}")
    raw_jobs = load_raw_jobs(args.input)
    print(f"   {len(raw_jobs)}件の求人を読み込みました")

    print("⚙️  スコアリング・正規化中...")
    results = process_jobs(raw_jobs, use_llm=use_llm, llm_limit=args.llm_limit)

    # スコア順にソート
    results.sort(key=lambda x: x["score"], reverse=True)

    # 上位N件に絞る
    if args.top:
        results = results[:args.top]
        print(f"   上位{args.top}件に絞り込みました")

    # 保存
    save_results(results, args.output)
    print(f"📤 保存完了: {args.output}")

    # サマリー
    if not args.quiet:
        print_summary(results)


if __name__ == "__main__":
    main()

