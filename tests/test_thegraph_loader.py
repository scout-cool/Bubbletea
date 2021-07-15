import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib import earlgrey
import streamlit as st


st.subheader('Single Subgraph')
url_aave_subgraph = 'https://api.thegraph.com/subgraphs/name/aave/protocol'
query_aave = """
{
    deposits(
        where:{timestamp_gt:1609459200, timestamp_lt:1609462800}
        orderBy: timestamp
        orderDirection: desc
        first:5
        # bypassPagination: true
    ) {
        reserve {
            symbol,
            decimals
        }
        amount
        timestamp
    }
    flashLoans(
        orderBy: timestamp
        orderDirection: asc
        first:3
    ){
        amount
         timestamp
     }
}
"""
data = earlgrey.load_subgraph(url_aave_subgraph, query_aave)
print(data)


# url_compoundv2_subgraph = 'https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v2'
# query_compoundv2 = """
# {
# 	mintEvents(
#         where:{blockTime_gte:1609459200, blockTime_lt:1609462800}
#         bypassPagination: true
#     ) {
# 	    cTokenSymbol
#         amount
#         underlyingAmount
#         blockTime
# 	}
# }
# """
# data = gl.load_subgraph(url_compoundv2_subgraph, query_compoundv2)


# data = data['data']
# for k in data.keys():
#     st.markdown(f'### {k}')
#     st.markdown('#### Data')
#     st.write(data[k])
#     st.markdown('#### Column Types')
#     st.write(data[k].dtypes)



# st.markdown('---')
# st.subheader('Multiple Subgraphs')
# data = gl.load_subgraphs([
#     gl.SubgraphDef(url=url_aave_subgraph, query=query_aave), 
#     gl.SubgraphDef( url=url_compoundv2_subgraph, query=query_compoundv2)
#     ])

# for k in data.keys():
#     st.subheader(k)
#     subgraph = data[k]
#     for e in subgraph.keys():
#         st.markdown(f'### {e}')
#         df = subgraph[e]
#         st.markdown('#### Data')
#         st.write(df)
#         st.markdown('#### Column Types')
#         st.write(df.dtypes)
#         # print(df.dtypes)