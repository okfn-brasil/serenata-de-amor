
using DataFrames, Gadfly

limit = readtable("../data/2016-11-15-limit-by-subquota.csv")

limit[:diff] = map((x,y) -> x-y , limit[:value], limit[:max])


by(limit, [:subquota_description], limit -> sum(limit[:diff]))

plot(limit,ygroup="subquota_description" ,y="diff", Geom.subplot_grid(Geom.point))

plot(limit, x="diff", color="subquota_description", Geom.density)


set_default_plot_size(22cm, 28cm)
plot(limit, ygroup="subquota_description", x="month",  y="diff", color="subquota_description", Geom.subplot_grid(Geom.point))
