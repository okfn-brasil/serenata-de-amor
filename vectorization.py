# Outer product 
import time 
import numpy 
import array 

a = array.array('i') 
for i in range(200): 
	a.append(i); 

b = array.array('i') 
for i in range(200, 400): 
	b.append(i) 

# classic outer product of vectors implementation 
tic = time.process_time() 
outer_product = numpy.zeros((200, 200)) 

for i in range(len(a)): 
for j in range(len(b)): 
	outer_product[i][j]= a[i]*b[j] 

toc = time.process_time() 

print("outer_product = "+ str(outer_product)); 
print("Computation time = "+str(1000*(toc - tic ))+"ms") 

n_tic = time.process_time() 
outer_product = numpy.outer(a, b) 
n_toc = time.process_time() 

print("outer_product = "+str(outer_product)); 
print("\nComputation time = "+str(1000*(n_toc - n_tic ))+"ms") 

