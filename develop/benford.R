library(benford.analysis)

# Reads data
data <- read.csv("../data/2016-08-08-last-year.xz")

# Performs benford analysis with first 2 digits
net_value.benford <- benford(data$net_value,number.of.digits = 2)
# Mean absolute deviation
MAD(net_value.benford)

# Plot results. 
plot(net_value.benford,)
# Get 10 most frequent initial 2 digits and absolut different from benford distribution
head(suspectsTable(net_value.benford),10) # Looks like 10 and 50 are favorite

# Selects cases with 2 most frequent digits
suspects <- getSuspects(net_value.benford,data, how.many=2)

# Here we have the most cited names 
sort(table(suspects$congressperson_name)) #Looks like we have some suspects:)

frequent_values <- suspectsTable(net_value.benford)
ggplot(frequent_values,aes(y = absolute.diff, x = as.factor(digits))) + geom_point()
