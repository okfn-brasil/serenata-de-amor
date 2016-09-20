## Performs Benford analysis on dataset and returns summary stats and values for suspects

## Returns list with two matrix objetics:
### 1 - Sample stats from Benford analysis; 
### 2 - Frequency of cases per congressman for frequent initial digit sequences  

# To do
# ( ) Parse issue_date and get results per month/trimester (good for detecting pattern changes) 

# We can use "output.size" argument to get more values and "by" 
# to change stat used for classification (’abs.excess.summation’,’difference’,’squared.diff’
# or’absolute.diff’).

benford.subquota <- function(data,value = "net_value",
                             date.str = "issue_date",congr.name = "congressperson_name",
                             ndigits = 2, output.size = 3,by = "absolute.diff"){
  require(benford.analysis)

  # Input checking
  if(!(is.data.frame(data))) stop ("Data must be in data.frame format",call. = TRUE)
  vars.list <- c(value,date.str,congr.name) 
  match.values <- sum((vars.list %in% colnames(data)))
  if (match.values != length(vars.list)) stop("Variables not found in data set",call. = TRUE) #Check if variables are in dataset
  
  # Analysis and saving values
  net_value.benford <- benford(data[,value],number.of.digits = ndigits)
  sample.stats <- matrix(nrow = 13,ncol = 1)
  row.names(sample.stats) <- c("no_obsv","no_2obsv","no_digits",
                               "mantiss_mean","mantiss_var","mantiss_exkurt","mantiss_skew",
                               "mantiss_l2","mantiss_df",
                               "chi_square","df",
                               "mean_abs_dev","distort_fact")
  colnames(sample.stats) <- "value"
  sample.stats[,1] <- c(nrow(net_value.benford$data),nrow(net_value.benford$s.o.data),ndigits,
                    net_value.benford$mantissa[1:4][[2]],
                    as.numeric(net_value.benford$stats[[2]][1:2]),
                    as.numeric(net_value.benford$stats[[1]][1:2]),
                    net_value.benford$MAD,net_value.benford$distortion.factor)
  
  # The following is 'imported' from getSuspects function
  benf.digits <- net_value.benford[["bfd"]][order(get(by), decreasing = TRUE)][, 
                                                            list(digits)][1:output.size]
  suspect.lines <- list()
  data$digit <- numeric(length = nrow(data))
  data$digit <- NA
  for (i in 1:length(benf.digits$digits)){
  suspect.lines[[i]] <- net_value.benford[["data"]]$lines.used[net_value.benford[["data"]]$data.digits %in% 
                                               benf.digits$digits[i]]
  data[suspect.lines[[i]],"digit"] <- benf.digits$digits[[i]]
  }
  congress.values <- table(data[,c("congressperson_name","digit")])
  return (list(sample_stats = sample.stats,congress_values = congress.values))
  }
