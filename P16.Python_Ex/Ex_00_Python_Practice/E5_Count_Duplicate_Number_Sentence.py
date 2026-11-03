# output: 
# -1 = 2
# 0 = 2
 
arr8=[1,2,3,4,5,6,-1,-5,0,-1,0];
count8 = {}
 
for num in arr8:
    if num in count8:
        count8[num] += 1
    else:
        count8[num] = 1
 
for key in count8:
    if count8[key] > 1:
        print(f"{key} = {count8[key]}")