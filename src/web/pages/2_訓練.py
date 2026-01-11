"""
訓練ページ
"""
import streamlit as st
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="訓練 - 競馬AI", page_icon="🧠", layout="wide")

st.title("🧠 モデル訓練")

st.markdown("""
9つの専門家AIを訓練します。
訓練データを指定して、各エージェントのモデルを構築します。
""")

# エージェント情報
AGENTS = {
    'past_performance': {'name': '過去成績分析AI', 'weight': '20%', 'description': '直近成績・調子トレンド'},
    'distance': {'name': '距離適性分析AI', 'weight': '15%', 'description': '距離とコースの相性'},
    'jockey_trainer': {'name': '騎手・調教師分析AI', 'weight': '15%', 'description': '人的要因の分析'},
    'pedigree': {'name': '血統分析AI', 'weight': '10%', 'description': '血統からの適性判断'},
    'pace': {'name': 'レースペース分析AI', 'weight': '12%', 'description': 'ペース予測・展開予想'},
    'physical': {'name': '馬体・コンディション分析AI', 'weight': '8%', 'description': 'フィジカルコンディション'},
    'track_condition': {'name': '馬場・天候適性分析AI', 'weight': '10%', 'description': '馬場状態・コース適性'},
    'statistical': {'name': '統計パターン分析AI', 'weight': '5%', 'description': '歴史的パターン'},
    'odds': {'name': 'オッズ分析AI', 'weight': '5%', 'description': 'オッズの歪み検出'},
}

# エージェント一覧表示
st.subheader("📋 専門家AIエージェント一覧")

agent_df_data = []
for agent_id, info in AGENTS.items():
    model_path = Path(f"models/{agent_id}_agent.pkl")
    status = "✅ 訓練済み" if model_path.exists() else "❌ 未訓練"
    agent_df_data.append({
        'エージェント': info['name'],
        '重み': info['weight'],
        '役割': info['description'],
        'ステータス': status
    })

import pandas as pd
st.dataframe(pd.DataFrame(agent_df_data), use_container_width=True)

st.markdown("---")

# 訓練フォーム
with st.form("training_form"):
    st.subheader("訓練設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # データファイル選択
        data_dir = Path("data/processed")
        csv_files = list(data_dir.glob("*.csv")) if data_dir.exists() else []
        
        if csv_files:
            data_file = st.selectbox(
                "訓練データ",
                options=csv_files,
                format_func=lambda x: x.name
            )
        else:
            st.warning("⚠️ 処理済みデータが見つかりません")
            data_file = None
        
        output_dir = st.text_input("モデル出力先", value="models")
    
    with col2:
        selected_agents = st.multiselect(
            "訓練対象エージェント",
            options=list(AGENTS.keys()),
            default=list(AGENTS.keys()),
            format_func=lambda x: AGENTS[x]['name']
        )
        
        optimize = st.checkbox("ハイパーパラメータ最適化を実行", value=False)
    
    with st.expander("詳細設定"):
        cv_folds = st.slider("Cross-Validation分割数", min_value=2, max_value=10, value=5)
        test_size = st.slider("テストデータ割合", min_value=0.1, max_value=0.3, value=0.2, step=0.05)
    
    submitted = st.form_submit_button("🚀 訓練開始", type="primary", use_container_width=True)

# 訓練実行
if submitted:
    if data_file is None:
        st.error("⚠️ 訓練データを選択してください")
    elif not selected_agents:
        st.error("⚠️ 少なくとも1つのエージェントを選択してください")
    else:
        st.info(f"📊 訓練データ: {data_file.name}")
        st.info(f"🎯 対象エージェント: {len(selected_agents)}個")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.container()
        
        try:
            from src.training.train_agents import AgentTrainer
            
            df = pd.read_csv(data_file)
            st.write(f"データサイズ: {len(df):,} 行")
            
            trainer = AgentTrainer(output_dir=output_dir)
            
            results = {}
            for i, agent_name in enumerate(selected_agents):
                status_text.text(f"訓練中: {AGENTS[agent_name]['name']} ({i+1}/{len(selected_agents)})")
                progress_bar.progress((i) / len(selected_agents))
                
                result = trainer.train_single_agent(
                    agent_name=agent_name,
                    df=df,
                    optimize=optimize,
                    cv_folds=cv_folds
                )
                results[agent_name] = result
            
            progress_bar.progress(100)
            status_text.text("")
            
            st.success("✅ 訓練完了！")
            
            # 結果表示
            with results_container:
                st.subheader("📊 訓練結果")
                
                result_df_data = []
                for agent_name, result in results.items():
                    result_df_data.append({
                        'エージェント': AGENTS[agent_name]['name'],
                        'RMSE': f"{result.get('rmse', 'N/A'):.4f}" if result.get('rmse') else 'N/A',
                        'R²': f"{result.get('r2', 'N/A'):.4f}" if result.get('r2') else 'N/A',
                        '訓練時間': f"{result.get('training_time', 0):.1f}秒"
                    })
                
                st.dataframe(pd.DataFrame(result_df_data), use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ エラー: {str(e)}")
            st.exception(e)

# サイドバー: モデル情報
with st.sidebar:
    st.header("📁 訓練済みモデル")
    
    models_dir = Path("models")
    if models_dir.exists():
        pkl_files = list(models_dir.glob("*.pkl"))
        st.write(f"モデル数: {len(pkl_files)}")
        
        for f in pkl_files:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            st.caption(f"🧠 {f.stem} ({mtime.strftime('%m/%d')})")
    else:
        st.info("まだモデルがありません")
