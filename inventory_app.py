import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. 設定
JSON_KEYFILE = r"C:\Users\mish-\OneDrive\Documents\GenAI\在庫管理\crucial-limiter-485602-b3-ee3cb1b718c9.json"
# スプレッドシートのURLが https://docs.google.com/spreadsheets/d/◯◯◯/edit の場合、◯◯◯の部分です
SPREADSHEET_ID = "1Iowg-r5FoR2G0AcdtzDMClWKtuZJSeirDEppgXCdY7U"

# 2. データの読み込み
def connect_to_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
    client = gspread.authorize(creds)
    # 1番目のシートを開く
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

def load_data(sheet):
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# アプリの見た目設定
st.set_page_config(page_title="在庫管理システム", layout="centered")
st.title("📦 在庫管理 (Spreadsheet連携)")

# スプレッドシートに接続
try:
    sheet = connect_to_sheet()
    df = load_data(sheet)
except Exception as e:
    st.error(f"スプレッドシートに接続できませんでした。IDや共有設定を確認してください。")
    st.write(f"エラー内容: {e}")
    st.stop()

# --- 在庫0アラート ---
out_of_stock = df[df["在庫数"] == 0]
if not out_of_stock.empty:
    st.subheader("🚨 買い出しが必要")
    for _, row in out_of_stock.iterrows():
        st.error(f"‼️ **在庫切れ**：{row['商品名']} ({row['カテゴリー']})")
st.divider()

# --- カテゴリーごとに表示 ---
categories = df["カテゴリー"].unique()

for cat in categories:
    with st.expander(f"📂 {cat}", expanded=True):
        category_df = df[df["カテゴリー"] == cat]
        
        for index, row in category_df.iterrows():
            # スプレッドシート上の行番号（見出し1行＋0始まりインデックス+1）
            # データフレームのindexを使って元の行を特定します
            original_row_idx = index + 2
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                if row["在庫数"] == 0:
                    st.markdown(f":red[**{row['商品名']}**]")
                else:
                    st.write(row["商品名"])
            
            with col2:
                st.write(f"**{row['在庫数']}**")

            with col3:
                if st.button("－1", key=f"min_{index}"):
                    new_val = max(0, int(row["在庫数"]) - 1)
                    sheet.update_cell(original_row_idx, 3, new_val) # 3列目(在庫数)を更新
                    st.rerun()

            with col4:
                if st.button("＋1", key=f"plus_{index}"):
                    new_val = int(row["在庫数"]) + 1
                    sheet.update_cell(original_row_idx, 3, new_val)
                    st.rerun()
    st.write("") # カテゴリー間の余白
    