# Function - Performs Benford analysis on .csv dataset with variables 
# net_value, issue_date, congressperson_name
# To do
# (X) Return summary stats of benford analysis 
# ( ) Use data.table to improve loading speed data.table
library(benford.analysis)

benford.subquota <- function(data, mode = "std",value = "net_value",
                             date.str = "issue_date",congr.name = "congressperson_name",ndigits = 2){
  require(benford.analysis)
  # Input checking
  if(!(is.data.frame(data))) stop ("Data must be in data.frame format",call. = TRUE)
  vars.list <- c(value,date.str,congr.name) 
  match.values <- sum((vars.list %in% colnames(data)))
  if (match.values != length(vars.list)) stop("Variables not found in data set",call. = TRUE) #Check if variables are in dataset
  
  # Analysis and saving values
  net_value.benford <- benford(data$net_value,number.of.digits = ndigits)
  sample.stats <- matrix(nrow = 13,ncol = 1)
  row.names(sample.stats) <- c("no_obsv","no_2obsv","no_digits",
                               "mantiss_mean","mantiss_var","mantiss_exkurt","mantiss_skew",
                               "mantiss_l2","mantiss_df",
                               "chi_square","df",
                               "mean_abs_dev","distort_fact")
  sample.stats[,1] <- c(nrow(net_value.benford$data),nrow(net_value.benford$s.o.data),ndigits,
                    net_value.benford$mantissa[1:4][[2]],
                    as.numeric(net_value.benford$stats[[2]][1:2]),
                    as.numeric(net_value.benford$stats[[1]][1:2]),
                    net_value.benford$MAD,net_value.benford$distortion.factor)
  return(sample.stats)
  }

# Reads data
data.set <- read.csv("../data/2016-08-08-last-year.xz")

# Performs benford analysis with first 2 digits
net_value.benford <- benford(data$net_value,number.of.digits = 2)

# Selects cases with 2 most frequent digits
suspects <- getSuspects(net_value.benford,data, how.many=2)

# Here we have the most cited names 
sort(table(suspects$congressperson_name)) #Looks like we have some suspects:)

