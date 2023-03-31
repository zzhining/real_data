from pandas_datareader import data
import yfinance as yfin
import pandas as pd
from datetime import timedelta
import plotly.graph_objects as go

yfin.pdr_override()

def get_stocks(ticker, start = '2023-01-01'):
    stock_df = data.get_data_yahoo(ticker, start = start)
    #stock_df['Close'].plot()
    return stock_df

def get_price_dataframe(num, percent, start_price):
    price_list = [start_price]
    average_price_list = []
    for i in range(num):
        price_list.append(price_list[i] * (1 - percent))
    df = pd.DataFrame({'매수가': price_list})
    df['매수량'] = 1#range(len(price_list))
    df['보유량'] = df['매수량'].cumsum()
    average_price_list = [df['매수가'][0]]
    for i in range(len(df)-1):
        average_price = (average_price_list[i] * df['보유량'][i] + df['매수가'][i+1] * df['매수량'][i+1]) / df['보유량'][i+1]
        average_price_list.append(average_price)
    df['매수 후 평균단가'] = average_price_list
    df['원금'] = df['매수 후 평균단가'] * df['보유량'] 
    df['매수 후 평가금액'] = df['매수가'] * df['보유량'] 
    df['수익률'] = df['매수 후 평가금액']/df['원금'] - 1
    return df

def get_sell_dates(plan_df, stock_df):
    first_date = []
    for value in plan_df['매수가']:
        # print(value)
        index_list = stock_df.query(f'Close >={value} and Close <={value+1}' ).index

        if len(index_list) == 0 or (len(first_date) > 0 and index_list[-1] - first_date[-1] >= timedelta(days=5)
    ):
            index_list = stock_df.query(f'Close <={value+1}' ).index

        # print(index_list)

        if len(first_date) == 0:
            first_date.append(index_list[0])
        else:
            for i in index_list:
                if i > first_date[-1]:
                    # print('i: {}, first_date:{}'.format(i, first_date[-1]))
                    first_date.append(i)
                    break
        # print(first_date[-1])
        # print('-'*10)
    return first_date

def plot_status(stock_df, plan_df, sell_dates):

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=stock_df.index,
        y=stock_df['Close'],
        name = '종가',
        # connectgaps=True # override default to connect the gaps
    ))
    fig.add_trace(go.Scatter(
        x=stock_df.index,
        y=[plan_df['매수 후 평균단가'].iloc[-1]] * len(stock_df.index),
        name='매수 후 평균단가',
    ))
    fig.add_trace(go.Scatter(
        x=sell_dates,
        y=plan_df['매수가'],#TSLA_df.loc[first_date]['Close'],
        mode="markers+text",
        name="분할매수시점",
        # text=plan_df['매수가'],#["Text D", "Text E", "Text F", '3', '3'],
        textposition="bottom center"
    ))
    fig.show()

def run():#ticker, num, percent, start_price):
    ticker = input('시뮬레이션 할 종목의 티커를 입력하세요.(예:TSLA): ')
    stock_df = get_stocks(ticker)
    num = input('몇 번 분할매수를 진행하시겠습니까? (예:20): ')
    percent = input('몇 % 하락시 분할매수를 진행하시겠습니까? (예:1): ')
    print('{}의 종가 최고가는 {:.2f}입니다.'.format(ticker, stock_df['Close'].max()))
    start_price = input('첫 주가 구매 금액을 얼마로 설정하시겠습니까?(예:214): ')
    
    plan_df = get_price_dataframe(int(num), int(percent)/100, float(start_price))
    sell_dates = get_sell_dates(plan_df, stock_df)

    print('\n\n')
    print('='*90)
    print('{}의 현재 보유량은 {}, 매수 후 평균단가는 ${:.2f}입니다.'\
      .format(ticker, plan_df.iloc[-1]['보유량'], plan_df.iloc[-1]['매수 후 평균단가']))

    result = (stock_df.iloc[-1]['Close'] * plan_df.iloc[-1]['보유량'] / plan_df.iloc[-1]['원금'] -1) * 100
    print('총 투자 원금은 ${:.2f} 입니다. {} 기준 수익률은 {:.2f}%입니다.'\
        .format(plan_df.iloc[-1]['원금'], stock_df.index[-1], result))    
    
    filename = '{}_planner.xlsx'.format(ticker)
    plan_df.to_excel(filename)
    print('='*90)
    print('※{}이 생성되었습니다.좌측의 생성된 파일을 다운로드 받아주세요'.format(filename))
    plot_status(stock_df, plan_df, sell_dates)