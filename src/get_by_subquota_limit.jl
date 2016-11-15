using DataFrames

# join the files
files = ["./data/2016-08-08-previous-years.csv",
"./data/2016-08-08-last-year.csv",
"./data/2016-08-08-current-year.csv"]

df = readtable(files[1])

for i in 2:length(files)
  concatdf = readtable(files[i])
  df = vcat(df, concatdf)
end

# group files by [:year, :month, :subquota_description, :congressperson_name]
dfgroup = by(df, [:year, :month, :subquota_description, :congressperson_name], df -> sum(df[:net_value]))

nrows, ncolumns = size(dfgroup)

rename!(dfgroup, :x1, :net_value) 

#create a new df with all data pass the limit
limit = DataFrame(month = 0, year = 0, name = "", subquota_description = "",value = 0.0, max = 0.0)

for row in eachrow(dfgroup)
  if (row[:year] >= 2013 && row[:month] >10) && !(row[:year] >= 2015 && row[:month] >2)
    if row[:subquota_description] == "Automotive vehicle renting or charter" && row[:net_value] > 10001
      push!(limit, @data([row[:month], row[:year], row[:congressperson_name], row[:subquota_description] ,row[:net_value], 10000]))
    end
    if row[:subquota_description] == "Taxi, toll and parking" && row[:net_value] > 2501
      push!(limit, @data([row[:month], row[:year], row[:congressperson_name], row[:subquota_description] ,row[:net_value], 2500]))
    end
  elseif (row[:year] >= 2014 && row[:month] > 4) && !(row[:year] >= 2015 && row[:month] > 2)
    if row[:subquota_description] == "Security service provided by specialized company" && row[:net_value] > 8001
      push!(limit, @data([row[:month], row[:year], row[:congressperson_name], row[:subquota_description] ,row[:net_value], 8000]))
    end
  elseif row[:year] >= 2015 && row[:month] > 2 
    if row[:subquota_description] == "Automotive vehicle renting or charter" && row[:net_value] > 10901
      push!(limit, @data([row[:month], row[:year], row[:congressperson_name], row[:subquota_description] ,row[:net_value], 10900]))
    end
    if row[:subquota_description] == "Taxi, toll and parking" && row[:net_value] > 2701
      push!(limit, @data([row[:month], row[:year], row[:congressperson_name], row[:subquota_description] ,row[:net_value], 2700]))
    end
    if row[:subquota_description] == "Security service provided by specialized company" && row[:net_value] > 8701
      push!(limit, @data([row[:month], row[:year], row[:congressperson_name], row[:subquota_description] ,row[:net_value], 8700]))
    end
    if row[:subquota_description] == "Participation in course, talk or similar event" && row[:net_value] > 7698
      push!(limit, @data([row[:month], row[:year], row[:congressperson_name], row[:subquota_description] ,row[:net_value], 7697]))
    end
    if row[:subquota_description] == "Fuels and lubricants" && row[:net_value] > 4901 && !(row[:year] >= 2015 && row[:month] > 9)
      push!(limit, @data([row[:month], row[:year], row[:congressperson_name], row[:subquota_description] ,row[:net_value], 4900]))
    end
  elseif row[:year] >= 2015 && row[:month] > 9 
    if row[:subquota_description] == "Fuels and lubricants" && row[:net_value] > 6001
      push!(limit, @data([row[:month], row[:year], row[:congressperson_name], row[:subquota_description] ,row[:net_value], 6000]))
    end
  end
end

if(length(limit) != 0)
  deleterows!(limit, 1)
end

writetable("./data/2016-11-15-limit-by-subquota.csv", limit)
