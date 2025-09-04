
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import html

# Chart creation functions (moved from main.py)
def create_main_chart(df, stock_name, indicators):
    """주가, 볼린저 밴드, 매매 신호를 포함하는 메인 차트를 생성합니다."""
    fig = go.Figure()

    # 주가 캔들스틱
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='주가', increasing_line_color='red', decreasing_line_color='blue',
        hovertemplate=
            '<b>날짜</b>: %{x}<br>'
            '<b>시가</b>: %{open:,.0f}<br>'
            '<b>고가</b>: %{high:,.0f}<br>'
            '<b>저가</b>: %{low:,.0f}<br>'
            '<b>종가</b>: %{close:,.0f}<br>'
            '<b>전일 대비 변화율</b>: %{customdata[0]:.2f}%<br>'
            '<extra></extra>', # Removes the trace name from the tooltip
        customdata=df[['Daily_Change_Pct']] # Pass the new column as customdata
    ))

    # 볼린저 밴드
    if 'bb' in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], mode='lines', name='BB 상단', line=dict(color='rgba(255, 152, 0, 0.5)', dash='dash'))),
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Middle'], mode='lines', name='BB 중심', line=dict(color='rgba(244, 67, 54, 0.5)', dash='dot'))),
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], mode='lines', name='BB 하단', line=dict(color='rgba(33, 150, 243, 0.5)', dash='dash')))

    # 매매 신호
    buy_signals = df[df['signal'] == 'BUY']
    sell_signals = df[df['signal'] == 'SELL']
    
    fig.add_trace(
        go.Scatter(
            x=buy_signals.index, y=buy_signals['Low'] * 0.98,
            mode='markers', name='매수 신호',
            marker=dict(symbol='triangle-up', color='green', size=10)
        )
    )
    fig.add_trace(
        go.Scatter(
            x=sell_signals.index, y=sell_signals['High'] * 1.02,
            mode='markers', name='매도 신호',
            marker=dict(symbol='triangle-down', color='red', size=10)
        )
    )

    fig.update_layout(
        title=f"{stock_name} 종합 차트",
        yaxis_title="가격 (원)",
        legend_title="지표",
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=40, b=10),
        height=400,
        xaxis=dict(
            type="date",
            tickformat="%Y-%m-%d", # Display full date
            dtick="D1" # Force 1-day intervals
        )
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

# UI rendering functions
def render_sidebar():
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

    return {
        "date_to_check": date_to_check,
        "date_str": date_str,
        "stock_limit": stock_limit,
        "show_bb": show_bb,
        "bb_window": bb_window,
        "bb_std": bb_std,
        "show_rsi": show_rsi,
        "rsi_window": rsi_window,
        "show_macd": show_macd,
        "macd_short": macd_short,
        "macd_long": macd_long,
        "macd_signal": macd_signal
    }

def render_main_analysis_summary(results):
    st.subheader("📊 분석 결과 요약")
    def get_signal_display(signal):
        return {"BUY": "🟢 매수", "SELL": "🔴 매도"}.get(signal, "⚪ 관망")

    summary_df = pd.DataFrame([{
        "종목명": res["name"], "티커": res["ticker"],
        "현재가": f"{res['close']:,.0f}원", "신호": get_signal_display(res["signal"])
    } for res in results])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

def render_detailed_chart_analysis(results, selected_stock_name, indicators_to_show):
    st.subheader("📈 상세 차트 분석")
    
    stock_names = [res['name'] for res in results]
    selected_stock_name = st.selectbox("분석할 종목을 선택하세요:", stock_names, index=stock_names.index(selected_stock_name) if selected_stock_name in stock_names else 0)

    selected_stock_data = next((res for res in results if res['name'] == selected_stock_name), None)

    if selected_stock_data:
        df = selected_stock_data['df']
        
        # 메인 차트
        st.plotly_chart(create_main_chart(df, selected_stock_name, indicators_to_show), use_container_width=True)
        
        # 거래량 차트
        st.plotly_chart(create_volume_chart(df), use_container_width=True)

        # 보조지표 차트
        if 'rsi' in indicators_to_show:
            st.plotly_chart(create_rsi_chart(df), use_container_width=True)
        if 'macd' in indicators_to_show:
            st.plotly_chart(create_macd_chart(df), use_container_width=True)
