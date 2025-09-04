
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import html
import logging

from src.data_provider import get_top_market_cap_stocks, get_price_history, get_stock_name
from src.indicator_calculator import add_bollinger_bands, add_rsi, add_macd
from src.signal_generator import generate_signals

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(layout="wide")

# --- 함수 정의 --- #

def create_main_chart(df, stock_name, indicators):
    """주가, 볼린저 밴드, 매매 신호를 포함하는 메인 차트를 생성합니다."""
    fig = go.Figure()

    # 주가 캔들스틱
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='주가', increasing_line_color='red', decreasing_line_color='blue'
    ))

    # 볼린저 밴드
    if 'bb' in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], mode='lines', name='BB 상단', line=dict(color='rgba(255, 152, 0, 0.5)', dash='dash')))
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Middle'], mode='lines', name='BB 중심', line=dict(color='rgba(244, 67, 54, 0.5)', dash='dot')))
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], mode='lines', name='BB 하단', line=dict(color='rgba(33, 150, 243, 0.5)', dash='dash')))

    # 매매 신호
    buy_signals = df[df['signal'] == 'BUY']
    sell_signals = df[df['signal'] == 'SELL']
    
    fig.add_trace(go.Scatter(
        x=buy_signals.index, y=buy_signals['Low'] * 0.98,
        mode='markers', name='매수 신호',
        marker=dict(symbol='triangle-up', color='green', size=10)
    ))
    fig.add_trace(go.Scatter(
        x=sell_signals.index, y=sell_signals['High'] * 1.02,
        mode='markers', name='매도 신호',
        marker=dict(symbol='triangle-down', color='red', size=10)
    ))

    fig.update_layout(
        title=f"{stock_name} 종합 차트",
        yaxis_title="가격 (원)",
        legend_title="지표",
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=40, b=10),
        height=400
    )
    return fig

def create_volume_chart(df):
    """거래량 차트를 생성합니다."""
    colors = ['red' if row['Open'] - row['Close'] >= 0 else 'blue' for index, row in df.iterrows()]
    fig = go.Figure(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='거래량'))
    fig.update_layout(yaxis_title="거래량", height=150, margin=dict(l=10, r=10, t=20, b=10))
    return fig

def create_rsi_chart(df):
    """RSI 차트를 생성합니다."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI'))
    fig.add_hline(y=70, line_dash="dash", line_color="red")
    fig.add_hline(y=30, line_dash="dash", line_color="blue")
    fig.update_layout(yaxis_title="RSI", height=150, margin=dict(l=10, r=10, t=20, b=10))
    return fig

def create_macd_chart(df):
    """MACD 차트를 생성합니다."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], mode='lines', name='MACD', line_color='green'))
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], mode='lines', name='Signal Line', line_color='orange'))
    fig.add_bar(x=df.index, y=df['MACD'] - df['MACD_Signal'], name='Oscillator', marker_color='purple')
    fig.update_layout(yaxis_title="MACD", height=150, margin=dict(l=10, r=10, t=20, b=10))
    return fig


# --- 사이드바 --- #
st.sidebar.title("📈 KOSPI 분석 설정")
today = datetime.today()
date_to_check = st.sidebar.date_input("기준일", today, max_value=today)
date_str = date_to_check.strftime("%Y%m%d")
stock_limit = st.sidebar.slider("분석할 종목 수", 10, 50, 20)

st.sidebar.header("기술적 지표 설정")
show_bb = st.sidebar.checkbox("볼린저 밴드 (BB)", value=True)
bb_window = st.sidebar.slider("BB 기간 (일)", 5, 60, 20)
bb_std = st.sidebar.slider("BB 표준편차", 1.0, 3.0, 2.0, 0.1)

show_rsi = st.sidebar.checkbox("RSI", value=True)
rsi_window = st.sidebar.slider("RSI 기간 (일)", 7, 28, 14)

show_macd = st.sidebar.checkbox("MACD", value=False)
macd_short = st.sidebar.slider("MACD 단기 EMA", 5, 20, 12)
macd_long = st.sidebar.slider("MACD 장기 EMA", 21, 50, 26)
macd_signal = st.sidebar.slider("MACD 신호선", 5, 15, 9)


# --- 메인 화면 --- #
st.title("KOSPI 상위 종목 매매 신호 분석")
st.write(f"{date_to_check.strftime('%Y년 %m월 %d일')} 기준 시가총액 상위 {stock_limit}개 종목")

if 'results' not in st.session_state or st.sidebar.button("분석 시작", use_container_width=True):
    try:
        with st.spinner("KOSPI 시가총액 상위 종목을 가져오는 중..."):
            top_stocks = get_top_market_cap_stocks(date_str, limit=stock_limit)
        st.success(f"상위 {len(top_stocks)}개 종목을 성공적으로 가져왔습니다.")

        start_date = (date_to_check - timedelta(days=max(bb_window, rsi_window, macd_long) * 2)).strftime("%Y%m%d")
        end_date = date_str

        results = []
        progress_bar = st.progress(0, text="종목별 분석 진행 중...")

        for i, ticker in enumerate(top_stocks):
            stock_name = html.escape(get_stock_name(ticker))
            progress_text = f"({i+1}/{len(top_stocks)}) {stock_name} ({ticker}) 분석 중..."
            progress_bar.progress((i + 1) / len(top_stocks), text=progress_text)

            df = get_price_history(ticker, start_date, end_date)
            if df.empty: continue

            df = add_bollinger_bands(df.copy(), window=bb_window, std=bb_std)
            df = add_rsi(df.copy(), window=rsi_window)
            df = add_macd(df.copy(), short_window=macd_short, long_window=macd_long, signal_window=macd_signal)
            
            # Generate signals for each row for plotting
            df['signal'] = df.apply(lambda row: generate_signals(pd.DataFrame([row])), axis=1)

            results.append({
                "ticker": ticker, "name": stock_name,
                "signal": df.iloc[-1]['signal'], "close": df.iloc[-1]['Close'],
                "df": df
            })
        progress_bar.empty()
        st.session_state['results'] = results

    except Exception as e:
        logging.error(f"분석 중 예기치 않은 오류 발생: {e}", exc_info=True)
        st.error("오류가 발생하여 분석을 완료할 수 없습니다. 서버 로그를 확인해주세요.")

if 'results' in st.session_state and st.session_state['results']:
    results = st.session_state['results']
    
    st.subheader("📊 분석 결과 요약")
    def get_signal_display(signal):
        return {"BUY": "🟢 매수", "SELL": "🔴 매도"}.get(signal, "⚪ 관망")

    summary_df = pd.DataFrame([{
        "종목명": res["name"], "티커": res["ticker"],
        "현재가": f"{res['close']:,.0f}원", "신호": get_signal_display(res["signal"])
    } for res in results])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.subheader("📈 상세 차트 분석")
    
    stock_names = [res['name'] for res in results]
    selected_stock_name = st.selectbox("분석할 종목을 선택하세요:", stock_names)

    selected_stock_data = next((res for res in results if res['name'] == selected_stock_name), None)

    if selected_stock_data:
        df = selected_stock_data['df']
        
        indicators_to_show = []
        if show_bb: indicators_to_show.append('bb')
        if show_rsi: indicators_to_show.append('rsi')
        if show_macd: indicators_to_show.append('macd')

        # 메인 차트
        st.plotly_chart(create_main_chart(df, selected_stock_name, indicators_to_show), use_container_width=True)
        
        # 거래량 차트
        st.plotly_chart(create_volume_chart(df), use_container_width=True)

        # 보조지표 차트
        if 'rsi' in indicators_to_show:
            st.plotly_chart(create_rsi_chart(df), use_container_width=True)
        if 'macd' in indicators_to_show:
            st.plotly_chart(create_macd_chart(df), use_container_width=True)

