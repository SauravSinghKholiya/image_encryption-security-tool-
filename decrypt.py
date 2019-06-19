# Now using the secret key [x,y,b1,b2,z,r], the decryption can be proceeded

import math
import numpy as np  

#Creating modified hanon map matrix "hmap"

hmapx = np.empty((256), dtype=np.float)
hmapy = np.empty((256), dtype=np.float)

def MHM(x,y,b1,b2):
    for k in range(0,256):
        hmapx[k] = x 
        hmapy[k] = y
        orgy = y
        y = -x
        x = (1 - (b1*math.cos(x)) - (b2*orgy) ) 
 
MHM(100,200,2.87,0.3)

print(hmapx)

hmapxf = np.empty((256), dtype=np.uint32)
for i in range(0,256):
    hmapxf[i] = round((hmapx[i]*1000000000)%256)
    
print(hmapxf)

print(hmapy)

hmapyf = np.empty((256), dtype=np.uint32)
for i in range(0,256):
    hmapyf[i] = round((hmapy[i]*1000000000)%256)
    
print(hmapyf)    


##########     CREATING SINE MAP "smap" :

smap = np.empty((256,256), dtype=np.float)

def SM(z,r):
    for m in range(0,256):
        for n in range(0,256):
            smap[m][n] = z
            z = (r*math.sin(math.pi * z))   
 
SM(300,0.88)

#now making transformed sine matrix "smapf" using original sine values from "smap"
smapf = np.empty((256,256), dtype=np.uint8)
for i in range(0,256):
    for j in range(0,256):
        smapf[i][j] = round((smap[i][j]*1000000000)%256)
    
print(smapf)


#importing the encrypted image
    
from PIL import Image
    
img = Image.open("encrypted.png")
img.format = "PNG"

   
#extracting pixels values of image into a numpy matrix "arr"
    
rarr = np.empty((256,256), dtype=np.uint8)
width, height = img.size
for i in range(0,height):
    for j in range(0,width):
        pxl = img.getpixel((j,i))
        rarr[i][j] = pxl
        
print(rarr)
    
##########     REVERSING SECOND LEVEL DIFFUSION

rarr1 = np.empty((256,256), dtype=np.uint8)

for j in range(0,256):
    for k in range(0,256):
        if j==0 and k==0:
            rarr1[j][k]= rarr[j][k]^smapf[j][k]
        elif k==0:
            rarr1[j][k]=rarr[j][k]^smapf[j][k]^rarr1[j-1][255]
        else:
            rarr1[j][k]=rarr[j][k]^smapf[j][k]^rarr1[j][k-1]
        
    
 #####    REVERSE DIAGONAL SCAN TRANSFORMATION :

rarr2 = np.empty((256,256), dtype=np.uint8)
rbrr = np.empty((65536), dtype=np.uint8)
 
n=0
for i in range(0,256):
    for j in range(0,256):
        rbrr[n]=rarr1[i][j]
        n+=1

flag=0
i=j=0
n=1
rarr2[0][0]=rbrr[0]
while flag!=2:
    if flag==0 and n!=65535:
        if i!=255:
            i+=1
        else:
             j+=1
        x=j-1
        while i!=x:
            rarr2[i][j]=rbrr[n]
            i-=1
            j+=1
            n+=1
        i+=1
        j-=1
        flag=1
    if flag==1 and n!=65535:
        if j!=255:
            j+=1
        else:
            i+=1
        x=i-1
        while j!=x:
            rarr2[i][j]=rbrr[n]
            i+=1
            j-=1
            n+=1
        i-=1
        j+=1
        flag=0
    if n==65535:
        flag=2
rarr2[255][255]=rbrr[65535]

print(rarr2)


##########     REVERSE RANDOM PIXEL DIFFUSION ALGORITHM OR FIRST LEVEL DIFFUSION :

rarr3 = np.empty((256,256), dtype=np.uint8)

for i in range(0,256):
    for j in range(0,256):
        if (i>=2 and i<=254) and (j>=2 and j<=254):
            rarr3[i][j]=rarr2[i][j]^smapf[i-1][255]
            rarr3[i][j]^=smapf[i][j+1]
        else:
            rarr3[i][j]=rarr2[i][j]
            
print(rarr3)

##########     REVERSE SHIFT ROW TRANSFORMATION :
#shifting rows to right according to the row numbers

rarr4 = np.empty((256,256), dtype=np.uint8)
for i in range(0,256):
    for j in range(0,256):
        rarr4[i][j]=rarr3[i][(j+i)%256] #rightshift according to row number
        
##########    REVERSE BOUNDARY PIXEL SUBSTITUTION :
# replacing first and last row of rarr4 by using chaotic sequences.
# XORing chaotic "hmapxf" by first row and "hmapyf" by last row of "rarr4"

for i in range(0,256):
    rarr4[0][i]^=hmapxf[i]
    rarr4[255][i]^=hmapyf[i]


##########    REVERSE  HCST ALGORITHM : (a) Row pixel scrambling  and (b) Column pixel scrambling

# (a) cyclic shifting rows in "rarr4" using "hmapy" matrix and storing result in "rarr5"
rarr5 = np.empty((256,256), dtype=np.uint8)
for j in range(0,256):
    if(hmapyf[j]%2 == 0):
        sh = abs(hmapyf[j])
        for i in range(0,256):
            rarr5[j][i] = rarr4[j][(i-sh)%256]#left cyclic row shift
    else:
        sh = abs(hmapyf[j])
        for i in range(0,256):
            rarr5[j][i] = rarr4[j][(i+sh)%256] #right cyclic row shift            

# (b) cyclic shifting columns in "rarr5" using "hmapx" matrix and storing result in "rarr6"
rarr6 = np.empty((256,256), dtype=np.uint8)
for i in range(0,256):
    if(hmapxf[i]%2 == 0):
        sh = abs(hmapxf[i])
        for j in range(0,256):
            rarr6[j][i] = rarr5[(j-sh)%256][i] #up cyclic column shift
    else:
        sh = abs(hmapxf[i])
        for j in range(0,256):
            rarr6[j][i] = rarr5[(j+sh)%256][i] #down cyclic column shift
            
# Converting decrypted array "rarr6" back to image

decimg1 = Image.fromarray(rarr6)
decimg1.show()
decimg1.save("decrypted.png")
