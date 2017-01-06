
# coding: utf-8

# # Applying OCR to receipts
# 
# As part of some analysis we might want to know the exact time when a receipt was issued and / or want to know the items that makes up for it in order to analyse its contents.
# 
# For example, we can:
# 
# * Match the timestamp of a receipt in a city far away from Brasilia when we believe the congress person was supposed to be in a session.
# * Match two timestamps of receipts made on the same day on cities really far from each other /
# * Look for things like alcoholic beverages.
# * See if the congressperson ordered too many dishes for "himself".
# * Check in and check out dates from hotels.
# 
# Even though we have lots of libraries for doing OCR in Python, I believe [Google's Cloud Vision API](https://cloud.google.com/vision/) should be the "State of the art" when it comes to that type of thing since it is backed by Google, not to say that it is really easy to use. This notebook outlines the results of OCR'ing the receipts of the following 10 reimbursements picked from another analysis I did:
# 
# * https://jarbas.datasciencebr.com/#/document_id/5631309 -> http://www.camara.gov.br/cota-parlamentar/documentos/publ/1789/2015/5631309.pdf
# * https://jarbas.datasciencebr.com/#/document_id/5631380 -> http://www.camara.gov.br/cota-parlamentar/documentos/publ/1789/2015/5631380.pdf
# * https://jarbas.datasciencebr.com/#/document_id/5928875 -> http://www.camara.gov.br/cota-parlamentar/documentos/publ/1564/2016/5928875.pdf
# * https://jarbas.datasciencebr.com/#/document_id/5768932 -> http://www.camara.gov.br/cota-parlamentar/documentos/publ/80/2015/5768932.pdf
# * https://jarbas.datasciencebr.com/#/document_id/5962849 -> http://www.camara.gov.br/cota-parlamentar/documentos/publ/3052/2016/5962849.pdf
# * https://jarbas.datasciencebr.com/#/document_id/5962903 -> http://www.camara.gov.br/cota-parlamentar/documentos/publ/3052/2016/5962903.pdf
# * https://jarbas.datasciencebr.com/#/document_id/5855221 -> http://www.camara.gov.br/cota-parlamentar/documentos/publ/2238/2015/5855221.pdf
# * https://jarbas.datasciencebr.com/#/document_id/5856784 -> http://www.camara.gov.br/cota-parlamentar/documentos/publ/2238/2015/5856784.pdf
# * https://jarbas.datasciencebr.com/#/document_id/5921187 -> http://www.camara.gov.br/cota-parlamentar/documentos/publ/2871/2016/5921187.pdf
# * https://jarbas.datasciencebr.com/#/document_id/6069360 -> http://www.camara.gov.br/cota-parlamentar/documentos/publ/2935/2016/6069360.pdf
# 
# **NOTE**: While this could have been done in Python, it would take me a while to get it going so I kept things as simple as possible with bash since this is just a spike.

# # Setup
# 
# _Make sure your `config.ini` has the Google APIKey set._

# In[1]:

import configparser

settings = configparser.RawConfigParser()
settings.read('../config.ini')

target = open('/tmp/cloud-vision.key', 'w')
target.write(settings.get('Google', 'APIKey'))
target.close()


# You'll also need the `pdftoppm` command to convert PDFs to PNGs and `jq` to pretty print the JSON output returned by Google's API.
# 
# On the Docker environment provided, you'll need to `docker exec -u root -ti CONTAINER bash` in order to have permissions to install the packages with a
# 
# ```
# apt-get update && apt-get install -y poppler-utils jq
# ```
# 
# ## Download receipts, convert to PNG and OCR them

# In[2]:

get_ipython().run_cell_magic('bash', '', '\nocr() {\n  id="${1}"\n  url="${2}"\n  mkdir -p "/tmp/reimbursements/${id}"\n  cd "/tmp/reimbursements/${id}"\n  echo "---> $id"\n  echo "     Downloading PDF from \'$url\'..."\n  curl -s "${url}" > "document.pdf"\n  echo "     Generating PNGs..."\n  pdftoppm -rx 300 -ry 300 -png "document.pdf" page\n  \n  for img in page*.png; do\n    echo "     OCRing ${img}..."\n    payload="payload-${img%.*}.json"\n    response="response-${img%.*}.json"\n    echo -n \'{"requests": [ { "features": [ { "type": "TEXT_DETECTION" } ], "image": { "content": "\' > $payload\n    base64 -w 0 $img >> $payload\n    echo -n \'" } } ] }\' >> $payload\n    \n    curl -s "https://vision.clients6.google.com/v1/images:annotate?key=$(cat /tmp/cloud-vision.key)&alt=json" \\\n         --data-binary @$payload \\\n         -H \'Content-Type: application/json\' \\\n      > $response\n  done\n}\n\ndate\nocr 5631309 \'http://www.camara.gov.br/cota-parlamentar/documentos/publ/1789/2015/5631309.pdf\'\nocr 5631380 \'http://www.camara.gov.br/cota-parlamentar/documentos/publ/1789/2015/5631380.pdf\'\nocr 5928875 \'http://www.camara.gov.br/cota-parlamentar/documentos/publ/1564/2016/5928875.pdf\'\nocr 5768932 \'http://www.camara.gov.br/cota-parlamentar/documentos/publ/80/2015/5768932.pdf\'\nocr 5962849 \'http://www.camara.gov.br/cota-parlamentar/documentos/publ/3052/2016/5962849.pdf\'\nocr 5962903 \'http://www.camara.gov.br/cota-parlamentar/documentos/publ/3052/2016/5962903.pdf\'\nocr 5855221 \'http://www.camara.gov.br/cota-parlamentar/documentos/publ/2238/2015/5855221.pdf\'\nocr 5856784 \'http://www.camara.gov.br/cota-parlamentar/documentos/publ/2238/2015/5856784.pdf\'\nocr 5921187 \'http://www.camara.gov.br/cota-parlamentar/documentos/publ/2871/2016/5921187.pdf\'\nocr 6069360 \'http://www.camara.gov.br/cota-parlamentar/documentos/publ/2935/2016/6069360.pdf\'\ndate')


# As we can see, it takes a while to process just 10 PDFs on a 60Mb connection (~2 minutes), if we ever move on with this we should really look into parallelizing it from day 0 and / or sending receipts in batches as it is supported by the API.
# 
# ## Document [5631309](https://jarbas.datasciencebr.com/#/document_id/5631309)
# 
# A hotel receipt with lots of text in it. There is a lot of stuff on those JSON responses so we just extract the info for the piece that represents the whole text.

# In[3]:

get_ipython().run_cell_magic('bash', '', "jq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/5631309/response-page-1.json\necho '--------------'; echo\njq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/5631309/response-page-2.json")


# As we can see, it'd be pretty hard to parse the contents with a trivial "string matching algorithm", my guess is that the fact that the receipt is not fully vertical gets the OCR confused

# ## Document [5631380](https://jarbas.datasciencebr.com/#/document_id/5631380)
# 
# There are 3 timestamps on the receipt and OCR extracted 2. The receipt items prices were also more or less extracted properly (4.50 and 4.75)

# In[4]:

get_ipython().run_cell_magic('bash', '', "jq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/5631380/response-page-1.json")


# ## Document [5928875](https://jarbas.datasciencebr.com/#/document_id/5928875) 
# 
# The API is obviously not that magical and it can't parse handwritten stuff

# In[5]:

get_ipython().run_cell_magic('bash', '', "jq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/5928875/response-page-1.json")


# ## Document [5768932](https://jarbas.datasciencebr.com/#/document_id/5768932) 
# 
# A six page reimbursement document, most interesting info is on pages 4 and 5. On page 4, we can see items that make up for the meals expenses:

# In[6]:

get_ipython().run_cell_magic('bash', '', "jq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/5768932/response-page-4.json")


# And on page 5 we can easily identify the period the person was in the hotel (search for `IN` and `OUT`, both followed by a date)

# In[7]:

get_ipython().run_cell_magic('bash', '', "jq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/5768932/response-page-5.json")


# ## Document [5962849](https://jarbas.datasciencebr.com/#/document_id/5962849) 
# 
# We can parse both timestamps on the receipt

# In[8]:

get_ipython().run_cell_magic('bash', '', "jq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/5962849/response-page-1.json")


# ## Document [5962903](https://jarbas.datasciencebr.com/#/document_id/5962903) 
# 
# Can nicely parse receipt items, prices and timestamp

# In[9]:

get_ipython().run_cell_magic('bash', '', "jq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/5962903/response-page-1.json")


# ## Document [5855221](https://jarbas.datasciencebr.com/#/document_id/5855221) 
# 
# Here we have both the card receipt and the invoice, the quality of the PDF / images sucks and the API can't do magic

# In[10]:

get_ipython().run_cell_magic('bash', '', "jq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/5855221/response-page-1.json")


# ## Document [5856784](https://jarbas.datasciencebr.com/#/document_id/5856784) 
# 
# Here we have both the card receipt and the invoice but this time the API can get some timestamps and a bit of the receipt items

# In[11]:

get_ipython().run_cell_magic('bash', '', "jq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/5856784/response-page-1.json")


# ## Document [5921187](https://jarbas.datasciencebr.com/#/document_id/5921187) 
# 
# OCR doesn't make any sense, probably because the receipt is not fully vertical as well

# In[12]:

get_ipython().run_cell_magic('bash', '', "jq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/5921187/response-page-1.json")


# ## Document [6069360](https://jarbas.datasciencebr.com/#/document_id/6069360) 
# 
# All messed up, even found some weird foreign characters, but it found the timestamp

# In[13]:

get_ipython().run_cell_magic('bash', '', "jq -r '.responses[].textAnnotations[0].description' /tmp/reimbursements/6069360/response-page-1.json")


# # Conclusion
# 
# Even though not everything will be able to be parsed, more than half can get their timestamps extracted which is a nice data point to have around.
# 
# Some ideas for future work:
# 
# - Figure out if we can detect that the receipts have been rotated and try to use some image processing to fix it.
# - Come up with some pre analysis of the image to detect "bluriness" so we can potentially discard OCR processing when a new receipt comes in that is not good.
# - Another nice pre analysis would be to determine if a receipt is handwritten or not so we can flag them and filter them out on other analysis.
# 
# **NOTE** Everyone that registers for the Google Cloud engine gets US$300 to spend on the first 60 days so we can probably do a lot of tweaking on our code for free before we "Get it right"
