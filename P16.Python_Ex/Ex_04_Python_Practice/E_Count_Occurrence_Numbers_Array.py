# O/P: 10 = 3, 20 = 2, 30 = 1, 40 = 1
 
arr2 = [10, 20, 30, 10, 20, 10, 40]
count2 = {}
 
for num in arr2:
    if num in count2:
        count2[num] += 1
    else:
        count2[num] = 1
 
for key in count2:
    print(f"{key} = {count2[key]}")