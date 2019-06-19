from PIL import Image
import math

#Importing Image from the same folder
img=Image.open("source.png")
img.format = "PNG"
print(img.size)

#Converting image to greyscale
greyimg = img.convert('LA')

#resizing the greyscale image to 256 x 256 pixels
fimg = greyimg.resize((256,256))
width, height = fimg.size
print("width is ",width)
print("height is",height)
fimg.show()

#Converting pixel values of image in numpy matrix "arr"
import numpy as np

arr = np.empty((256,256), dtype=np.uint8)

for i in range(0,height):
    for j in range(0,width):
        pxl = fimg.getpixel((j,i))
        arr[i][j] = pxl[0]
    
print(arr)

##########     CREATING CHAOTIC METRICES "hmap" OR CHAOTIC SEQUENCES
# multiplying by 10^8 and mod by 256 to bring the values in 0-255 pixel range

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

##########     HCST ALGORITHM : (a) Column pixel scrambling and (b) Row pixel scrambling
# (a) cyclic shifting columns in "arr" using "hmapx" matrix and storing result in "arr1"
arr1 = np.empty((256,256), dtype=np.uint8)
for i in range(0,256):
    if(hmapxf[i]%2 == 0):
        sh = abs(hmapxf[i])
        for j in range(0,256):
            arr1[j][i] = arr[(j+sh)%256][i] #down cyclic column shift
    else:
        sh = abs(hmapxf[i])
        for j in range(0,256):
            arr1[j][i] = arr[(j-sh)%256][i] #up cyclic column shift
            

# (b) cyclic shifting rows in "arr1" using "hmapy" matrix and storing result in "arr2"
arr2 = np.empty((256,256), dtype=np.uint8)
for j in range(0,256):
    if(hmapyf[j]%2 == 0):
        sh = abs(hmapyf[j])
        for i in range(0,256):
            arr2[j][i] = arr1[j][(i+sh)%256] #right cyclic row shift
    else:
        sh = abs(hmapyf[j])
        for i in range(0,256):
            arr2[j][i] = arr1[j][(i-sh)%256]#left cyclic row shift


##########    BOUNDARY PIXEL SUBSTITUTION :
# replacing first and last row of arr2 by using chaotic sequences.
# XORing chaotic "hmapxf" by first row and "hmapyf" by last row of "arr2"

for i in range(0,256):
    arr2[0][i]^=hmapxf[i]
    arr2[255][i]^=hmapyf[i]


##########     SHIFT ROW TRANSFORMATION :
#shifting rows to left according to the row numbers

arr3 = np.empty((256,256), dtype=np.uint8)
for i in range(0,256):
    for j in range(0,256):
        arr3[i][j]=arr2[i][(j-i)%256] #leftshift according to row number


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


##########     RANDOM PIXEL DIFFUSION ALGORITHM OR FIRST LEVEL DIFFUSION :
# taking sine map "smapf: and image matrix "arr3"

arr4 = np.empty((256,256), dtype=np.uint8)

for i in range(0,256):
    for j in range(0,256):
        if (i>=2 and i<=254) and (j>=2 and j<=254):
            arr4[i][j]=arr3[i][j]^smapf[i-1][255]
            arr4[i][j]^=smapf[i][j+1]
        else:
            arr4[i][j]=arr3[i][j]


##########     DIAGONAL SCAN TRANSFORMATION :

arr5 = np.empty((256,256), dtype=np.uint8)
brr = np.empty((65536), dtype=np.uint8)

brr[0] = arr4[0][0]
n=1
flag=0
i=j=0
while flag!=2:
    if flag==0 and n!=65535:
        if i!=255:
            i+=1
        else:
            j+=1
        x=j-1
        while i!=x:
            brr[n]=arr4[i][j]
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
            brr[n]=arr4[i][j]
            i+=1
            j-=1
            n+=1
        i-=1
        j+=1
        flag=0
    if n==65535:
        flag=2
brr[65535]=arr4[255][255]

n=0
for i in range(0,256):
    for j in range(0,256):
        arr5[i][j]=brr[n]
        n+=1
                    

##########     SECOND LEVEL DIFFUSION

arr6 = np.empty((256,256), dtype=np.uint8)

for j in range(0,256):
    for k in range(0,256):
        if j==0 and k==0:
            arr6[j][k]= arr5[j][k]^smapf[j][k]
        elif k==0:
            arr6[j][k]=arr5[j-1][255]^arr5[j][k]^smapf[j][k]
        else:
            arr6[j][k]=arr5[j][k-1]^arr5[j][k]^smapf[j][k]
                
enimg = Image.fromarray(arr6)
enimg.show()
enimg.save("encrypted.png")

#here enimg3 is the final encrypted image. Now using the secret key [x,y,b1,b2,z,r], the
# decryption can be proceeded
    
    