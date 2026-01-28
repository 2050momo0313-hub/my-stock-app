import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. 設定 ---
SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]

# --- 2. データの読み込み ---
def connect_to_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        info = st.secrets["gcp_service_account"]
        ss_id = st.secrets["SPREADSHEET_ID"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(ss_id).sheet1
        return sheet
    except Exception as e:
        st.error(f"接続エラー: {e}")
        return None

def load_data(sheet):
    if sheet is None: return pd.DataFrame()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# --- アプリの見た目設定 ---
st.set_page_config(page_title="お買い物のリスト", layout="centered")

# スマホでタイトルの余白を削るカスタムCSS
st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 10px; height: 3em; }
    .reportview-container .main .block-container { padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("📦 お買い物リスト")

# スプレッドシートに接続
try:
    sheet = connect_to_sheet()
    df = load_data(sheet)
except Exception as e:
    st.error(f"スプレッドシートに接続できませんでした。")
    st.stop()

# --- 在庫0アラート ---
out_of_stock = df[df["在庫数"] == 0]
if not out_of_stock.empty:
    with st.container():
        st.subheader("🚨 買うもの")
        for _, row in out_of_stock.iterrows():
            st.warning(f"🛒 **{row['商品名']}** ({row['カテゴリー']})")
st.divider()

# --- カテゴリーごとに表示 ---
categories = df["カテゴリー"].unique()

for cat in categories:
    with st.expander(f"📂 {cat}", expanded=False):
        category_df = df[df["カテゴリー"] == cat]
        
        for index, row in category_df.iterrows():
            original_row_idx = index + 2
            
            # --- ここからスマホ最適化レイアウト ---
            # 1行目: 商品名と在庫数
            c1, c2 = st.columns([3, 1])
            with c1:
                if row["在庫数"] == 0:
                    st.markdown(f"### :red[{row['商品名']}]")
                else:
                    st.markdown(f"### {row['商品名']}")
            with c2:
                st.markdown(f"<h3 style='text-align: right;'>{row['在庫数']}</h3>", unsafe_allow_html=True)

            # 2行目: 操作ボタン（マイナスとプラスを大きく配置）
            b1, b2 = st.columns(2)
            with b1:
                if st.button(f"➖ 減らす", key=f"min_{index}"):
                    new_val = max(0, int(row["在庫数"]) - 1)
                    sheet.update_cell(original_row_idx, 3, new_val)
                    st.rerun()
            with b2:
                if st.button(f"➕ 増やす", key=f"plus_{index}"):
                    new_val = int(row["在庫数"]) + 1
                    sheet.update_cell(original_row_idx, 3, new_val)
                    st.rerun()
            
            st.markdown("---") # 商品ごとの区切り線

    st.write("")

