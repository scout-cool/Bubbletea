import math
import bubbletea

# # # # # # # # # # # # # # # # #
# Load data from Aave subgraph  #
# # # # # # # # # # # # # # # # #
url_aave_subgraph = "https://api.thegraph.com/subgraphs/name/aave/protocol-v2"
query_aave = """
{
    deposits(
        where:{timestamp_gt:1609459200, timestamp_lt:1610236800}
        orderBy: timestamp
        orderDirection: asc
        bypassPagination: true
    ) {
        amount
        timestamp
        reserve {
            symbol
            decimals
        }
    }
}
"""

df = bubbletea.load_subgraph(url_aave_subgraph, query_aave)
df = df["deposits"]
df = df[df['reserve.symbol'] == 'AAVE'] #Only show deposits with AAVE tokens
df['amount'] = df["amount"] / math.pow(10, 18) #Convert token amount with 18 decimals


# # # # # # # # # # # # # # # # #
# Draw the data on a line chart #
# # # # # # # # # # # # # # # # #
bubbletea.plot_line(
    title='AAVE Deposits',
    df=df,
    x={"title": "Time", "field": "timestamp"},
    ys=[{"title": "Amount", "field": "amount"}],
)