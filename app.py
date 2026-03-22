import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# --- 1. AIの設定 ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "あなたのAPIキーをここに"

genai.configure(api_key=api_key.strip(), transport='rest')

# --- 2. ドキュメント作成関数（確実に bytes を返す） ---
def create_docx(content, shop_name):
    doc = Document()
    # 内容には日本語を使っても大丈夫です
    doc.add_heading(f"{shop_name} Business Plan", 0)
    for line in content.split('\n'):
        text = line.strip()
        if not text:
            continue
        if text.startswith('###'):
            doc.add_heading(text.replace('###', '').strip(), level=2)
        elif text.startswith('##'):
            doc.add_heading(text.replace('##', '').strip(), level=1)
        else:
            doc.add_paragraph(text)
    
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 3. 画面構成 ---
st.set_page_config(page_title="Business Plan Maker", layout="wide")
st.title("🚀 Business Plan Generator") # 日本語を避けてみる

step = st.sidebar.radio("Menu", ["Step 1", "Step 2", "Step 3"])

if 'plan_text' not in st.session_state: 
    st.session_state.plan_text = ""

# --- Step 1 ---
if step == "Step 1":
    st.header("Step 1: Basic Info")
    st.session_state.industry = st.selectbox("Industry", ["Retail", "Food", "Service", "Construction", "IT", "Other"])
    st.session_state.shop_name = st.text_input("Shop Name", value=st.session_state.get('shop_name', "My Business"))
    st.session_state.target = st.text_area("Target Customer")
    st.session_state.strength = st.text_area("Strength")

# --- Step 2 ---
elif step == "Step 2":
    st.header("Step 2: Simulation")
    money_val = st.number_input("Investment (10k Yen)", value=500)
    unit_price = st.number_input("Unit Price (Yen)", value=2000)
    fixed_costs = st.number_input("Fixed Cost (10k Yen)", value=40)
    variable_rate = st.slider("Cost Rate (%)", 0, 100, 30)

    m_rate = 1 - (variable_rate / 100)
    breakeven = fixed_costs / m_rate if m_rate > 0 else 0
    st.session_state.finance_data = {"unit": unit_price, "breakeven": breakeven}
    st.info(f"Breakeven Sales: {breakeven:.1f} (10k Yen/Month)")

# --- Step 3 ---
elif step == "Step 3":
    st.header("Step 3: Generate")
    
    # 💡 ボタンのラベルを英語に変更
    if st.button("Generate Business Plan"):
        with st.spinner("AI is thinking..."):
            try:
                model = genai.GenerativeModel('gemini-flash-latest')
                f = st.session_state.get('finance_data', {"breakeven": 0})
                
                # 指示は日本語で送っても大丈夫です
                prompt = f"あなたはプロのコンサルタントです。店名「{st.session_state.shop_name}」の事業計画書を日本語で詳しく作成し、最後に「以上」で終わらせてください。損益分岐点{f['breakeven']:.1f}万円への言及も含めてください。"
                
                response = model.generate_content(prompt)
                st.session_state.plan_text = response.text
                # st.rerun() は使わずに自然に表示させる
                
            except Exception as e:
                st.error(f"Error: {e}")

    # 結果の表示
    if st.session_state.plan_text:
        st.markdown(st.session_state.plan_text)
        
        st.divider()
        st.subheader("Download Results")

        try:
            # 💡 データの変換
            text_bytes = st.session_state.plan_text.encode('utf-8')
            docx_bytes = create_docx(st.session_state.plan_text, st.session_state.shop_name)

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                # 💡 ラベルとファイル名を完全に英語にする
                st.download_button(
                    label="Download as Text",
                    data=text_bytes,
                    file_name="plan.txt",
                    mime="text/plain",
                    key="txt_dl"
                )
            with col_dl2:
                # 💡 ラベルとファイル名を完全に英語にする
                st.download_button(
                    label="Download as Word",
                    data=docx_bytes,
                    file_name="plan.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="docx_dl"
                )
        except Exception as e:
            st.error(f"Download Error: {e}")
