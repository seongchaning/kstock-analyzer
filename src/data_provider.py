
import pandas as pd
from pykrx import stock
from datetime import datetime

def get_top_market_cap_stocks(date: str, limit: int = 50) -> list:
    """
    지정된 날짜 기준으로 KOSPI 시가총액 상위 종목 티커를 반환합니다.

    :param date: 조회할 날짜 (YYYYMMDD)
    :param limit: 가져올 종목 수
    :return: 티커 리스트
    """
    df = stock.get_market_cap_by_ticker(date, market="KOSPI")
    top_stocks = df.sort_values(by="시가총액", ascending=False).head(limit)
    return top_stocks.index.tolist()

def get_price_history(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    지정된 종목의 특정 기간 동안의 일별 시세 데이터를 반환합니다.

    :param ticker: 종목 티커
    :param start_date: 시작일 (YYYYMMDD)
    :param end_date: 종료일 (YYYYMMDD)
    :return: 시세 데이터프레임
    """
    df = stock.get_market_ohlcv_by_date(fromdate=start_date, todate=end_date, ticker=ticker)
    df.rename(columns={"시가": "Open", "고가": "High", "저가": "Low", "종가": "Close", "거래량": "Volume"}, inplace=True)
    return df

def get_stock_name(ticker: str) -> str:
    """
    티커에 해당하는 종목명을 반환합니다.
    
    :param ticker: 종목 티커
    :return: 종목명
    """
    return stock.get_market_ticker_name(ticker)

