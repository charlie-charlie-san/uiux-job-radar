"""
UI/UX求人レーダー - 営業リスト
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from src.utils.io import load_jobs, apply_custom_css, render_metric_card, COLORS

st.set_page_config(
    page_title="営業リスト | UI/UX求人レーダー",
    page_icon="📋",
    layout="wide",
)

apply_custom_css()

# ヘッダー
st.markdown("""
<div class="main-header">
    <h1>📋 営業リスト</h1>
    <p>新着順・スコア順で求人を確認 → 即日アプローチ！</p>
</div>
""", unsafe_allow_html=True)

# データ読み込み
df = load_jobs()

if df.empty:
    st.error("❌ データが見つかりません")
    st.stop()

# サイドバー
with st.sidebar:
    st.markdown("### 🔧 フィルター")
    
    # ソート順
    st.markdown("**並び順**")
    sort_options = {"🔥 新着順": "newest", "⭐ スコア順": "score"}
    selected_sort = st.radio("並び順", list(sort_options.keys()), label_visibility="collapsed")
    sort_by = sort_options[selected_sort]
    
    st.markdown("---")
    
    # 新着フィルター
    st.markdown("**📅 掲載日**")
    freshness_options = {"すべて": None, "🔥 本日": 0, "⚡ 24h以内": 1, "✨ 3日以内": 3, "🆕 1週間": 7}
    selected_freshness = st.radio("掲載日", list(freshness_options.keys()), label_visibility="collapsed")
    max_days = freshness_options[selected_freshness]
    
    st.markdown("---")
    
    # スコア
    st.markdown("**📊 スコア**")
    score_threshold = st.slider("最低スコア", int(df["score"].min()), int(df["score"].max()), int(df["score"].min()), 5)
    
    st.markdown("---")
    
    # カテゴリ
    if "category" in df.columns:
        st.markdown("**📁 カテゴリ**")
        categories = ["すべて"] + sorted(df["category"].unique().tolist())
        selected_category = st.selectbox("カテゴリ", categories, label_visibility="collapsed")
    else:
        selected_category = "すべて"
    
    # リモート
    if "remote_type" in df.columns:
        st.markdown("**🏠 リモート**")
        remote_types = ["すべて"] + sorted(df["remote_type"].unique().tolist())
        selected_remote = st.selectbox("リモート", remote_types, label_visibility="collapsed")
    else:
        selected_remote = "すべて"

# フィルター適用
filtered_df = df[df["score"] >= score_threshold].copy()

if selected_category != "すべて":
    filtered_df = filtered_df[filtered_df["category"] == selected_category]

if selected_remote != "すべて":
    filtered_df = filtered_df[filtered_df["remote_type"] == selected_remote]

if max_days is not None and "days_ago" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["days_ago"] <= max_days]

# ソート
if sort_by == "newest" and "posted_date" in filtered_df.columns:
    filtered_df = filtered_df.sort_values(["posted_date", "score"], ascending=[False, False])
else:
    filtered_df = filtered_df.sort_values("score", ascending=False)

filtered_df = filtered_df.head(20)

# メトリクス
if "days_ago" in df.columns:
    cols = st.columns(5)
    with cols[0]:
        st.markdown(render_metric_card("🔥 本日", f"{len(df[df['days_ago'] == 0])}件", highlight=True, orange=True), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(render_metric_card("⚡ 昨日", f"{len(df[df['days_ago'] == 1])}件"), unsafe_allow_html=True)
    with cols[2]:
        st.markdown(render_metric_card("🆕 1週間", f"{len(df[df['days_ago'] <= 7])}件"), unsafe_allow_html=True)
    with cols[3]:
        st.markdown(render_metric_card("📊 平均", f"{filtered_df['score'].mean():.1f}" if not filtered_df.empty else "—"), unsafe_allow_html=True)
    with cols[4]:
        st.markdown(render_metric_card("📋 表示", f"{len(filtered_df)}件"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# テーブル
if filtered_df.empty:
    st.warning("条件に一致する求人がありません")
    st.stop()

title = "🔥 即日アプローチリスト（新着順）" if sort_by == "newest" else "⭐ 営業リスト Top 20（スコア順）"
st.markdown(f'<p class="section-title">{title}</p>', unsafe_allow_html=True)

# 表示用データ
display_columns = ["company_name", "job_title", "score"]
if "hot_badge" in filtered_df.columns and "posted_date_str" in filtered_df.columns:
    filtered_df["freshness"] = filtered_df.apply(
        lambda row: f"{row['hot_badge']} {row['posted_date_str']}" if row['hot_badge'] else row['posted_date_str'], axis=1
    )
    display_columns.append("freshness")
display_columns.extend(["remote_type", "employment_type", "skills_text", "url"])

display_df = filtered_df[display_columns].copy()
display_df.columns = ["企業名", "職種", "スコア", "📅 掲載日", "リモート", "雇用形態", "スキル", "URL"][:len(display_columns)]
display_df = display_df.reset_index(drop=True)
display_df.index = display_df.index + 1

st.dataframe(
    display_df,
    use_container_width=True,
    height=550,
    column_config={
        "スコア": st.column_config.ProgressColumn("スコア", min_value=0, max_value=100, format="%d"),
        "URL": st.column_config.LinkColumn("URL", display_text="リンク"),
    },
)

# ダウンロード
st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 3])
with col1:
    csv_data = filtered_df[["company_name", "job_title", "score", "remote_type", "employment_type", "skills_text", "url"]].to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 CSVダウンロード", csv_data, f"uiux_leads_{date.today().isoformat()}.csv", "text/csv")

