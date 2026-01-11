"""
予測ページ
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from pathlib import Path

st.set_page_config(page_title="予測 - 競馬AI", page_icon="🎯", layout="wide")

st.title("🎯 レース予測")

# 入力フォーム
with st.form("prediction_form"):
    st.subheader("予測条件")
    
    col1, col2 = st.columns(2)
    
    with col1:
        prediction_date = st.date_input(
            "予測日",
            value=date.today() + timedelta(days=1),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=30)
        )
        
        strategy = st.selectbox(
            "戦略",
            options=["conservative", "balanced", "aggressive"],
            index=1,
            format_func=lambda x: {
                "conservative": "🛡️ 保守的（回収率105-110%目標）",
                "balanced": "⚖️ バランス型（回収率110-120%目標）",
                "aggressive": "🚀 積極的（回収率120-140%目標）"
            }[x]
        )
    
    with col2:
        budget = st.number_input(
            "予算（円）",
            min_value=1000,
            max_value=1000000,
            value=10000,
            step=1000
        )
        
        output_format = st.selectbox(
            "出力形式",
            options=["text", "json", "html"],
            format_func=lambda x: {"text": "📄 テキスト", "json": "📊 JSON", "html": "🌐 HTML"}[x]
        )
    
    submitted = st.form_submit_button("🔮 予測実行", type="primary", use_container_width=True)

# 予測実行
if submitted:
    data_file = Path(f'data/live_{prediction_date.strftime("%Y%m%d")}.csv')
    
    if not data_file.exists():
        st.error(f"⚠️ データが見つかりません: {data_file}")
        st.info("先にデータ収集を実行してください。")
        st.code(f"keiba-ai collect --start-date {prediction_date} --end-date {prediction_date}")
    else:
        with st.spinner("予測中..."):
            try:
                from src.orchestrator.agent_manager import AgentManager
                from src.orchestrator.weight_optimizer import WeightOptimizer
                from src.orchestrator.prediction_orchestrator import PredictionOrchestrator
                from src.orchestrator.ev_calculator import EVCalculator
                from src.orchestrator.betting_recommender import BettingRecommender
                
                df = pd.read_csv(data_file)
                
                agent_manager = AgentManager(model_dir='models')
                weight_optimizer = WeightOptimizer()
                orchestrator = PredictionOrchestrator(
                    agent_manager=agent_manager,
                    weight_optimizer=weight_optimizer
                )
                ev_calculator = EVCalculator(min_ev_threshold=0.05)
                recommender = BettingRecommender(total_budget=budget)
                
                races = df['race_id'].unique()
                
                st.success(f"✅ 予測完了: {len(races)} レース")
                
                # 結果表示
                st.markdown("---")
                st.header("📊 予測結果")
                
                for rid in races[:5]:  # 最初の5レースのみ表示
                    race_df = df[df['race_id'] == rid].copy()
                    predictions = orchestrator.predict_race(race_df)
                    positive_ev = ev_calculator.find_positive_ev_bets(predictions)
                    recommendations = recommender.generate_recommendations(positive_ev, strategy=strategy)
                    
                    with st.expander(f"レース: {rid}"):
                        st.text(recommender.format_output_text(recommendations))
                
                if len(races) > 5:
                    st.info(f"他 {len(races) - 5} レースの結果は出力ファイルをご確認ください。")
                    
            except Exception as e:
                st.error(f"❌ エラー: {str(e)}")
                st.exception(e)
