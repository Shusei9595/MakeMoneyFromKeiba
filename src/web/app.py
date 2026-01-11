"""
競馬AI予測システム - Web UI

Streamlitを使用したブラウザベースのインターフェース
"""
import streamlit as st
from pathlib import Path

# ページ設定
st.set_page_config(
    page_title="競馬AI予測システム",
    page_icon="🐴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# タイトル
st.markdown('<p class="main-header">🐴 競馬AI予測システム</p>', unsafe_allow_html=True)
st.markdown("---")

# サイドバー
with st.sidebar:
    st.header("📊 システム情報")
    
    # モデル状態確認
    models_dir = Path("models")
    if models_dir.exists():
        model_files = list(models_dir.glob("*.pkl"))
        st.metric("訓練済みモデル", f"{len(model_files)}/9")
    else:
        st.warning("モデルが見つかりません")
    
    # データ状態確認
    data_dir = Path("data/processed")
    if data_dir.exists():
        data_files = list(data_dir.glob("*.csv"))
        st.metric("処理済みデータ", f"{len(data_files)} ファイル")
    else:
        st.info("データは未処理です")
    
    st.markdown("---")
    st.markdown("""
    ### 📚 ナビゲーション
    左のメニューからページを選択してください。
    """)

# ホーム画面
st.header("ようこそ")
st.markdown("""
このシステムは、**9つの専門家AI**が協調して競馬予測を行う高度なシステムです。

### 🎯 特徴
- **マルチエージェントアーキテクチャ**: 各エージェントが専門分野を担当
- **期待値ベースの賭け推奨**: プラスEV（期待値）の賭けのみを推奨
- **柔軟な戦略選択**: 保守的・バランス型・積極的の3種類

### 📖 使い方
1. **データ収集**: netkeiba.comからレースデータを収集
2. **前処理**: データをクリーニング・特徴量エンジニアリング
3. **訓練**: 9つの専門家AIを訓練
4. **予測**: レース結果を予測し、推奨買い目を生成
5. **バックテスト**: 過去データで戦略を検証
""")

# クイックアクション
st.markdown("---")
st.header("🚀 クイックアクション")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📊 データ管理")
    st.markdown("データの収集・前処理を行います。")
    if st.button("データ収集ページへ", key="btn_collect"):
        st.switch_page("pages/1_データ収集.py")

with col2:
    st.subheader("🎯 予測実行")
    st.markdown("レースの予測を実行します。")
    if st.button("予測ページへ", key="btn_predict"):
        st.switch_page("pages/3_予測.py")

with col3:
    st.subheader("📈 バックテスト")
    st.markdown("戦略の検証を行います。")
    if st.button("バックテストページへ", key="btn_backtest"):
        st.switch_page("pages/4_バックテスト.py")

# フッター
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit | v1.0.0")
