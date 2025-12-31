#!/bin/bash
# 毎朝9時にデイリーレポートを実行するcron設定スクリプト

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# cronエントリ
CRON_ENTRY="0 9 * * * cd $PROJECT_DIR && /usr/bin/python3 scripts/daily_report.py --file >> /tmp/uiux_radar_cron.log 2>&1"

echo "=== UI/UX求人レーダー cron設定 ==="
echo ""
echo "以下のエントリをcrontabに追加します："
echo ""
echo "$CRON_ENTRY"
echo ""

read -p "追加しますか？ (y/n): " confirm

if [ "$confirm" = "y" ]; then
    # 既存のcrontabを取得して追加
    (crontab -l 2>/dev/null | grep -v "daily_report.py"; echo "$CRON_ENTRY") | crontab -
    echo "✅ crontabに追加しました"
    echo ""
    echo "現在のcrontab:"
    crontab -l
else
    echo "キャンセルしました"
fi

echo ""
echo "=== 手動実行の場合 ==="
echo "cd $PROJECT_DIR"
echo "python scripts/daily_report.py"
echo ""
echo "=== Slack通知を使う場合 ==="
echo "1. Slack App作成 → Incoming Webhook有効化"
echo "2. .env に SLACK_WEBHOOK_URL を設定"
echo "3. python scripts/daily_report.py --slack"

