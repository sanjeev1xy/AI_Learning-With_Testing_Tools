# output: 1=5, 2=4, 3=2, 7=3, 8=2
 
arr8 = "My Name 1112223 is 77889 Sanjeev 76543112"
count8 = {}
 
for num in arr8:
    if not num.isdigit():
        continue
    if num in count8:
        count8[num] += 1
    else:
        count8[num] = 1
 
for key in count8:
    if count8[key] > 1:
        print(f"{key} = {count8[key]}")