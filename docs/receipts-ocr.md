# Receipts OCR

While looking at the reimbursement details we get from the CEAP dataset provides
a lot of value to do things like detecting outliers, there is no easy way to
analyse the receipts provided by congresspeople with the data we get from the
government. One way to "read" the receipts informations is to use
[OCR](https://en.wikipedia.org/wiki/Optical_character_recognition) and, one of
the easiest and best ways to do that these days is to delegate the OCR
processing to Google's [Cloud Vision API](https://cloud.google.com/vision/).

As of this writing, we have a way to OCR reimbursements on demand by using
[serenata-toolbox](https://github.com/datasciencebr/serenata-toolbox) and some
code outlined below that can be copy & pasted on a Jupyter notebook / Python
script in case you want to OCR a set of reimbursement receipts.

## Available datasets

To make use of the Cloud Vision API you need a Google API Key and you'll be
[charged after 1.000 requests in a month](https://cloud.google.com/vision/#cloud-vision-api-pricing).
The process is slow (but can be parallelized) and in order to make things
simpler there has been an effort to provide a dataset with a reasonable amount
of receipts OCRed ready to be analysed:

- `2017-02-15-receipts-texts.xz`: CSV with the full text of a reimbursement
  receipt in a single string based on a reimbursement's `document_id`.
- `2017-02-15-receipts-texts-raw.tar.xz`: Raw Cloud Vision API responses.

Those datasets are made up of nearly 200.000 reimbursements of the following
subquotas:

```
Aircraft renting or charter of aircraft        589
Congressperson meal                          56715
Consultancy, research and technical work      5082
Flight tickets                                5010
Fuels and lubricants                         64989
Postal services                               4804
Publicity of parliamentary activity          14387
Taxi, toll and parking                       41922
Terrestrial, maritime and fluvial tickets     1786
Watercraft renting or charter                   69
```

For more information on how it was created, check the following links:

- https://github.com/datasciencebr/serenata-de-amor/issues/188#issue-206940795
- https://github.com/datasciencebr/serenata-de-amor/issues/188#issuecomment-279411197
- https://github.com/datasciencebr/serenata-de-amor/issues/188#issuecomment-283495404

**NOTE**: This dataset was created using the [`TEXT_DETECTION` feature](https://cloud.google.com/vision/docs/detecting-text)
of the API but recently [a feature called `DOCUMENT_TEXT_DETECTION`](https://cloud.google.com/vision/docs/detecting-fulltext)
has been introduced (currently in beta) which might yield better results and is
worth further investigation.

### Receipt texts dataset

As mentioned above, the `2017-02-15-receipts-texts.xz` provides a CSV made up of
`document_id` and the reimbursement receipt text (stored on the `text` column).
Combining it reimbursements and using it on your notebooks is as easy as:

```python
import pandas as pd
import numpy as np

# Make sure the data has been downloaded
from serenata_toolbox.datasets import fetch
fetch("2017-02-15-receipts-texts.xz", "../data")
fetch("2016-12-06-reimbursements.xz", "../data")

# Read OCR dataframe
texts = pd.read_csv('../data/2017-02-15-receipts-texts.xz', dtype={'text': np.str}, low_memory=False)
# OPTIONAL: Normalize the string to make it easier to work with
texts['text'] = texts.text.str.upper()

# Read reimbursements data and filter to 2015 to reduce the memory used by it
reimbursements = pd.read_csv('../data/2016-12-06-reimbursements.xz', low_memory=False)
reimbursements = reimbursements.query('(year >= 2015)')

# "JOIN" dataframes on document id
data = texts.merge(reimbursements, on='document_id')
```

### Raw Cloud Vision API responses

The data sent to the API is an image encoded in base 64 (more info [here](https://cloud.google.com/vision/docs/reference/rest/v1/images/annotate#AnnotateImageRequest))
and the data returned is a JSON described [here](https://cloud.google.com/vision/docs/reference/rest/v1/images/annotate#annotateimageresponse).

The `2017-02-15-receipts-texts-raw.tar.xz` file found on Serenata de Amor's S3
bucket contains the raw JSON responses returned by the API grouped by
`document_id` and page number:

```javascript
{
  "1": [
    // First element of the array is the full text of the receipt
    {
      "description": "... <FULL TEXT OF THE RECEIPT> ...",
      "boundingPoly": {
        "vertices": [
          // The rectangle where the API found the whole text
          { "y": 469,  "x": 866  },
          { "y": 469,  "x": 1753 },
          { "y": 1413, "x": 1753 },
          { "y": 1413, "x": 866  }
        ]
      },
      "locale": "pt-PT"
    },
    // What folllows is each word found and the location it was found
    {
      "description": "Restaurante",
      "boundingPoly": {
        "vertices": [
          // The rectangle where the API found the word
          { "y": 469, "x": 1009 },
          { "y": 478, "x": 1187 },
          { "y": 518, "x": 1185 },
          { "y": 509, "x": 1007 }
        ]
      }
    },
    // ... other words here ...
  ],
  "2": // Same info for page 2
}
```

Most of the time you'll only use the full text provided by
`2017-02-15-receipts-texts.xz` but, for example, if you want to build some logic
around analysing the text of specific regions of the receipt you're able to do
that with the `x` and `y` coordinates above.

## Challenges with OCRing the Chamber of Deputies receipts

There are many challenges in dealing with OCRed info and more specifically for
the receipts scanned and provided by the Chamber of Deputies we need to keep the
following in mind:

- Many receipts are filled in by hand and unfortunately handwriting is even
  harder to parse than "computer text".
- Some receipts are not scanned carefully and end up being rotated (sometimes it
  is even scanned up side down).
- Some scans have really low quality and / or the receipt gets a bit "faded
  away" due to the thermal paper many places emit, making it harder for the
  computer to guess what's the text in it.

In other words, there is room for (non trivial) improvements on this OCR process
(like some image preprocessing) and there are things we can do ourselves in
order to increase the chances of finding suspicious reimbursements with the PDFs
provided.
