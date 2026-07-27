# output: My=3 Sanjeev=2
 
s3 = "My name is sanjeev Sanjeev Sanjeev My My"
words3 = s3.split(" ")
count3 = {}
 
for w in words3:
    if w in count3:
        count3[w] += 1
    else:
        count3[w] = 1
 
for key in count3:
    if count3[key] > 1:
        print(f"{key}={count3[key]}")