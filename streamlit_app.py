"""
UI/UX求人レーダー - ホーム
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from src.utils.io import load_jobs, apply_custom_css, render_metric_card, COLORS

st.set_page_config(
    page_title="UI/UX求人レーダー",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_css()

# ヘッダー
st.markdown("""
<div class="main-header">
    <h1>🎯 UI/UX求人レーダー</h1>
    <p>UI/UXデザイナー求人を出している企業を自動検知 → 即日アプローチ！</p>
</div>
""", unsafe_allow_html=True)

# データ読み込み
df = load_jobs()

if df.empty:
    st.error("❌ データが見つかりません")
    st.info("先に以下のコマンドを実行してください:")
    st.code("python scripts/generate_dummy.py\npython src/cli.py", language="bash")
    st.stop()

# メトリクス
st.markdown('<p class="section-title">📊 ダッシュボード</p>', unsafe_allow_html=True)

if "days_ago" in df.columns:
    today_count = len(df[df["days_ago"] == 0])
    yesterday_count = len(df[df["days_ago"] == 1])
    week_count = len(df[df["days_ago"] <= 7])
    avg_score = df['score'].mean()
    high_score_count = len(df[df["score"] >= 70])
    
    cols = st.columns(5)
    with cols[0]:
        st.markdown(render_metric_card("🔥 本日掲載", f"{today_count}件", highlight=True, orange=True), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(render_metric_card("⚡ 昨日掲載", f"{yesterday_count}件"), unsafe_allow_html=True)
    with cols[2]:
        st.markdown(render_metric_card("🆕 1週間以内", f"{week_count}件"), unsafe_allow_html=True)
    with cols[3]:
        st.markdown(render_metric_card("⭐ 高スコア", f"{high_score_count}件"), unsafe_allow_html=True)
    with cols[4]:
        st.markdown(render_metric_card("📋 総求人数", f"{len(df)}件"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# クイックアクション
st.markdown('<p class="section-title">⚡ クイックアクション</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="company-card">
        <h3 style="color: {COLORS['navy']}; margin-top: 0;">📋 営業リスト</h3>
        <p style="color: {COLORS['text_muted']};">新着順・スコア順で求人を確認</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("営業リストを見る →", key="btn_list"):
        st.switch_page("pages/1_営業リスト.py")

with col2:
    st.markdown(f"""
    <div class="company-card">
        <h3 style="color: {COLORS['navy']}; margin-top: 0;">🏢 企業詳細</h3>
        <p style="color: {COLORS['text_muted']};">企業ごとの求人履歴を確認</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("企業詳細を見る →", key="btn_company"):
        st.switch_page("pages/2_企業詳細.py")

with col3:
    st.markdown(f"""
    <div class="company-card">
        <h3 style="color: {COLORS['navy']}; margin-top: 0;">✅ アクションボード</h3>
        <p style="color: {COLORS['text_muted']};">アプローチ状況を管理</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("アクションボードへ →", key="btn_action"):
        st.switch_page("pages/3_アクションボード.py")

st.markdown("<br>", unsafe_allow_html=True)

# 本日の注目求人
if "days_ago" in df.columns:
    today_df = df[df["days_ago"] == 0].sort_values("score", ascending=False).head(5)
    
    if not today_df.empty:
        st.markdown('<p class="section-title">🔥 本日の注目求人</p>', unsafe_allow_html=True)
        
        for _, row in today_df.iterrows():
            score = row.get("score", 0)
            company = row.get("company_name", "不明")
            title = row.get("job_title", "不明")
            emp_type = row.get("employment_type", "")
            
            st.markdown(f"""
            <div class="action-item">
                <strong style="color: {COLORS['navy']};">{company}</strong>
                <span style="background: {COLORS['orange']}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; margin-left: 8px;">{score}点</span>
                <br>
                <span style="color: {COLORS['text_muted']};">{title} / {emp_type}</span>
            </div>
            """, unsafe_allow_html=True)
