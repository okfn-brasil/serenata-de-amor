
using DataFrames, PlotlyJS

limit = readtable("../data/2016-11-15-limit-by-subquota.csv")

limit[:diff] = map((x,y) -> round(x-y,2) , limit[:value], limit[:max])
data = bar(;x=limit[:name],y=limit[:diff])

plot(data)

sum(limit[:diff])
