"""
バックテストページ
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from pathlib import Path

st.set_page_config(page_title="バックテスト - 競馬AI", page_icon="📈", layout="wide")

st.title("📈 バックテスト")

# 入力フォーム
with st.form("backtest_form"):
    st.subheader("バックテスト条件")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "開始日",
            value=date.today() - timedelta(days=30)
        )
        
        end_date = st.date_input(
            "終了日",
            value=date.today() - timedelta(days=1)
        )
    
    with col2:
        budget = st.number_input(
            "初期資金（円）",
            min_value=10000,
            max_value=10000000,
            value=100000,
            step=10000
        )
        
        strategies = st.multiselect(
            "戦略",
            options=["conservative", "balanced", "aggressive"],
            default=["balanced"],
            format_func=lambda x: {
                "conservative": "🛡️ 保守的",
                "balanced": "⚖️ バランス型",
                "aggressive": "🚀 積極的"
            }[x]
        )
    
    submitted = st.form_submit_button("📊 バックテスト実行", type="primary", use_container_width=True)

# バックテスト実行
if submitted:
    if not strategies:
        st.error("⚠️ 少なくとも1つの戦略を選択してください")
    else:
        data_path = Path('data/processed/training_data.csv')
        
        if not data_path.exists():
            st.error(f"⚠️ データが見つかりません: {data_path}")
            st.info("先に前処理を実行してください。")
        else:
            with st.spinner("バックテスト実行中..."):
                try:
                    from src.evaluation.backtester import Backtester
                    
                    df = pd.read_csv(data_path)
                    
                    # 日付フィルタ
                    if 'race_date' in df.columns:
                        df['race_date'] = pd.to_datetime(df['race_date'])
                        df = df[(df['race_date'] >= pd.Timestamp(start_date)) & 
                                (df['race_date'] <= pd.Timestamp(end_date))]
                    
                    st.info(f"対象データ: {len(df):,} 行")
                    
                    results = {}
                    progress_bar = st.progress(0)
                    
                    for i, strategy in enumerate(strategies):
                        backtester = Backtester(
                            initial_budget=budget,
                            strategy=strategy
                        )
                        result = backtester.run(df)
                        results[strategy] = result
                        progress_bar.progress((i + 1) / len(strategies))
                    
                    st.success("✅ バックテスト完了")
                    
                    # 結果表示
                    st.markdown("---")
                    st.header("📊 結果サマリー")
                    
                    cols = st.columns(len(strategies))
                    for i, (strategy, result) in enumerate(results.items()):
                        with cols[i]:
                            final_budget = result.get('final_budget', budget)
                            roi = (final_budget / budget - 1) * 100
                            hit_rate = result.get('hit_rate', 0) * 100
                            
                            st.metric(
                                label=f"{strategy}",
                                value=f"¥{final_budget:,.0f}",
                                delta=f"{roi:+.1f}%"
                            )
                            st.caption(f"的中率: {hit_rate:.1f}%")
                    
                    # チャート
                    st.markdown("---")
                    st.subheader("📈 資金推移")
                    
                    chart_data = pd.DataFrame({
                        strategy: result.get('budget_history', [budget])
                        for strategy, result in results.items()
                    })
                    st.line_chart(chart_data)
                    
                except Exception as e:
                    st.error(f"❌ エラー: {str(e)}")
                    st.exception(e)
