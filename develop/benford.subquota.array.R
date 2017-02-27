# Performs benford analysis on dataset and returns array of logical values, TRUE indicates
# suspicious document. The function uses as standard metric the squared difference 
# related compared to the expected value in the Benford distribution.


benford.array <- function(reimb.data, value = "total_net_value", 
                          metric = "squared.diff", ndigits = 2, doc_id = "document_id" , groups = 2){
  require(benford.analysis)
  
  # input checking
  if(!(is.data.frame(reimb.data))) stop ("data must be in data.frame format",call. = TRUE)
  vars.list <- c(value,doc_id) 
  match.values <- sum((vars.list %in% colnames(reimb.data)))
  if (match.values != length(vars.list)) stop("variables not found in data set",call. = TRUE)
  
  # Analyzes dataset and creates bfd object 
  net_value.benford <- benford(reimb.data[,value],number.of.digits = ndigits)
  
  # Get suspicious observations from original dataset
  reimb.susp <- getSuspects(bfd = net_value.benford, data = reimb.data,by = metric)
  logical.array <- reimb.data[[doc_id]] %in% reimb.susp[[doc_id]] # Array with suspects
  return (logical.array)
  }
