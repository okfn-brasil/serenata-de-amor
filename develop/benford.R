library(benford.analysis)

# Reads data
data <- read.csv("../data/2016-08-08-last-year.xz")

# Performs benford analysis with first 3 digits
net_value.benford <- benford(data$net_value,number.of.digits = 3)

# Plot results
plot(net_value.benford)

# Get 10 most frequent values
head(suspectsTable(net_value.benford),10)

# Selects cases with 2 most frequent digits
suspects <- getSuspects(net_value.benford,data, how.many=2)

# Mean absolute deviation
MAD(net_value.benford)

# Here we have the most cited names 
sort(table(suspects$congressperson_name))