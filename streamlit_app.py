"""
UI/UX求人レーダー - 営業リストビューア
Streamlit App（Premium UI Design）

Color Palette:
- Background: #FFFFFF (White)
- Base: #1E3A5F (Navy)
- Accent: #FF6B35 (Orange)
- Success: #28A745
- Warning: #FFC107
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
import pandas as pd

# === 設定 ===
DATA_PATH = Path(__file__).parent / "data" / "out" / "jobs_norm.jsonl"
TOP_N = 20

# === カラーパレット ===
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


# === カスタムCSS ===
def apply_custom_css():
    st.markdown(f"""
    <style>
        /* 全体のフォント・背景 */
        .stApp {{
            background-color: {COLORS['white']};
            font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Noto Sans JP', sans-serif;
        }}
        
        /* ヘッダー */
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
        
        /* メトリクスカード */
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
        
        /* HOTバッジ */
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.3rem;
        }}
        
        .badge-hot {{
            background: linear-gradient(135deg, {COLORS['orange']} 0%, #FF8C5A 100%);
            color: white;
        }}
        
        .badge-new {{
            background: {COLORS['navy']};
            color: white;
        }}
        
        .badge-week {{
            background: {COLORS['gray']};
            color: {COLORS['navy']};
        }}
        
        /* セクションタイトル */
        .section-title {{
            color: {COLORS['navy']};
            font-size: 1.2rem;
            font-weight: 700;
            padding-bottom: 0.75rem;
            border-bottom: 3px solid {COLORS['orange']};
            margin-bottom: 1rem;
            display: inline-block;
        }}
        
        /* サイドバー */
        [data-testid="stSidebar"] {{
            background-color: {COLORS['gray_light']};
        }}
        
        [data-testid="stSidebar"] .stRadio > label {{
            color: {COLORS['navy']};
            font-weight: 600;
        }}
        
        /* ボタン */
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
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
        }}
        
        /* データフレーム */
        [data-testid="stDataFrame"] {{
            border: 1px solid {COLORS['gray']};
            border-radius: 12px;
            overflow: hidden;
        }}
        
        /* 区切り線 */
        hr {{
            border: none;
            border-top: 1px solid {COLORS['gray']};
            margin: 1.5rem 0;
        }}
        
        /* Streamlitデフォルトの非表示 */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        /* プログレスバーの色 */
        .stProgress > div > div > div > div {{
            background: linear-gradient(90deg, {COLORS['navy']} 0%, {COLORS['orange']} 100%);
        }}
    </style>
    """, unsafe_allow_html=True)


# === データ読み込み ===
@st.cache_data
def load_data() -> pd.DataFrame:
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


def render_metric_card(label: str, value: str, highlight: bool = False, orange: bool = False):
    """メトリクスカードをレンダリング"""
    highlight_class = "highlight" if highlight else ""
    value_class = "orange" if orange else ""
    return f"""
    <div class="metric-card {highlight_class}">
        <div class="metric-value {value_class}">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


# === メイン ===
def main():
    st.set_page_config(
        page_title="UI/UX求人レーダー",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # カスタムCSS適用
    apply_custom_css()

    # ヘッダー
    st.markdown("""
    <div class="main-header">
        <h1>🎯 UI/UX求人レーダー</h1>
        <p>営業リスト - UI/UXデザイナー求人を出している企業を即日アプローチ！</p>
    </div>
    """, unsafe_allow_html=True)

    # データ読み込み
    df = load_data()

    if df.empty:
        st.error(f"❌ データが見つかりません: `{DATA_PATH}`")
        st.info("先に以下のコマンドを実行してください:")
        st.code(
            "python scripts/generate_dummy.py\npython src/cli.py",
            language="bash"
        )
        return

    # === サイドバー: フィルター ===
    with st.sidebar:
        st.markdown(f"### 🔧 フィルター")
        
        # ソート順選択
        st.markdown("**並び順**")
        sort_options = {
            "🔥 新着順（即日アプローチ）": "newest",
            "⭐ スコア順": "score",
        }
        selected_sort = st.radio(
            "並び順を選択",
            list(sort_options.keys()),
            index=0,
            label_visibility="collapsed",
        )
        sort_by = sort_options[selected_sort]

        st.markdown("---")
        
        # 新着フィルター
        st.markdown("**📅 掲載日フィルター**")
        freshness_options = {
            "すべて": None,
            "🔥 本日のみ": 0,
            "⚡ 24時間以内": 1,
            "✨ 3日以内": 3,
            "🆕 1週間以内": 7,
        }
        selected_freshness = st.radio(
            "掲載日を選択",
            list(freshness_options.keys()),
            label_visibility="collapsed",
        )
        max_days = freshness_options[selected_freshness]

        st.markdown("---")
        
        # スコア閾値
        st.markdown("**📊 スコアフィルター**")
        min_score = int(df["score"].min())
        max_score = int(df["score"].max())
        score_threshold = st.slider(
            "最低スコア",
            min_value=min_score,
            max_value=max_score,
            value=min_score,
            step=5,
        )

        st.markdown("---")
        
        # カテゴリフィルター
        if "category" in df.columns:
            st.markdown("**📁 カテゴリ**")
            categories = ["すべて"] + sorted(df["category"].unique().tolist())
            selected_category = st.selectbox("カテゴリを選択", categories, label_visibility="collapsed")
        else:
            selected_category = "すべて"

        # リモートタイプフィルター
        if "remote_type" in df.columns:
            st.markdown("**🏠 リモートタイプ**")
            remote_types = ["すべて"] + sorted(df["remote_type"].unique().tolist())
            selected_remote = st.selectbox("リモートタイプを選択", remote_types, label_visibility="collapsed")
        else:
            selected_remote = "すべて"

    # === フィルター適用 ===
    filtered_df = df[df["score"] >= score_threshold].copy()

    if selected_category != "すべて":
        filtered_df = filtered_df[filtered_df["category"] == selected_category]

    if selected_remote != "すべて":
        filtered_df = filtered_df[filtered_df["remote_type"] == selected_remote]

    # 新着フィルター適用
    if max_days is not None and "days_ago" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["days_ago"] <= max_days]

    # ソート適用
    if sort_by == "newest" and "posted_date" in filtered_df.columns:
        filtered_df = filtered_df.sort_values(
            ["posted_date", "score"], 
            ascending=[False, False]
        )
    else:
        filtered_df = filtered_df.sort_values("score", ascending=False)

    # Top N
    filtered_df = filtered_df.head(TOP_N)

    # === メトリクス ===
    if "days_ago" in df.columns:
        today_count = len(df[df["days_ago"] == 0])
        yesterday_count = len(df[df["days_ago"] == 1])
        week_count = len(df[df["days_ago"] <= 7])
        avg_score = filtered_df['score'].mean() if not filtered_df.empty else 0
        
        cols = st.columns(5)
        
        with cols[0]:
            st.markdown(render_metric_card("🔥 本日掲載", f"{today_count}件", highlight=True, orange=True), unsafe_allow_html=True)
        with cols[1]:
            st.markdown(render_metric_card("⚡ 昨日掲載", f"{yesterday_count}件"), unsafe_allow_html=True)
        with cols[2]:
            st.markdown(render_metric_card("🆕 1週間以内", f"{week_count}件"), unsafe_allow_html=True)
        with cols[3]:
            st.markdown(render_metric_card("📊 平均スコア", f"{avg_score:.1f}"), unsafe_allow_html=True)
        with cols[4]:
            st.markdown(render_metric_card("📋 全データ", f"{len(df)}件"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # === テーブル表示 ===
    if filtered_df.empty:
        st.warning("条件に一致する求人がありません。フィルターを調整してください。")
        return

    # タイトル
    if sort_by == "newest":
        st.markdown('<p class="section-title">🔥 即日アプローチリスト（新着順）</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="section-title">⭐ 営業リスト Top 20（スコア順）</p>', unsafe_allow_html=True)

    # 表示用カラムを整形
    display_columns = ["company_name", "job_title", "score"]
    
    # HOTバッジ + 掲載日を追加
    if "hot_badge" in filtered_df.columns and "posted_date_str" in filtered_df.columns:
        filtered_df["freshness"] = filtered_df.apply(
            lambda row: f"{row['hot_badge']} {row['posted_date_str']}" if row['hot_badge'] else row['posted_date_str'],
            axis=1
        )
        display_columns.append("freshness")
    
    display_columns.extend(["remote_type", "employment_type", "skills_text", "url"])
    
    display_df = filtered_df[display_columns].copy()

    # カラム名を日本語に
    column_names = {
        "company_name": "企業名",
        "job_title": "職種",
        "score": "スコア",
        "freshness": "📅 掲載日",
        "remote_type": "リモート",
        "employment_type": "雇用形態",
        "skills_text": "スキル",
        "url": "URL",
    }
    display_df.columns = [column_names.get(c, c) for c in display_df.columns]

    # インデックスをリセット（1から開始）
    display_df = display_df.reset_index(drop=True)
    display_df.index = display_df.index + 1

    st.dataframe(
        display_df,
        use_container_width=True,
        height=550,
        column_config={
            "スコア": st.column_config.ProgressColumn(
                "スコア",
                min_value=0,
                max_value=100,
                format="%d",
            ),
            "URL": st.column_config.LinkColumn("URL", display_text="リンク"),
        },
    )

    # === ダウンロード ===
    st.markdown("<br>", unsafe_allow_html=True)
    
    # CSV用のカラム
    csv_columns = ["company_name", "job_title", "score"]
    if "posted_date" in filtered_df.columns:
        csv_columns.append("posted_date")
    csv_columns.extend(["remote_type", "employment_type", "skills_text", "url"])

    csv_data = filtered_df[[c for c in csv_columns if c in filtered_df.columns]].copy()
    if "posted_date" in csv_data.columns:
        csv_data["posted_date"] = csv_data["posted_date"].dt.strftime("%Y-%m-%d")
    
    csv_str = csv_data.to_csv(index=False, encoding="utf-8-sig")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv_str,
            file_name=f"uiux_leads_{date.today().isoformat()}.csv",
            mime="text/csv",
        )
    with col2:
        if "days_ago" in df.columns:
            today_df = df[df["days_ago"] == 0]
            if not today_df.empty:
                today_csv = today_df[[c for c in csv_columns if c in today_df.columns]].copy()
                if "posted_date" in today_csv.columns:
                    today_csv["posted_date"] = today_csv["posted_date"].dt.strftime("%Y-%m-%d")
                today_csv_str = today_csv.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="🔥 本日分のみ",
                    data=today_csv_str,
                    file_name=f"uiux_today_{date.today().isoformat()}.csv",
                    mime="text/csv",
                )


if __name__ == "__main__":
    main()
