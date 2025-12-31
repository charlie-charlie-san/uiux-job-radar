#!/usr/bin/env python3
"""
毎朝定時レポート生成スクリプト

新着求人Top N件をSlack通知またはファイル出力
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# HTTPリクエスト用
import urllib.request
import urllib.error

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models import RawJob

# ============================================================
# 設定
# ============================================================

DEFAULT_TOP_N = 10
DEFAULT_DAYS = 7  # 直近N日を「新着」とみなす
DATA_PATH = PROJECT_ROOT / "data" / "out" / "jobs_norm.jsonl"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"

# Slack Webhook URL（環境変数から取得）
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


# ============================================================
# データ読み込み
# ============================================================

def load_jobs(data_path: Path) -> list[dict]:
    """正規化済み求人データを読み込み"""
    if not data_path.exists():
        return []
    
    jobs = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                jobs.append(json.loads(line))
    return jobs


def filter_recent_jobs(jobs: list[dict], days: int = DEFAULT_DAYS) -> list[dict]:
    """直近N日の求人をフィルタ"""
    cutoff = date.today() - timedelta(days=days)
    recent = []
    
    for job in jobs:
        posted = job.get("posted_date")
        if posted:
            try:
                posted_date = date.fromisoformat(posted)
                if posted_date >= cutoff:
                    recent.append(job)
            except ValueError:
                pass
    
    return recent


# ============================================================
# レポート生成
# ============================================================

def generate_report_text(jobs: list[dict], top_n: int = DEFAULT_TOP_N) -> str:
    """テキスト形式のレポートを生成"""
    today = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    
    # スコア順でソート
    sorted_jobs = sorted(jobs, key=lambda x: x.get("score", 0), reverse=True)[:top_n]
    
    lines = [
        f"📊 UI/UX求人レーダー デイリーレポート",
        f"📅 {today}",
        f"",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🆕 新着求人 Top {top_n}（直近7日）",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"",
    ]
    
    if not sorted_jobs:
        lines.append("該当する新着求人はありません。")
    else:
        for i, job in enumerate(sorted_jobs, 1):
            score = job.get("score", 0)
            company = job.get("company_name", "不明")
            title = job.get("job_title", "不明")
            remote = job.get("remote_type", "")
            emp_type = job.get("employment_type", "")
            skills = job.get("skills", [])
            url = job.get("url", "")
            
            # スコアに応じた絵文字
            if score >= 80:
                emoji = "🔥"
            elif score >= 60:
                emoji = "⭐"
            else:
                emoji = "📝"
            
            lines.append(f"{emoji} {i}. [{score}点] {company}")
            lines.append(f"   {title}")
            
            meta = []
            if emp_type:
                meta.append(emp_type)
            if remote and remote != "unknown":
                meta.append(remote)
            if meta:
                lines.append(f"   📍 {' / '.join(meta)}")
            
            if skills:
                lines.append(f"   🛠 {', '.join(skills[:5])}")
            
            if url:
                lines.append(f"   🔗 {url}")
            
            lines.append("")
    
    # サマリー
    lines.extend([
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📈 サマリー",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"新着件数: {len(jobs)}件",
    ])
    
    if sorted_jobs:
        avg_score = sum(j.get("score", 0) for j in sorted_jobs) / len(sorted_jobs)
        lines.append(f"Top{top_n}平均スコア: {avg_score:.1f}")
        
        # カテゴリ別
        categories = {}
        for j in jobs:
            cat = j.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1
        
        lines.append(f"カテゴリ別: {', '.join(f'{k}:{v}件' for k, v in sorted(categories.items(), key=lambda x: -x[1]))}")
    
    return "\n".join(lines)


def generate_slack_blocks(jobs: list[dict], top_n: int = DEFAULT_TOP_N) -> list[dict]:
    """Slack Block Kit形式のメッセージを生成"""
    today = datetime.now().strftime("%Y年%m月%d日")
    sorted_jobs = sorted(jobs, key=lambda x: x.get("score", 0), reverse=True)[:top_n]
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🎯 UI/UX求人レーダー ({today})",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*新着求人 Top {top_n}*（直近7日）"
            }
        },
        {"type": "divider"},
    ]
    
    if not sorted_jobs:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "該当する新着求人はありません。"}
        })
    else:
        for i, job in enumerate(sorted_jobs, 1):
            score = job.get("score", 0)
            company = job.get("company_name", "不明")
            title = job.get("job_title", "不明")
            remote = job.get("remote_type", "")
            emp_type = job.get("employment_type", "")
            skills = job.get("skills", [])
            url = job.get("url", "")
            
            # スコアバッジ
            if score >= 80:
                badge = "🔥"
            elif score >= 60:
                badge = "⭐"
            else:
                badge = "📝"
            
            text_parts = [
                f"{badge} *{i}. {company}* `{score}点`",
                f">{title}",
            ]
            
            meta = []
            if emp_type:
                meta.append(emp_type)
            if remote and remote != "unknown":
                meta.append(remote)
            if meta:
                text_parts.append(f"_{' / '.join(meta)}_")
            
            if skills:
                text_parts.append(f"🛠 {', '.join(skills[:4])}")
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "\n".join(text_parts)},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "詳細", "emoji": True},
                    "url": url,
                    "action_id": f"view_job_{i}"
                } if url else None
            })
    
    # サマリー
    if sorted_jobs:
        avg_score = sum(j.get("score", 0) for j in sorted_jobs) / len(sorted_jobs)
        blocks.extend([
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"📊 新着: {len(jobs)}件 | Top{top_n}平均: {avg_score:.1f}点"}
                ]
            }
        ])
    
    # accessoryがNoneの場合は削除
    for block in blocks:
        if block.get("accessory") is None and "accessory" in block:
            del block["accessory"]
    
    return blocks


# ============================================================
# 出力
# ============================================================

def save_report_file(report_text: str, report_dir: Path) -> Path:
    """レポートをファイルに保存"""
    report_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"daily_report_{date.today().isoformat()}.txt"
    filepath = report_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    return filepath


def send_slack_notification(blocks: list[dict], webhook_url: str) -> bool:
    """Slack Webhookで通知を送信"""
    payload = {
        "blocks": blocks,
        "text": "UI/UX求人レーダー デイリーレポート",  # フォールバック
    }
    
    data = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except urllib.error.URLError as e:
        print(f"❌ Slack送信エラー: {e}", file=sys.stderr)
        return False


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="UI/UX求人レーダー デイリーレポート生成"
    )
    parser.add_argument(
        "-n", "--top",
        type=int,
        default=DEFAULT_TOP_N,
        help=f"表示件数 (default: {DEFAULT_TOP_N})"
    )
    parser.add_argument(
        "-d", "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"新着とみなす日数 (default: {DEFAULT_DAYS})"
    )
    parser.add_argument(
        "--slack",
        action="store_true",
        help="Slack通知を送信（SLACK_WEBHOOK_URL環境変数が必要）"
    )
    parser.add_argument(
        "--file",
        action="store_true",
        help="ファイルに保存"
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=DATA_PATH,
        help=f"入力ファイル (default: {DATA_PATH})"
    )
    
    args = parser.parse_args()
    
    # データ読み込み
    print(f"📥 データ読み込み中: {args.input}")
    all_jobs = load_jobs(args.input)
    
    if not all_jobs:
        print("❌ データがありません。先にCLIでデータを生成してください。")
        sys.exit(1)
    
    print(f"   全{len(all_jobs)}件")
    
    # 新着フィルタ
    recent_jobs = filter_recent_jobs(all_jobs, args.days)
    print(f"   直近{args.days}日の新着: {len(recent_jobs)}件")
    
    # レポート生成
    report_text = generate_report_text(recent_jobs, args.top)
    
    # 出力先がない場合はコンソールに表示
    if not args.slack and not args.file:
        print("\n" + report_text)
        return
    
    # ファイル保存
    if args.file:
        filepath = save_report_file(report_text, REPORT_DIR)
        print(f"📄 ファイル保存: {filepath}")
    
    # Slack通知
    if args.slack:
        webhook_url = SLACK_WEBHOOK_URL
        if not webhook_url:
            print("❌ SLACK_WEBHOOK_URL 環境変数が設定されていません", file=sys.stderr)
            sys.exit(1)
        
        print("📤 Slack通知送信中...")
        blocks = generate_slack_blocks(recent_jobs, args.top)
        
        if send_slack_notification(blocks, webhook_url):
            print("✅ Slack通知を送信しました")
        else:
            print("❌ Slack通知の送信に失敗しました")
            sys.exit(1)


if __name__ == "__main__":
    main()

