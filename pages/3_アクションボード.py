"""
UI/UX求人レーダー - アクションボード
"""

import sys
from datetime import date, datetime
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from src.utils.io import load_jobs, apply_custom_css, render_metric_card, COLORS

st.set_page_config(
    page_title="アクションボード | UI/UX求人レーダー",
    page_icon="✅",
    layout="wide",
)

apply_custom_css()

# === ステータス定義 ===
STATUSES = {
    "未着手": {"color": COLORS["gray"], "icon": "⬜", "order": 0},
    "連絡済": {"color": COLORS["orange"], "icon": "📧", "order": 1},
    "返信待ち": {"color": COLORS["warning"], "icon": "⏳", "order": 2},
    "商談化": {"color": COLORS["navy"], "icon": "🤝", "order": 3},
    "失注": {"color": COLORS["text_muted"], "icon": "❌", "order": 4},
}

# === セッションステート初期化 ===
if "watch_list" not in st.session_state:
    # {company_name: {status, memo, added_at, updated_at}}
    st.session_state.watch_list = {}

# ヘッダー
st.markdown("""
<div class="main-header">
    <h1>✅ アクションボード</h1>
    <p>ウォッチ企業を管理 → アプローチ状況をトラッキング</p>
</div>
""", unsafe_allow_html=True)

# データ読み込み
df = load_jobs()

if df.empty:
    st.error("❌ データが見つかりません")
    st.stop()

# === サイドバー: 企業追加 ===
with st.sidebar:
    st.markdown("### ➕ ウォッチリストに追加")
    
    # 未追加の企業リスト
    all_companies = sorted(df["company_name"].unique().tolist())
    unwatched = [c for c in all_companies if c not in st.session_state.watch_list]
    
    if unwatched:
        new_company = st.selectbox("企業を選択", unwatched, key="add_company")
        
        if st.button("➕ 追加", use_container_width=True):
            st.session_state.watch_list[new_company] = {
                "status": "未着手",
                "memo": "",
                "added_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            st.rerun()
    else:
        st.info("すべての企業を追加済みです")
    
    st.markdown("---")
    
    # 統計
    st.markdown("### 📊 ステータス別")
    status_counts = {s: 0 for s in STATUSES.keys()}
    for data in st.session_state.watch_list.values():
        status_counts[data["status"]] = status_counts.get(data["status"], 0) + 1
    
    for status, count in status_counts.items():
        info = STATUSES[status]
        st.markdown(f"{info['icon']} **{status}**: {count}件")
    
    st.markdown("---")
    st.markdown(f"**合計: {len(st.session_state.watch_list)}社**")

# === メインエリア ===

# メトリクス
cols = st.columns(5)
total = len(st.session_state.watch_list)
with cols[0]:
    st.markdown(render_metric_card("📋 ウォッチ中", f"{total}社"), unsafe_allow_html=True)
with cols[1]:
    st.markdown(render_metric_card("⬜ 未着手", f"{status_counts.get('未着手', 0)}社"), unsafe_allow_html=True)
with cols[2]:
    st.markdown(render_metric_card("📧 連絡済", f"{status_counts.get('連絡済', 0)}社", orange=True), unsafe_allow_html=True)
with cols[3]:
    st.markdown(render_metric_card("🤝 商談化", f"{status_counts.get('商談化', 0)}社", highlight=True), unsafe_allow_html=True)
with cols[4]:
    # 商談化率
    contacted = status_counts.get('連絡済', 0) + status_counts.get('返信待ち', 0) + status_counts.get('商談化', 0) + status_counts.get('失注', 0)
    rate = (status_counts.get('商談化', 0) / contacted * 100) if contacted > 0 else 0
    st.markdown(render_metric_card("📈 商談化率", f"{rate:.0f}%"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# フィルター
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown('<p class="section-title">📋 ウォッチリスト</p>', unsafe_allow_html=True)
with col2:
    filter_status = st.multiselect(
        "ステータスで絞り込み",
        list(STATUSES.keys()),
        default=list(STATUSES.keys()),
        label_visibility="collapsed",
    )

# ウォッチリストが空の場合
if not st.session_state.watch_list:
    st.info("👈 サイドバーから企業を追加してください")
    st.stop()

# ウォッチリスト表示
for company, data in sorted(
    st.session_state.watch_list.items(),
    key=lambda x: (STATUSES[x[1]["status"]]["order"], x[0])
):
    # フィルター
    if data["status"] not in filter_status:
        continue
    
    status_info = STATUSES[data["status"]]
    
    # 企業の求人情報取得
    company_df = df[df["company_name"] == company]
    job_count = len(company_df)
    avg_score = company_df["score"].mean() if not company_df.empty else 0
    top_job = company_df.sort_values("score", ascending=False).iloc[0] if not company_df.empty else None
    
    with st.container():
        st.markdown(f"""
        <div class="company-card" style="border-left: 4px solid {status_info['color']};">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h3 style="color: {COLORS['navy']}; margin: 0;">{status_info['icon']} {company}</h3>
                    <p style="color: {COLORS['text_muted']}; margin: 0.3rem 0; font-size: 0.9rem;">
                        求人: {job_count}件 / 平均スコア: {avg_score:.0f}点
                        {f" / 最新: {top_job['job_title']}" if top_job is not None else ""}
                    </p>
                </div>
                <span style="background: {status_info['color']}; color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.85rem;">
                    {data['status']}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 編集エリア
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            new_status = st.selectbox(
                "ステータス",
                list(STATUSES.keys()),
                index=list(STATUSES.keys()).index(data["status"]),
                key=f"status_{company}",
                label_visibility="collapsed",
            )
        
        with col2:
            new_memo = st.text_input(
                "メモ",
                value=data["memo"],
                placeholder="メモを入力...",
                key=f"memo_{company}",
                label_visibility="collapsed",
            )
        
        with col3:
            if st.button("🗑️", key=f"delete_{company}", help="削除"):
                del st.session_state.watch_list[company]
                st.rerun()
        
        # 変更があれば更新
        if new_status != data["status"] or new_memo != data["memo"]:
            st.session_state.watch_list[company]["status"] = new_status
            st.session_state.watch_list[company]["memo"] = new_memo
            st.session_state.watch_list[company]["updated_at"] = datetime.now().isoformat()
        
        st.markdown("<hr style='margin: 0.5rem 0; border-color: #eee;'>", unsafe_allow_html=True)

# === CSVダウンロード ===
st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.watch_list:
    # CSV用データ作成
    csv_data = []
    for company, data in st.session_state.watch_list.items():
        company_df = df[df["company_name"] == company]
        avg_score = company_df["score"].mean() if not company_df.empty else 0
        job_count = len(company_df)
        
        csv_data.append({
            "企業名": company,
            "ステータス": data["status"],
            "メモ": data["memo"],
            "求人数": job_count,
            "平均スコア": round(avg_score, 1),
            "追加日": data["added_at"][:10],
            "更新日": data["updated_at"][:10],
        })
    
    csv_df = pd.DataFrame(csv_data)
    csv_str = csv_df.to_csv(index=False, encoding="utf-8-sig")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.download_button(
            "📥 CSVダウンロード",
            csv_str,
            f"watch_list_{date.today().isoformat()}.csv",
            "text/csv",
            use_container_width=True,
        )
    with col2:
        if st.button("🗑️ 全削除", use_container_width=True):
            st.session_state.watch_list = {}
            st.rerun()
