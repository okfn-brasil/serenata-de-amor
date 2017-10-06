
# coding: utf-8

# # This notebook aims to detect duplicate reimbursements.
# 
# ## To do so i took the following paper as base:
# 1) B. Wang, Z. Li, M. Li and W. y. Ma, "Large-Scale Duplicate Detection for Web Image Search," 2006 IEEE International Conference on Multimedia and Expo, Toronto, Ont., 2006, pp. 353-356.
# doi: 10.1109/ICME.2006.262509
# link: https://pdfs.semanticscholar.org/32fe/c74b6e319921672aa7f6ca2d2598bf92120d.pdf
# 
# They are generating hash code to detect duplicate image. Thus, i found some python libraries which do the same. 
# 
# Dash Python library to calculate the difference hash (perceptual hash) for a given image, useful for detecting duplicates. (https://github.com/Jetsetter/dhash)
# 
# 

# # Necessary imports

# In[1]:

from io import BytesIO
from urllib.request import urlopen
import dhash
from PIL import Image as pil_image
from wand.image import Image
from PIL import ImageFilter


# # Function to download the pdf and convert it to PNG

# In[2]:

def download_doc(url_link):
            try:
                # Open the resquest and get the file
                response = urlopen(url_link)
                # Default arguments to read the file and has a good resolution
                with Image(file=response, resolution=300) as img:
                    img.compression_quality = 99
                    # Chosen format to convert pdf to image
                    with img.convert('png') as converted:
                        # Converts the Wand image to PIL image
                        data = pil_image.open(BytesIO(converted.make_blob()))
                        data = data.convert('RGB')
                        hw_tuple = (800,600)
                        # Resizing of PIL image to fit our ML model
                        if data.size != hw_tuple:
                            data = data.resize(hw_tuple)
                        return data
            except Exception as ex:
                print("Error during pdf download")
                print(ex)
                # Case we get some exception we return None
                return None

def hamming2(s1, s2):
    """Calculate the Hamming distance between two bit strings"""
    assert len(s1) == len(s2)
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))


# # Duplicated Reimbursement
# 
# As duplicate i'm applying a BLUR filter in the downloaded reimbursement. Therefore, the reimbursement is the same, but with different image resolution!
# 

# In[3]:

doc1 = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/2437/2015/5645173.pdf'


# In[4]:

# Original
image1 = download_doc(doc1)

# Duplicate
image2 = image1.filter(ImageFilter.BLUR)


# # Detection!

# In[5]:

dhash.force_pil()

size = 8

row, col = dhash.dhash_row_col(image1)
hash1 = dhash.format_hex(row, col,size=size)
print(hash1)
row, col = dhash.dhash_row_col(image2)
hash2 = dhash.format_hex(row, col,size=size)
print(hash2)
num_bits_different = hamming2(hash1, hash2)
print(num_bits_different)
print('{} {} out of {} ({:.1f}%)'.format(
                num_bits_different,
                'bit differs' if num_bits_different == 1 else 'bits differ',
                size * size * 2,
                100 * num_bits_different / (size * size * 2)))


# # Using documents which looks close, however they are different!
# 
# document_ids: 5886345 and 5886361.

# In[6]:

doc1 = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/3074/2015/5886345.pdf'
doc2 = 'http://www.camara.gov.br/cota-parlamentar/documentos/publ/3074/2015/5886361.pdf'


# In[7]:

image1 = download_doc(doc1)
image2 = download_doc(doc2)


# # Detection!

# In[8]:

dhash.force_pil()

size = 8

row, col = dhash.dhash_row_col(image1)
hash1 = dhash.format_hex(row, col,size=size)
print(hash1)
row, col = dhash.dhash_row_col(image2)
hash2 = dhash.format_hex(row, col,size=size)
print(hash2)
num_bits_different = hamming2(hash1, hash2)
print(num_bits_different)
print('{} {} out of {} ({:.1f}%)'.format(
                num_bits_different,
                'bit differs' if num_bits_different == 1 else 'bits differ',
                size * size * 2,
                100 * num_bits_different / (size * size * 2)))


# # Conclusion 
# 
# I’ve found that the dhash is great for detecting near duplicates (using a size 8 dhash with a maximum delta of 2 bits). But because of the simplicity of the algorithm, it’s not great at finding similar images or duplicate-but-cropped images – you’d need a more sophisticated image fingerprint if you want that. However, the dhash is good for finding exact duplicates and near duplicates, for example, the same image with slightly altered lighting, a few pixels of cropping, or very light photoshopping.

# # Possible direction

# I suggest to take a look in the follwing paper:
#     
# Pratim Ghosh, E. Drelie Gelasca, K.R. Ramakrisnan and B.S. Manjunath,
# “Duplicate Image Detection in Large Scale Databases”,
# Book Chapter in Platinum Jubilee Volume, Indian Statistical Institute, Kolkata, Oct. 2007.
#     
# https://vision.ece.ucsb.edu/sites/vision.ece.ucsb.edu/files/publications/pratim_2007_book.pdf

# In[ ]:



