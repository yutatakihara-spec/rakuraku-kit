import streamlit as st
import google.generativeai as genai
from docx import Document
from io import BytesIO

# --- 1. AIの設定（セキュリティ対策版） ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = "" # ローカルPC用

genai.configure(api_key=api_key.strip(), transport='rest')

# --- 2. Word作成関数（確実に動作する設定） ---
def create_docx(content, shop_name):
    doc = Document()
    # 内容は日本語でOK
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

# --- 3. 画面構成（ワイドモード設定済み） ---
st.set_page_config(page_title="事業計画書作成楽楽キット", page_icon="📝", layout="wide")
st.title("🚀 事業計画書作成楽楽キット")

# サイドバー：日本語表示、内部キーは英語
step = st.sidebar.radio(
    "メニュー", 
    ["Step 1: 基本情報", "Step 2: 収支分析", "Step 3: 計画書作成"], 
    key="main_step"
)

if 'plan_text' not in st.session_state: 
    st.session_state.plan_text = ""

# --- Step 1: 基本情報の入力 ---
if step == "Step 1: 基本情報":
    st.header("📋 Step 1: 基本情報の入力")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.industry = st.selectbox(
            "業種を選択", 
            ["小売業", "飲食業", "サービス業", "建設業", "IT", "その他"], 
            key="ind_select"
        )
        # 「その他」の追加入力
        if st.session_state.industry == "その他":
            st.session_state.other_industry = st.text_input("具体的な事業内容", key="other_ind_input")
        else:
            st.session_state.other_industry = ""
            
        st.session_state.shop_name = st.text_input("屋号・会社名", value=st.session_state.get('shop_name', ""), key="sn_input")
        
    with col2:
        st.session_state.target = st.text_area("ターゲット顧客", key="tg_input")
        st.session_state.strength = st.text_area("独自の強み", key="st_input")

# --- Step 2: 収支分析 ---
elif step == "Step 2: 収支分析":
    st.header("💰 Step 2: 収支シミュレーション")
    col1, col2 = st.columns(2)
    with col1:
        money_val = st.number_input("初期投資額 または 借入額（万円）", value=500, key="v_money")
        unit_price = st.number_input("想定客単価（円）", value=2000, key="v_price")
    with col2:
        fixed_costs = st.number_input("月額固定費（家賃・人件費など計：万円）", value=40, key="v_fixed")
        variable_rate = st.slider("原価率（％）", 0, 100, 30, key="v_rate")

    # 損益分岐点計算
    m_rate = 1 - (variable_rate / 100)
    breakeven = fixed_costs / m_rate if m_rate > 0 else 0
    st.session_state.finance_data = {"unit": unit_price, "breakeven": breakeven}
    st.info(f"あなたのビジネスの損益分岐点は、月間売上 **{breakeven:.1f} 万円** です。")

# --- Step 3: AI作成・保存 ---
elif step == "Step 3: 計画書作成":
    st.header("📄 Step 3: 事業計画書の完成")
    
    # 💡 ボタンの表示は日本語、動作は安定版
    if st.button("AIで事業計画書をフル生成する", key="gen_button"):
        if not st.session_state.get('shop_name'):
            st.error("Step 1 で店名を入力してください。")
        else:
            with st.spinner("AIコンサルタントが執筆中..."):
                try:
                    # 確実に動くモデル名を使用
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    f = st.session_state.get('finance_data', {"breakeven": 0})
                    ind = st.session_state.other_industry if st.session_state.industry == "その他" else st.session_state.industry
                    
                    prompt = f"""
                    あなたは{ind}のコンサルタントです。店名「{st.session_state.shop_name}」の事業計画書を日本語で作成してください。
                    ターゲット顧客、競合優位性、集客戦略、そして損益分岐点{f['breakeven']:.1f}万円を突破するためのアドバイスを詳しく書き、最後に「以上」で終わらせてください。
                    """
                    response = model.generate_content(prompt)
                    st.session_state.plan_text = response.text
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    # 結果の表示
    if st.session_state.plan_text:
        st.success("事業計画書の作成が完了しました！")
        st.markdown("---")
        st.markdown(st.session_state.plan_text)
        
        st.divider()
        st.subheader("📥 成果物のダウンロード")
        
        try:
            # データのバイナリ化（日本語エラー対策）
            docx_data = create_docx(st.session_state.plan_text, st.session_state.shop_name)

            # 💡 ファイル名だけはエラー回避のため英語（plan.docx）のままにします
            st.download_button(
                label="📄 Googleドキュメント形式で保存",
                data=docx_data,
                file_name="plan.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_btn"
            )
            st.caption("※保存したファイルを開けば、GoogleドキュメントやWordで編集可能です。")
        except Exception as e:
            st.error(f"ダウンロード準備中にエラー: {e}")
