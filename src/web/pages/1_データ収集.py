"""
データ収集ページ
"""
import streamlit as st
from datetime import date, timedelta
from pathlib import Path

st.set_page_config(page_title="データ収集 - 競馬AI", page_icon="📊", layout="wide")

st.title("📊 データ収集")

st.markdown("""
netkeiba.comからレースデータを収集します。
指定した期間のレース結果、出馬表、オッズ情報を取得できます。
""")

# 入力フォーム
with st.form("collection_form"):
    st.subheader("収集条件")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "開始日",
            value=date.today() - timedelta(days=30)
        )
        
        data_type = st.multiselect(
            "収集データタイプ",
            options=["レース結果", "出馬表", "オッズ", "馬情報"],
            default=["レース結果", "出馬表"]
        )
    
    with col2:
        end_date = st.date_input(
            "終了日",
            value=date.today() - timedelta(days=1)
        )
        
        output_dir = st.text_input(
            "出力ディレクトリ",
            value="data/raw"
        )
    
    # 詳細設定
    with st.expander("詳細設定"):
        crawl_delay = st.slider("クロール間隔（秒）", min_value=0.5, max_value=5.0, value=1.0, step=0.5)
        max_retries = st.number_input("最大リトライ回数", min_value=1, max_value=10, value=3)
    
    submitted = st.form_submit_button("📥 データ収集開始", type="primary", use_container_width=True)

# 収集実行
if submitted:
    if start_date > end_date:
        st.error("⚠️ 開始日は終了日より前である必要があります")
    else:
        st.info(f"📅 期間: {start_date} ～ {end_date}")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 実行
            status_text.text("データ収集を開始しています...")
            
            from src.data_collection.netkeiba_scraper import RaceResultScraper
            import yaml
            
            # 設定読み込み
            config_path = Path('config/scraping_config.yaml')
            if config_path.exists():
                with open(config_path) as f:
                    config = yaml.safe_load(f)
            else:
                config = {
                    'base_url': 'https://db.netkeiba.com',
                    'request_interval': crawl_delay
                }
            
            config['request_interval'] = crawl_delay
            
            # スクレイパー初期化
            scraper = RaceResultScraper(config)
            
            progress_bar.progress(10)
            status_text.text("レースデータを収集中...")
            
            # データ収集
            df = scraper.scrape_date_range(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            progress_bar.progress(80)
            status_text.text("データを保存中...")
            
            if df is not None and not df.empty:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                output_file = output_path / f"race_results_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                
                progress_bar.progress(100)
                status_text.text("")
                
                st.success(f"✅ データ収集完了！")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("収集レコード数", f"{len(df):,}")
                with col2:
                    st.metric("保存先", str(output_file.name))
                with col3:
                    unique_races = df['race_id'].nunique() if 'race_id' in df.columns else "N/A"
                    st.metric("ユニークレース数", unique_races)
                
                # プレビュー
                st.subheader("データプレビュー")
                st.dataframe(df.head(20))
                
            else:
                progress_bar.progress(100)
                st.warning("⚠️ 指定期間にデータが見つかりませんでした")
                
        except Exception as e:
            st.error(f"❌ エラー: {str(e)}")
            st.exception(e)

# サイドバー: 既存データ確認
with st.sidebar:
    st.header("📁 既存データ")
    
    raw_dir = Path("data/raw")
    if raw_dir.exists():
        csv_files = list(raw_dir.glob("*.csv"))
        st.write(f"ファイル数: {len(csv_files)}")
        
        for f in csv_files[:10]:
            size_mb = f.stat().st_size / (1024 * 1024)
            st.caption(f"📄 {f.name} ({size_mb:.1f}MB)")
        
        if len(csv_files) > 10:
            st.caption(f"... 他 {len(csv_files) - 10} ファイル")
    else:
        st.info("まだデータがありません")
