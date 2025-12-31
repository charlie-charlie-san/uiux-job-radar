"""
UI/UX求人レーダー - 営業リストビューア
Streamlit App（キーエンス式 即日アプローチ対応）
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
import pandas as pd

# === 設定 ===
DATA_PATH = Path(__file__).parent / "data" / "out" / "jobs_norm.jsonl"
TOP_N = 20


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
        return "🆕 1週間以内"
    return ""


def _format_posted_date(posted_date, days_ago: int) -> str:
    """掲載日を見やすくフォーマット"""
    if pd.isna(posted_date):
        return "不明"
    
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


# === メイン ===
def main():
    st.set_page_config(
        page_title="UI/UX求人レーダー",
        page_icon="🎯",
        layout="wide",
    )

    # ヘッダー
    st.title("🎯 UI/UX求人レーダー")
    st.markdown("**営業リスト** - UI/UXデザイナー求人を出している企業を即日アプローチ！")

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
    st.sidebar.header("🔧 フィルター")

    # ソート順選択
    sort_options = {
        "🔥 新着順（即日アプローチ推奨）": "newest",
        "⭐ スコア順": "score",
    }
    selected_sort = st.sidebar.radio(
        "並び順",
        list(sort_options.keys()),
        index=0,  # デフォルトは新着順
    )
    sort_by = sort_options[selected_sort]

    # 新着フィルター
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 新着フィルター")
    
    freshness_options = {
        "すべて": None,
        "🔥 本日のみ": 0,
        "⚡ 24時間以内": 1,
        "✨ 3日以内": 3,
        "🆕 1週間以内": 7,
    }
    selected_freshness = st.sidebar.radio(
        "掲載日",
        list(freshness_options.keys()),
    )
    max_days = freshness_options[selected_freshness]

    # スコア閾値
    st.sidebar.markdown("---")
    min_score = int(df["score"].min())
    max_score = int(df["score"].max())
    score_threshold = st.sidebar.slider(
        "最低スコア",
        min_value=min_score,
        max_value=max_score,
        value=min_score,
        step=5,
    )

    # カテゴリフィルター
    if "category" in df.columns:
        categories = ["すべて"] + sorted(df["category"].unique().tolist())
        selected_category = st.sidebar.selectbox("カテゴリ", categories)
    else:
        selected_category = "すべて"

    # リモートタイプフィルター
    if "remote_type" in df.columns:
        remote_types = ["すべて"] + sorted(df["remote_type"].unique().tolist())
        selected_remote = st.sidebar.selectbox("リモートタイプ", remote_types)
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

    # === 本日掲載のハイライト ===
    if "days_ago" in df.columns:
        today_count = len(df[df["days_ago"] == 0])
        yesterday_count = len(df[df["days_ago"] == 1])
        week_count = len(df[df["days_ago"] <= 7])
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("🔥 本日掲載", f"{today_count}件", 
                     delta="即アプローチ！" if today_count > 0 else None)
        with col2:
            st.metric("⚡ 昨日掲載", f"{yesterday_count}件")
        with col3:
            st.metric("🆕 1週間以内", f"{week_count}件")
        with col4:
            if not filtered_df.empty:
                st.metric("平均スコア", f"{filtered_df['score'].mean():.1f}")
        with col5:
            st.metric("全データ件数", f"{len(df)}件")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("表示件数", f"{len(filtered_df)}件")
        with col2:
            if not filtered_df.empty:
                st.metric("最高スコア", filtered_df["score"].max())
        with col3:
            if not filtered_df.empty:
                st.metric("平均スコア", f"{filtered_df['score'].mean():.1f}")
        with col4:
            st.metric("全データ件数", f"{len(df)}件")

    st.divider()

    # === テーブル表示 ===
    if filtered_df.empty:
        st.warning("条件に一致する求人がありません。フィルターを調整してください。")
        return

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
        "url": "求人URL",
    }
    display_df.columns = [column_names.get(c, c) for c in display_df.columns]

    # URLをクリック可能に
    display_df["求人URL"] = display_df["求人URL"].apply(
        lambda x: f"[リンク]({x})" if x else ""
    )

    # インデックスをリセット（1から開始）
    display_df = display_df.reset_index(drop=True)
    display_df.index = display_df.index + 1

    # タイトル
    if sort_by == "newest":
        st.markdown("### 🔥 即日アプローチリスト（新着順）")
    else:
        st.markdown("### ⭐ 営業リスト Top 20（スコア順）")

    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        column_config={
            "スコア": st.column_config.ProgressColumn(
                "スコア",
                min_value=0,
                max_value=100,
                format="%d",
            ),
            "求人URL": st.column_config.LinkColumn("求人URL"),
        },
    )

    # === ダウンロード ===
    st.divider()

    # CSV用のカラム
    csv_columns = ["company_name", "job_title", "score"]
    if "posted_date" in filtered_df.columns:
        csv_columns.append("posted_date")
    csv_columns.extend(["remote_type", "employment_type", "skills_text", "url"])

    csv_data = filtered_df[[c for c in csv_columns if c in filtered_df.columns]].copy()
    if "posted_date" in csv_data.columns:
        csv_data["posted_date"] = csv_data["posted_date"].dt.strftime("%Y-%m-%d")
    
    csv_str = csv_data.to_csv(index=False, encoding="utf-8-sig")

    col1, col2 = st.columns(2)
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
                    label="🔥 本日掲載のみダウンロード",
                    data=today_csv_str,
                    file_name=f"uiux_today_{date.today().isoformat()}.csv",
                    mime="text/csv",
                )


if __name__ == "__main__":
    main()
