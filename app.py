import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# --- 1. AIの設定 ---
# キーの取得（セキュリティ対応）
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "" # ローカルPC用

genai.configure(api_key=api_key.strip(), transport='rest')

# --- 2. Word作成関数（確実にUTF-8で処理） ---
def create_docx(content, shop_name_ascii):
    doc = Document()
    doc.add_heading(f"Business Plan: {shop_name_ascii}", 0)
    for line in content.split('\n'):
        if line.strip():
            doc.add_paragraph(line.strip())
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 3. 画面構成（日本語を極力排除したID管理） ---
st.set_page_config(page_title="BizPlan-Kit", layout="wide")
st.title("Business Plan Generator")

# 💡 ID（key）を全て英語に固定することでエラーを回避します
step = st.sidebar.radio("Step", ["S1", "S2", "S3"], key="main_step")

if 'plan_text' not in st.session_state:
    st.session_state.plan_text = ""

# --- Step 1 ---
if step == "S1":
    st.header("Step 1: Input Info")
    # 💡 内部的な値（index）で管理
    ind_list = ["Retail", "Food", "Service", "Construction", "IT", "Other"]
    st.selectbox("Select Industry", ind_list, key="industry_choice")
    st.text_input("Business Name (Alphabet recommended)", key="shop_name_input")
    st.text_area("Target / Details", key="target_input")
    st.text_area("Strength", key="strength_input")

# --- Step 2 ---
elif step == "S2":
    st.header("Step 2: Simulation")
    st.number_input("Investment (10k Yen)", value=500, key="val_money")
    st.number_input("Price (Yen)", value=1000, key="val_price")
    st.number_input("Monthly Fixed Cost (10k Yen)", value=30, key="val_fixed")
    st.slider("Cost Rate (%)", 0, 100, 30, key="val_rate")

# --- Step 3 ---
elif step == "S3":
    st.header("Step 3: Generate")
    
    # 💡 ボタンのラベルとキーを英語に
    if st.button("Generate Now", key="gen_btn"):
        with st.spinner("AI is generating..."):
            try:
                # 必要な情報を取得（空ならデフォルト値）
                s_name = st.session_state.get('shop_name_input', 'My Business')
                s_ind = st.session_state.get('industry_choice', 'Business')
                s_target = st.session_state.get('target_input', '')
                s_strength = st.session_state.get('strength_input', '')
                
                model = genai.GenerativeModel('gemini-flash-latest')
                
                # 指示（プロンプト）は日本語でも、本体の通信に載るのでOK
                prompt = f"あなたは{s_ind}のプロです。店名「{s_name}」の事業計画書を日本語で詳しく作成し、最後に「以上」で終わらせてください。ターゲット:{s_target}、強み:{s_strength}。"
                
                response = model.generate_content(prompt)
                st.session_state.plan_text = response.text
                
            except Exception as e:
                st.error(f"Generation Error: {e}")

    # 生成結果の表示
    if st.session_state.plan_text:
        st.markdown(st.session_state.plan_text)
        
        st.divider()
        try:
            # 安全なファイル名の生成（英数字のみ）
            raw_name = st.session_state.get('shop_name_input', 'plan')
            safe_filename = "".join([c for c in raw_name if c.isalnum()]) or "plan"

            # データの準備
            docx_data = create_docx(st.session_state.plan_text, safe_filename)

            # 💡 ダウンロードボタンも英語に
            st.download_button(
                label="Download Word File",
                data=docx_data,
                file_name=f"{safe_filename}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="download_btn"
            )
        except Exception as e:
            st.error(f"Prepare Error: {e}")
