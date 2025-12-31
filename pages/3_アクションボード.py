"""
UI/UX求人レーダー - アクションボード
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.utils.io import load_jobs, apply_custom_css, render_metric_card, COLORS

st.set_page_config(
    page_title="アクションボード | UI/UX求人レーダー",
    page_icon="✅",
    layout="wide",
)

apply_custom_css()

# ヘッダー
st.markdown("""
<div class="main-header">
    <h1>✅ アクションボード</h1>
    <p>アプローチ状況を管理 → 成約につなげる</p>
</div>
""", unsafe_allow_html=True)

# データ読み込み
df = load_jobs()

if df.empty:
    st.error("❌ データが見つかりません")
    st.stop()

# セッションステートでアクション状況を管理
if "actions" not in st.session_state:
    st.session_state.actions = {}

# ステータス定義
STATUSES = {
    "未着手": {"color": COLORS["gray"], "icon": "⬜"},
    "アプローチ中": {"color": COLORS["orange"], "icon": "🟧"},
    "商談中": {"color": COLORS["navy"], "icon": "🟦"},
    "成約": {"color": COLORS["success"], "icon": "✅"},
    "見送り": {"color": COLORS["text_muted"], "icon": "⏸️"},
}

# サイドバー: フィルター
with st.sidebar:
    st.markdown("### 🔧 フィルター")
    
    # ステータスフィルター
    st.markdown("**ステータス**")
    selected_statuses = st.multiselect(
        "ステータス",
        list(STATUSES.keys()),
        default=["未着手", "アプローチ中", "商談中"],
        label_visibility="collapsed",
    )
    
    st.markdown("---")
    
    # スコアフィルター
    st.markdown("**最低スコア**")
    min_score = st.slider("最低スコア", 0, 100, 50, 10, label_visibility="collapsed")
    
    st.markdown("---")
    
    # 統計
    st.markdown("### 📊 統計")
    status_counts = {}
    for status in STATUSES.keys():
        count = sum(1 for v in st.session_state.actions.values() if v == status)
        status_counts[status] = count
    
    for status, count in status_counts.items():
        icon = STATUSES[status]["icon"]
        st.markdown(f"{icon} **{status}**: {count}件")

# メインエリア
st.markdown('<p class="section-title">📋 アクションリスト</p>', unsafe_allow_html=True)

# 優先度の高い順（スコア高 + 新着）でソート
priority_df = df.copy()
if "days_ago" in priority_df.columns:
    # 新着度を考慮したソート（スコア + 新着ボーナス）
    priority_df["priority"] = priority_df["score"] + (7 - priority_df["days_ago"].clip(0, 7)) * 2
    priority_df = priority_df.sort_values("priority", ascending=False)
else:
    priority_df = priority_df.sort_values("score", ascending=False)

# フィルター適用
filtered_df = priority_df[priority_df["score"] >= min_score].head(30)

# メトリクス
cols = st.columns(5)
with cols[0]:
    st.markdown(render_metric_card("📋 対象", f"{len(filtered_df)}件"), unsafe_allow_html=True)
with cols[1]:
    st.markdown(render_metric_card("⬜ 未着手", f"{status_counts.get('未着手', 0)}件"), unsafe_allow_html=True)
with cols[2]:
    st.markdown(render_metric_card("🟧 アプローチ中", f"{status_counts.get('アプローチ中', 0)}件", orange=True), unsafe_allow_html=True)
with cols[3]:
    st.markdown(render_metric_card("🟦 商談中", f"{status_counts.get('商談中', 0)}件"), unsafe_allow_html=True)
with cols[4]:
    st.markdown(render_metric_card("✅ 成約", f"{status_counts.get('成約', 0)}件", highlight=True), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# アクションリスト
for idx, row in filtered_df.iterrows():
    company = row.get("company_name", "不明")
    title = row.get("job_title", "不明")
    score = row.get("score", 0)
    url = row.get("url", "")
    hot_badge = row.get("hot_badge", "")
    posted_str = row.get("posted_date_str", "")
    
    # 現在のステータス取得
    job_key = f"{company}_{title}"
    current_status = st.session_state.actions.get(job_key, "未着手")
    
    # フィルター適用
    if current_status not in selected_statuses:
        continue
    
    status_info = STATUSES[current_status]
    
    # カード表示
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f"""
        <div class="action-item" style="border-left-color: {status_info['color']};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: {COLORS['navy']};">{company}</strong>
                    <span style="background: {COLORS['orange'] if score >= 70 else COLORS['gray']}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; margin-left: 8px;">{score}点</span>
                    <span style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin-left: 8px;">{hot_badge}</span>
                    <br>
                    <span style="color: {COLORS['text_muted']}; font-size: 0.9rem;">{title}</span>
                </div>
                <div>
                    <span style="background: {status_info['color']}; color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.8rem;">{status_info['icon']} {current_status}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        new_status = st.selectbox(
            "ステータス",
            list(STATUSES.keys()),
            index=list(STATUSES.keys()).index(current_status),
            key=f"select_{job_key}",
            label_visibility="collapsed",
        )
        if new_status != current_status:
            st.session_state.actions[job_key] = new_status
            st.rerun()

# 空の場合
if filtered_df.empty or all(st.session_state.actions.get(f"{row['company_name']}_{row['job_title']}", "未着手") not in selected_statuses for _, row in filtered_df.iterrows()):
    st.info("表示する求人がありません。フィルターを調整してください。")

