#!/usr/bin/env python3
"""
即日アプローチアラート

本日掲載の求人を検知して即座に通知
キーエンス式ターゲティングマーケティング対応
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
import urllib.request
import urllib.error

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================
# 設定
# ============================================================

DATA_PATH = PROJECT_ROOT / "data" / "out" / "jobs_norm.jsonl"
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


# ============================================================
# データ処理
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


def filter_today_jobs(jobs: list[dict]) -> list[dict]:
    """本日掲載の求人をフィルタ"""
    today = date.today()
    today_jobs = []
    
    for job in jobs:
        posted = job.get("posted_date")
        if posted:
            try:
                posted_date = date.fromisoformat(posted)
                if posted_date == today:
                    today_jobs.append(job)
            except ValueError:
                pass
    
    # スコア順でソート
    return sorted(today_jobs, key=lambda x: x.get("score", 0), reverse=True)


# ============================================================
# 出力
# ============================================================

def generate_alert_text(jobs: list[dict]) -> str:
    """アラートテキストを生成"""
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    
    lines = [
        "🚨 即日アプローチアラート 🚨",
        f"⏰ {now}",
        "",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🔥 本日掲載の求人: {len(jobs)}件",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]
    
    if not jobs:
        lines.append("本日掲載の新着求人はありません。")
    else:
        for i, job in enumerate(jobs, 1):
            score = job.get("score", 0)
            company = job.get("company_name", "不明")
            title = job.get("job_title", "不明")
            remote = job.get("remote_type", "")
            emp_type = job.get("employment_type", "")
            category = job.get("category", "")
            url = job.get("url", "")
            
            # スコアに応じたマーク
            if score >= 80:
                mark = "🔥🔥🔥"
            elif score >= 60:
                mark = "🔥🔥"
            elif score >= 40:
                mark = "🔥"
            else:
                mark = "📝"
            
            lines.append(f"{mark} {i}. [{score}点] {company}")
            lines.append(f"   📋 {title}")
            
            meta = []
            if emp_type:
                meta.append(emp_type)
            if remote and remote != "unknown":
                meta.append(remote)
            if category:
                meta.append(f"[{category}]")
            if meta:
                lines.append(f"   📍 {' / '.join(meta)}")
            
            if url:
                lines.append(f"   🔗 {url}")
            
            lines.append("")
    
    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💡 即日アプローチで競合に差をつけよう！",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ])
    
    return "\n".join(lines)


def generate_slack_blocks(jobs: list[dict]) -> list[dict]:
    """Slack Block Kit形式のメッセージを生成"""
    today = datetime.now().strftime("%m/%d %H:%M")
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 即日アプローチアラート ({today})",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🔥 本日掲載: {len(jobs)}件*\n競合より先にアプローチしましょう！"
            }
        },
        {"type": "divider"},
    ]
    
    if not jobs:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "本日掲載の新着求人はありません。"}
        })
    else:
        # 上位5件のみSlackに表示
        for i, job in enumerate(jobs[:5], 1):
            score = job.get("score", 0)
            company = job.get("company_name", "不明")
            title = job.get("job_title", "不明")
            emp_type = job.get("employment_type", "")
            remote = job.get("remote_type", "")
            url = job.get("url", "")
            
            # スコアバッジ
            if score >= 80:
                badge = "🔥🔥🔥"
            elif score >= 60:
                badge = "🔥🔥"
            else:
                badge = "🔥"
            
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
            
            block = {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "\n".join(text_parts)},
            }
            
            if url:
                block["accessory"] = {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "詳細", "emoji": True},
                    "url": url,
                    "action_id": f"view_job_{i}",
                    "style": "primary" if score >= 60 else None,
                }
                # styleがNoneの場合は削除
                if block["accessory"]["style"] is None:
                    del block["accessory"]["style"]
            
            blocks.append(block)
        
        # 残りがある場合
        if len(jobs) > 5:
            blocks.append({
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"📋 他 {len(jobs) - 5}件 → Streamlitで確認"}
                ]
            })
    
    blocks.extend([
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "💡 _即日アプローチで競合に差をつけよう！_"}
            ]
        }
    ])
    
    return blocks


def send_slack_notification(blocks: list[dict], webhook_url: str) -> bool:
    """Slack Webhookで通知を送信"""
    payload = {
        "blocks": blocks,
        "text": "🚨 即日アプローチアラート",
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
        description="即日アプローチアラート - 本日掲載の求人を即座に通知"
    )
    parser.add_argument(
        "--slack",
        action="store_true",
        help="Slack通知を送信（SLACK_WEBHOOK_URL環境変数が必要）"
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=DATA_PATH,
        help=f"入力ファイル (default: {DATA_PATH})"
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="通知する最低スコア（default: 0）"
    )
    
    args = parser.parse_args()
    
    # データ読み込み
    print(f"📥 データ読み込み中: {args.input}")
    all_jobs = load_jobs(args.input)
    
    if not all_jobs:
        print("❌ データがありません")
        sys.exit(1)
    
    # 本日掲載をフィルタ
    today_jobs = filter_today_jobs(all_jobs)
    
    # スコアフィルタ
    if args.min_score > 0:
        today_jobs = [j for j in today_jobs if j.get("score", 0) >= args.min_score]
    
    print(f"🔥 本日掲載: {len(today_jobs)}件")
    
    # テキスト生成
    alert_text = generate_alert_text(today_jobs)
    
    # Slack通知
    if args.slack:
        webhook_url = SLACK_WEBHOOK_URL
        if not webhook_url:
            print("❌ SLACK_WEBHOOK_URL 環境変数が設定されていません", file=sys.stderr)
            # コンソールにも出力
            print("\n" + alert_text)
            sys.exit(1)
        
        print("📤 Slack通知送信中...")
        blocks = generate_slack_blocks(today_jobs)
        
        if send_slack_notification(blocks, webhook_url):
            print("✅ Slack通知を送信しました")
        else:
            print("❌ Slack通知の送信に失敗しました")
            # コンソールにも出力
            print("\n" + alert_text)
            sys.exit(1)
    else:
        # コンソール出力
        print("\n" + alert_text)
    
    # 件数を返す（CI/CD連携用）
    return len(today_jobs)


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count >= 0 else 1)

