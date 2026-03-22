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
    doc.add_heading(f"{shop_name} 事業計画書", 0)
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
st.set_page_config(page_title="事業計画書作成楽楽キット", page_icon="📝", layout="wide")
st.title("🚀 事業計画書作成楽楽キット")

step = st.sidebar.radio("メニュー", ["Step 1: 基本情報", "Step 2: 収支分析", "Step 3: AI作成・保存"])

if 'plan_text' not in st.session_state: 
    st.session_state.plan_text = ""

# --- Step 1: 基本情報の入力 ---
if step == "Step 1: 基本情報":
    st.header("📋 Step 1: 基本情報の入力")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.industry = st.selectbox("業種", ["小売業", "飲食業", "サービス業", "建設業", "IT", "その他"])
        if st.session_state.industry == "その他":
            st.session_state.other_industry = st.text_input("具体的な事業内容", value=st.session_state.get('other_industry', ""))
        else:
            st.session_state.other_industry = ""
        st.session_state.shop_name = st.text_input("屋号・会社名", value=st.session_state.get('shop_name', "My Business"))
    with col2:
        st.session_state.target = st.text_area("ターゲット顧客", value=st.session_state.get('target', ""))
        st.session_state.strength = st.text_area("独自の強み", value=st.session_state.get('strength', ""))

# --- Step 2: 収支分析 ---
elif step == "Step 2: 収支分析":
    st.header("💰 Step 2: 収支シミュレーション")
    status = st.radio("現在の状況", ["起業の準備中", "既に事業を行っている"])
    col1, col2 = st.columns(2)
    with col1:
        money_val = st.number_input("初期投資額 または 借入額（万円）", value=500)
        unit_price = st.number_input("想定客単価（円）", value=2000)
    with col2:
        fixed_costs = st.number_input("月額固定費（万円）", value=40)
        variable_rate = st.slider("原価率（％）", 0, 100, 30)

    m_rate = 1 - (variable_rate / 100)
    breakeven = fixed_costs / m_rate if m_rate > 0 else 0
    st.session_state.finance_data = {"status": status, "money": money_val, "unit": unit_price, "breakeven": breakeven}
    st.info(f"損益分岐点: 月間売上 {breakeven:.1f} 万円")

# --- Step 3: AI作成・保存 ---
elif step == "Step 3: AI作成・保存":
    st.header("📄 Step 3: 事業計画書の完成")
    
    if st.button("AIで事業計画書をフル生成"):
        with st.spinner("AIが執筆中..."):
            try:
                model = genai.GenerativeModel('gemini-flash-latest')
                f = st.session_state.finance_data
                ind = st.session_state.other_industry if st.session_state.industry == "その他" else st.session_state.industry
                prompt = f"あなたは{ind}のコンサルタントです。店名「{st.session_state.shop_name}」の事業計画書を詳細に作成してください。損益分岐点{f['breakeven']:.1f}万円への言及も含め、最後に「以上」で終わらせてください。"
                response = model.generate_content(prompt)
                st.session_state.plan_text = response.text
                st.rerun()
            except Exception as e:
                st.error(f"エラー: {e}")

    if st.session_state.plan_text:
        st.markdown(st.session_state.plan_text)
        st.divider()
        st.subheader("📥 ダウンロード（Googleドキュメント・Word対応）")

        try:
            # 💡 エラー回避の核心：
            # 1. データを bytes 型に変換
            # 2. 【最重要】file_name に日本語を使わず、半角英数字（plan.docx）にする
            
            text_bytes = st.session_state.plan_text.encode('utf-8')
            docx_bytes = create_docx(st.session_state.plan_text, st.session_state.shop_name)

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="📁 テキスト形式で保存",
                    data=text_bytes,
                    file_name="plan.txt",  # 日本語を避ける
                    mime="text/plain",
                    key="txt_download"
                )
            with col_dl2:
                st.download_button(
                    label="📄 Googleドキュメント形式で保存",
                    data=docx_bytes,
                    file_name="plan.docx", # 日本語を避ける
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="docx_download"
                )
            st.info("※保存時のファイル名は 'plan' になります。保存後に必要に応じて名前を変更してください。")
            
        except Exception as e:
            st.error(f"ダウンロード準備エラー: {e}")
