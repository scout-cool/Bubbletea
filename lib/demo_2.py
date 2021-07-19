import time
from earlgrey.thegraph import loader as gl
from earlgrey.charts import line as l
from earlgrey import crypto_compare as cp
from earlgrey.transformers import timeseries as ts
import os
import datetime
from earlgrey.transformers import urlparser as urlparser



urlvars = urlparser.parse_url_var([{'key':'startdate','type':'datetime'}, {'key':'enddate','type':'datetime'}])

try:
    end_date = urlvars['enddate']
except KeyError:
    end_date = datetime.date.today() - datetime.timedelta(days=0)

try:
    start_date = urlvars['startdate']
except KeyError:
    start_date = end_date - datetime.timedelta(days=7)

start_timestamp = int(time.mktime(start_date.timetuple()))
end_timestamp = int(time.mktime(end_date.timetuple()))

# # # # # # # # # # # # # # # # #
# Load data from AAVE subgraph  #
# # # # # # # # # # # # # # # # #
url_aave_subgraph = "https://api.thegraph.com/subgraphs/name/aave/protocol-v2"
query_aave = """
{
    deposits(
        where:{timestamp_gte:%s, timestamp_lt:%s}
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
""" % (
    start_timestamp,
    end_timestamp,
)

data_aave = gl.load_subgraph(url_aave_subgraph, query_aave)
data_aave = data_aave["data"]["deposits"]
data_aave = data_aave[data_aave['reserve.symbol'] == 'AAVE'] #Only show deposits with AAVE tokens
data_hourly_aave = ts.aggregate_timeseries( #aggregate deposits data by hours
    data_aave,
    time_column="timestamp",
    interval=ts.TimeseriesInterval.HOURLY,
    columns=[
        ts.ColumnConfig(
            name="amount",
            aggregate_method=ts.AggregateMethod.SUM,
            na_fill_value=0.0,
        )
    ],
)
data_hourly_aave["amount"] = data_hourly_aave["amount"] / 1000000000000000000 #Divided by 18 decimals

# # # # # # # # # # # # # # # # # # # # # # #
# Load pricing data from cryptocompare.com  #
# # # # # # # # # # # # # # # # # # # # # # #
CP_API_TOKEN = os.environ.get("cp_api_token")
pricing_df = cp.load_historical_data(
    "AAVE", "USD", start_timestamp, end_timestamp, CP_API_TOKEN, 2000
)

# # # # # # # # # # # # # # # # # # # # # # #
# merge the aave subgraph and pricing data  #
# # # # # # # # # # # # # # # # # # # # # # #
result = data_hourly_aave.merge(pricing_df, left_index=True, right_on='time')

# # # # # # # # # # # # # # # # #
# Draw the data on a line chart #
# # # # # # # # # # # # # # # # # 
l.plot(
    title='Hourly AAVE Deposits vs Pricing',
    df=result, 
    x={"title":"Time", "field":"time"},
    yLeft = [{"title":"Price", "field":"close"}],
    yRight= [{"title":"Amount", "field":"amount"}]
    )
