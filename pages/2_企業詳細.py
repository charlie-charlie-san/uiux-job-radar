"""
UI/UX求人レーダー - 企業詳細
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.utils.io import load_jobs, apply_custom_css, COLORS

st.set_page_config(
    page_title="企業詳細 | UI/UX求人レーダー",
    page_icon="🏢",
    layout="wide",
)

apply_custom_css()

# ヘッダー
st.markdown("""
<div class="main-header">
    <h1>🏢 企業詳細</h1>
    <p>企業ごとの求人履歴・スコア傾向を確認</p>
</div>
""", unsafe_allow_html=True)

# データ読み込み
df = load_jobs()

if df.empty:
    st.error("❌ データが見つかりません")
    st.stop()

# 企業リスト作成
company_stats = df.groupby("company_name").agg({
    "score": ["mean", "max", "count"],
    "job_title": "first",
}).reset_index()
company_stats.columns = ["company_name", "avg_score", "max_score", "job_count", "latest_job"]
company_stats = company_stats.sort_values("avg_score", ascending=False)

# サイドバー: 企業選択
with st.sidebar:
    st.markdown("### 🏢 企業を選択")
    
    # 検索
    search_query = st.text_input("🔍 企業名で検索", "")
    
    if search_query:
        filtered_companies = company_stats[company_stats["company_name"].str.contains(search_query, case=False, na=False)]
    else:
        filtered_companies = company_stats
    
    st.markdown("---")
    st.markdown(f"**{len(filtered_companies)}社** が見つかりました")
    
    # 企業リスト
    selected_company = None
    for _, row in filtered_companies.head(15).iterrows():
        company = row["company_name"]
        avg_score = row["avg_score"]
        job_count = row["job_count"]
        
        if st.button(f"📍 {company[:15]}... ({avg_score:.0f}点)", key=f"btn_{company}", use_container_width=True):
            selected_company = company

# メインエリア
if selected_company is None and not filtered_companies.empty:
    selected_company = filtered_companies.iloc[0]["company_name"]

if selected_company:
    company_df = df[df["company_name"] == selected_company].sort_values("posted_date", ascending=False)
    company_info = company_stats[company_stats["company_name"] == selected_company].iloc[0]
    
    # 企業サマリー
    st.markdown(f'<p class="section-title">📊 {selected_company}</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("求人数", f"{int(company_info['job_count'])}件")
    with col2:
        st.metric("平均スコア", f"{company_info['avg_score']:.1f}")
    with col3:
        st.metric("最高スコア", f"{int(company_info['max_score'])}")
    with col4:
        if "days_ago" in company_df.columns:
            recent = company_df[company_df["days_ago"] <= 7]
            st.metric("直近1週間", f"{len(recent)}件")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 求人一覧
    st.markdown(f'<p class="section-title">📋 求人一覧</p>', unsafe_allow_html=True)
    
    for _, row in company_df.iterrows():
        score = row.get("score", 0)
        title = row.get("job_title", "不明")
        emp_type = row.get("employment_type", "")
        remote = row.get("remote_type", "")
        skills = row.get("skills_text", "")
        url = row.get("url", "")
        hot_badge = row.get("hot_badge", "")
        posted_str = row.get("posted_date_str", "")
        
        # スコアバッジの色
        if score >= 80:
            badge_color = COLORS['orange']
        elif score >= 60:
            badge_color = COLORS['navy']
        else:
            badge_color = COLORS['text_muted']
        
        st.markdown(f"""
        <div class="company-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h4 style="color: {COLORS['navy']}; margin: 0 0 0.5rem 0;">{title}</h4>
                    <p style="color: {COLORS['text_muted']}; margin: 0; font-size: 0.9rem;">
                        {emp_type} {' / ' + remote if remote and remote != 'unknown' else ''}
                    </p>
                    {f'<p style="color: {COLORS["text_muted"]}; margin: 0.5rem 0 0 0; font-size: 0.85rem;">🛠 {skills}</p>' if skills else ''}
                </div>
                <div style="text-align: right;">
                    <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 16px; font-weight: 600;">{score}点</span>
                    <p style="color: {COLORS['text_muted']}; margin: 0.5rem 0 0 0; font-size: 0.8rem;">{hot_badge} {posted_str}</p>
                </div>
            </div>
            {f'<a href="{url}" target="_blank" style="color: {COLORS["orange"]}; font-size: 0.85rem;">🔗 求人ページを見る</a>' if url else ''}
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("左のサイドバーから企業を選択してください")

