import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# --- 1. AIの設定 ---
# セキュリティ対策：Secretsから読み込み
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "あなたのAPIキーをここに" # ローカル用（secrets.tomlが優先されます）

genai.configure(api_key=api_key.strip(), transport='rest')

# --- 2. ドキュメント作成関数（エラー対策版） ---
def create_docx(content, shop_name):
    doc = Document()
    # 日本語を確実に扱うため、見出しや段落を追加
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

# サイドバー：ステップ管理
step = st.sidebar.radio("メニュー", ["Step 1: 基本情報", "Step 2: 収支分析", "Step 3: AI作成・保存"])

# セッション状態の初期化
if 'plan_text' not in st.session_state: st.session_state.plan_text = ""

# --- Step 1: 基本情報の入力 ---
if step == "Step 1: 基本情報":
    st.header("📋 Step 1: 基本情報の入力")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.industry = st.selectbox(
            "業種",["小売業", "飲食業", "サービス業", "建設業", "IT", "その他"], 
            index=0
        )
        # 「その他」の時の追加入力
        if st.session_state.industry == "その他":
            st.session_state.other_industry = st.text_input(
                "具体的な事業内容", 
                value=st.session_state.get('other_industry', ""),
                placeholder="例：出張ペット美容サービス"
            )
        else:
            st.session_state.other_industry = ""

        st.session_state.shop_name = st.text_input("屋号・会社名", value=st.session_state.get('shop_name', ""))
    
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
        fixed_costs = st.number_input("月額固定費（家賃・人件費など計：万円）", value=40)
        variable_rate = st.slider("原価率（％）", 0, 100, 30)

    marginal_rate = 1 - (variable_rate / 100)
    breakeven = fixed_costs / marginal_rate if marginal_rate > 0 else 0
    st.session_state.finance_data = {"status": status, "money": money_val, "unit": unit_price, "breakeven": breakeven}
    st.info(f"損益分岐点は、月間売上 **{breakeven:.1f} 万円** です。")

# --- Step 3: AI作成・保存 ---
elif step == "Step 3: AI作成・保存":
    st.header("📄 Step 3: 事業計画書の完成")
    
    if st.button("AIで事業計画書をフル生成"):
        with st.spinner("AIが清書しています..."):
            try:
                model = genai.GenerativeModel('gemini-flash-latest')
                f = st.session_state.finance_data
                
                # 業種名の設定
                ind_name = st.session_state.industry
                if ind_name == "その他" and st.session_state.other_industry:
                    ind_name = st.session_state.other_industry

                prompt = f"""
                あなたは{ind_name}のコンサルタントです。
                店名「{st.session_state.shop_name}」の事業計画書を作成してください。
                損益分岐点（月{f['breakeven']:.1f}万円）をどう超えるかの戦略を詳しく書き、
                最後は「以上」で終わらせてください。
                """
                response = model.generate_content(prompt)
                st.session_state.plan_text = response.text
                st.rerun()
            except Exception as e:
                st.error(f"エラー: {e}")

    if st.session_state.plan_text:
        st.markdown(st.session_state.plan_text)
        
        st.divider()
        st.subheader("📥 成果物のダウンロード")
        
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            # 💡 修正ポイント：テキスト保存時に encoding='utf-8' を指定
            st.download_button(
                label="📁 テキスト形式(.txt)で保存",
                data=st.session_state.plan_text.encode('utf-8'), # 確実にUTF-8でバイト変換
                file_name=f"{st.session_state.shop_name}_事業計画書.txt",
                mime="text/plain"
            )
            
        with col_dl2:
            # Wordデータの生成とダウンロード
            docx_data = create_docx(st.session_state.plan_text, st.session_state.shop_name)
            st.download_button(
                label="📄 Googleドキュメント形式(.docx)で保存",
                data=docx_data, # create_docx側で既に bytes になっている
                file_name=f"{st.session_state.shop_name}_事業計画書.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
