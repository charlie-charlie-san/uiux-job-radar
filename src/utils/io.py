"""共通データ読み込みユーティリティ"""

import json
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "out" / "jobs_norm.jsonl"

# カラーパレット
COLORS = {
    "navy": "#1E3A5F",
    "navy_light": "#2D5A8B",
    "orange": "#FF6B35",
    "orange_light": "#FF8C5A",
    "white": "#FFFFFF",
    "gray_light": "#F8F9FC",
    "gray": "#E9ECEF",
    "text": "#1E3A5F",
    "text_muted": "#6C757D",
    "success": "#28A745",
    "warning": "#FFC107",
}


@st.cache_data
def load_jobs() -> pd.DataFrame:
    """JSONLファイルを読み込んでDataFrameに変換"""
    if not DATA_PATH.exists():
        return pd.DataFrame()

    records = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # skills をカンマ区切り文字列に変換
    if "skills" in df.columns:
        df["skills_text"] = df["skills"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else ""
        )

    # 掲載日をdatetime型に変換
    if "posted_date" in df.columns:
        df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce")
        
        # 経過日数を計算
        today = pd.Timestamp(date.today())
        df["days_ago"] = (today - df["posted_date"]).dt.days
        
        # HOTバッジ判定
        df["hot_badge"] = df["days_ago"].apply(_get_hot_badge)
        
        # 表示用の日付文字列
        df["posted_date_str"] = df.apply(
            lambda row: _format_posted_date(row["posted_date"], row["days_ago"]), 
            axis=1
        )

    return df


def _get_hot_badge(days_ago: int) -> str:
    """経過日数に応じたHOTバッジを返す"""
    if pd.isna(days_ago):
        return ""
    if days_ago == 0:
        return "🔥 本日"
    elif days_ago == 1:
        return "⚡ 昨日"
    elif days_ago <= 3:
        return "✨ 3日以内"
    elif days_ago <= 7:
        return "🆕 1週間"
    return ""


def _format_posted_date(posted_date, days_ago: int) -> str:
    """掲載日を見やすくフォーマット"""
    if pd.isna(posted_date):
        return "—"
    
    date_str = posted_date.strftime("%m/%d")
    
    if pd.isna(days_ago):
        return date_str
    elif days_ago == 0:
        return f"{date_str}（本日）"
    elif days_ago == 1:
        return f"{date_str}（昨日）"
    elif days_ago <= 7:
        return f"{date_str}（{days_ago}日前）"
    else:
        return date_str


def apply_custom_css():
    """共通カスタムCSSを適用"""
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {COLORS['white']};
            font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Noto Sans JP', sans-serif;
        }}
        
        .main-header {{
            background: linear-gradient(135deg, {COLORS['navy']} 0%, {COLORS['navy_light']} 100%);
            color: white;
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px rgba(30, 58, 95, 0.1);
        }}
        
        .main-header h1 {{
            margin: 0;
            font-size: 1.8rem;
            font-weight: 700;
        }}
        
        .main-header p {{
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
            font-size: 0.95rem;
        }}
        
        .metric-card {{
            background: {COLORS['white']};
            border: 1px solid {COLORS['gray']};
            border-radius: 12px;
            padding: 1.2rem;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: all 0.2s ease;
        }}
        
        .metric-card:hover {{
            border-color: {COLORS['orange']};
            box-shadow: 0 4px 12px rgba(255, 107, 53, 0.15);
        }}
        
        .metric-card.highlight {{
            border-color: {COLORS['orange']};
            background: linear-gradient(135deg, #FFF5F0 0%, {COLORS['white']} 100%);
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {COLORS['navy']};
            line-height: 1.2;
        }}
        
        .metric-value.orange {{
            color: {COLORS['orange']};
        }}
        
        .metric-label {{
            font-size: 0.85rem;
            color: {COLORS['text_muted']};
            margin-top: 0.3rem;
        }}
        
        .section-title {{
            color: {COLORS['navy']};
            font-size: 1.2rem;
            font-weight: 700;
            padding-bottom: 0.75rem;
            border-bottom: 3px solid {COLORS['orange']};
            margin-bottom: 1rem;
            display: inline-block;
        }}
        
        .company-card {{
            background: {COLORS['white']};
            border: 1px solid {COLORS['gray']};
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        }}
        
        .company-card:hover {{
            border-color: {COLORS['navy']};
            box-shadow: 0 4px 12px rgba(30, 58, 95, 0.1);
        }}
        
        .action-item {{
            background: {COLORS['gray_light']};
            border-left: 4px solid {COLORS['orange']};
            padding: 1rem;
            margin-bottom: 0.75rem;
            border-radius: 0 8px 8px 0;
        }}
        
        .action-item.completed {{
            border-left-color: {COLORS['success']};
            opacity: 0.7;
        }}
        
        [data-testid="stSidebar"] {{
            background-color: {COLORS['gray_light']};
        }}
        
        .stDownloadButton > button {{
            background: linear-gradient(135deg, {COLORS['navy']} 0%, {COLORS['navy_light']} 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.6rem 1.5rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        
        .stDownloadButton > button:hover {{
            background: linear-gradient(135deg, {COLORS['orange']} 0%, {COLORS['orange_light']} 100%);
        }}
        
        hr {{
            border: none;
            border-top: 1px solid {COLORS['gray']};
            margin: 1.5rem 0;
        }}
        
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, highlight: bool = False, orange: bool = False) -> str:
    """メトリクスカードのHTMLを返す"""
    highlight_class = "highlight" if highlight else ""
    value_class = "orange" if orange else ""
    return f"""
    <div class="metric-card {highlight_class}">
        <div class="metric-value {value_class}">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

