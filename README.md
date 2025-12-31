# 🎯 UI/UX求人レーダー

UI/UX系求人を自動収集・スコアリングし、営業リストを生成するツール。
**キーエンス式「即日アプローチ」** 対応。

## ✨ 機能

- 🔥 **即日アプローチ対応** - 掲載当日の求人を即座に検知・通知
- 🤖 **LLMスコアリング** - Claude APIで派遣向き度・緊急度を自動判定
- 📊 **Streamlit ダッシュボード** - 新着順/スコア順でリスト表示
- 📅 **デイリーレポート** - 毎朝Slack通知で新着求人をお届け

## 🚀 クイックスタート

```bash
# 依存パッケージインストール
pip install -r requirements.txt

# ダミーデータ生成
python scripts/generate_dummy.py

# スコアリング・正規化
python src/cli.py

# Streamlit起動
streamlit run streamlit_app.py
```

## 📁 フォルダ構成

```
uiux_job_radar/
├── streamlit_app.py          # Webダッシュボード
├── requirements.txt
├── .env                      # APIキー（要作成）
├── data/
│   └── out/
│       ├── jobs_raw.jsonl    # 生データ
│       └── jobs_norm.jsonl   # 正規化済み
├── scripts/
│   ├── generate_dummy.py     # ダミーデータ生成
│   ├── daily_report.py       # デイリーレポート
│   ├── instant_alert.py      # 即日アプローチアラート
│   └── setup_daily_cron.sh   # cron設定
└── src/
    ├── cli.py                # メインCLI
    ├── models.py             # データモデル
    └── pipeline/
        ├── score.py          # ルールベーススコアリング
        ├── normalize.py      # 正規化処理
        └── llm_score.py      # LLMスコアリング
```

## ⚙️ 環境変数

`.env` ファイルを作成：

```bash
# LLMスコアリング用
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Slack通知用（オプション）
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxxxx
```

## 📖 使い方

### CLI

```bash
# 基本実行
python src/cli.py

# LLMスコアリング有効（上位20件）
python src/cli.py --llm --llm-limit 20

# Top10のみ出力
python src/cli.py --top 10
```

### デイリーレポート

```bash
# コンソール表示
python scripts/daily_report.py -n 10

# Slack通知
python scripts/daily_report.py --slack
```

### 即日アプローチアラート

```bash
# 本日掲載のみ表示
python scripts/instant_alert.py

# スコア60以上のみSlack通知
python scripts/instant_alert.py --slack --min-score 60
```

## 🎯 スコアリング

### ルールベース（高速）
| 条件 | 加点 |
|------|------|
| UI/UXデザイナー | +30〜35 |
| Figma | +15 |
| デザインシステム | +12 |
| 業務委託 | +10 |
| フルリモート | +8 |
| バナー/広告系 | -15 |

### LLM（Claude）
| 評価軸 | 説明 |
|--------|------|
| 派遣向き度 | 業務委託・派遣で対応しやすいか |
| 緊急度 | 今すぐ人材が欲しそうか |
| スキルマッチ度 | UI/UXデザイナーとしての純度 |

## 📊 Streamlit ダッシュボード

- **新着順ソート** - 即日アプローチ推奨
- **HOTバッジ** - 🔥本日 / ⚡昨日 / ✨3日以内
- **フィルター** - スコア閾値、カテゴリ、リモートタイプ
- **CSVダウンロード** - 本日掲載のみも可

## 🔔 定時実行

```bash
# cron設定（毎朝9時）
./scripts/setup_daily_cron.sh
```

## 📝 License

MIT
