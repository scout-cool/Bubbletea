import earlgrey
import streamlit as st
from earlgrey.thegraph import loader as gl
from earlgrey.charts import line as l
import math

st.header("Testing template layout")
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

df = gl.load_subgraph(url_aave_subgraph, query_aave)
df = df["data"]["deposits"]
df = df[df['reserve.symbol'] == 'AAVE'] #Only show deposits with AAVE tokens
df['amount'] = df["amount"] / math.pow(10, 18) #Convert token amount with 18 decimals

with st.beta_expander("Some explanations"):
    st.write("Example tests of the explainer components")

col1, col2, col3 = st.beta_columns([4,1,1])
with col1:
    st.header("A cat")
    st.image("https://static.streamlit.io/examples/cat.jpg")
    l.plot(
    title='AAVE Deposits',
    df=df,
    x={"title": "Time", "field": "timestamp"},
    ys=[{"title": "Amount", "field": "amount"}],
)


with col2:
    st.header("A dog")
    st.image("https://static.streamlit.io/examples/dog.jpg")

with col3:
    st.header("An owl")
    st.image("https://static.streamlit.io/examples/owl.jpg")
