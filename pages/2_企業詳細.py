"""
UI/UX求人レーダー - 企業詳細
"""

import sys
from datetime import date
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
    <p>企業ごとの求人確認 → 提案文を生成</p>
</div>
""", unsafe_allow_html=True)

# データ読み込み
df = load_jobs()

if df.empty:
    st.error("❌ データが見つかりません")
    st.stop()

# 企業リスト作成
company_list = sorted(df["company_name"].unique().tolist())

# === サイドバー ===
with st.sidebar:
    st.markdown("### 🏢 企業を選択")
    selected_company = st.selectbox(
        "企業名",
        company_list,
        index=0,
        label_visibility="collapsed",
    )
    
    st.markdown("---")
    
    # 選択中の企業の統計
    company_df = df[df["company_name"] == selected_company].sort_values("score", ascending=False)
    
    st.markdown(f"**{selected_company}**")
    st.markdown(f"- 求人数: **{len(company_df)}件**")
    st.markdown(f"- 平均スコア: **{company_df['score'].mean():.1f}**")
    st.markdown(f"- 最高スコア: **{company_df['score'].max()}**")

# === メインエリア ===
col_left, col_right = st.columns([1, 1])

# --- 左カラム: 求人一覧 ---
with col_left:
    st.markdown(f'<p class="section-title">📋 {selected_company} の求人一覧</p>', unsafe_allow_html=True)
    
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
        </div>
        """, unsafe_allow_html=True)

# --- 右カラム: 提案文生成 ---
with col_right:
    st.markdown('<p class="section-title">✍️ 提案文を生成</p>', unsafe_allow_html=True)
    
    # 入力フォーム
    st.markdown(f"**担当者ロール**")
    role_options = ["採用責任者", "プロダクト責任者", "デザインマネージャー", "人事担当", "その他"]
    target_role = st.selectbox("担当者ロール", role_options, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"**提案テーマ**")
    theme_options = [
        "デザインシステム整備",
        "UXリサーチ・ユーザーインタビュー",
        "プロトタイピング・UI設計",
        "プロダクトデザイン全般",
        "デザイン組織立ち上げ支援",
    ]
    proposal_theme = st.selectbox("提案テーマ", theme_options, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"**稼働イメージ**")
    workstyle_options = [
        "週5常駐、長期",
        "週3-4常駐、3ヶ月〜",
        "週2-3リモート併用、3ヶ月〜",
        "フルリモート、スポット対応",
        "プロジェクト単位（1-2ヶ月）",
    ]
    workstyle = st.selectbox("稼働イメージ", workstyle_options, label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 生成ボタン
    if st.button("📝 提案文を生成", type="primary", use_container_width=True):
        # 求人情報から抽出
        top_job = company_df.iloc[0] if not company_df.empty else None
        job_title = top_job.get("job_title", "UI/UXデザイナー") if top_job is not None else "UI/UXデザイナー"
        skills_list = top_job.get("skills", []) if top_job is not None else []
        skills_str = "、".join(skills_list[:3]) if skills_list else "Figma、デザインシステム"
        
        # テンプレート生成
        proposal_text = f"""【ご提案】{selected_company}様 {proposal_theme}のご支援

{target_role}様

突然のご連絡失礼いたします。
UI/UXデザイナーの派遣・業務委託を行っております、○○株式会社の△△と申します。

貴社にて「{job_title}」を募集されているのを拝見し、
ぜひ弊社のデザイナーをご紹介できればと思い、ご連絡いたしました。

■ ご提案内容
・テーマ：{proposal_theme}
・稼働：{workstyle}
・対応可能スキル：{skills_str} など

■ 弊社デザイナーの強み
・プロダクト開発経験豊富なシニアデザイナーが多数在籍
・{proposal_theme}の実績多数
・即戦力として早期立ち上げが可能

ご興味をお持ちいただけましたら、
候補者のポートフォリオをお送りさせていただきます。

まずは15分程度のオンラインMTGにて、
貴社のご状況をお伺いできればと存じます。

ご検討のほど、よろしくお願いいたします。

---
○○株式会社
△△（担当者名）
TEL: 03-XXXX-XXXX
Email: xxx@example.com
"""
        
        st.session_state.generated_proposal = proposal_text
    
    # 生成結果表示
    if "generated_proposal" in st.session_state:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**生成された提案文**")
        st.text_area(
            "提案文",
            st.session_state.generated_proposal,
            height=400,
            label_visibility="collapsed",
        )
        st.caption("💡 上のテキストエリアをクリックして Cmd+A → Cmd+C でコピーできます")
