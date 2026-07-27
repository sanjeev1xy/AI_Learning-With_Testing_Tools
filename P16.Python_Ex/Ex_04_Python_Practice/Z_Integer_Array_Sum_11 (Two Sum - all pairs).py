# I/P = 4, 9, 3, 2, 5, 6, 11, 0, 12, -1
# O/P = 9 + 2 = 11, 2 + 9 = 11, 5 + 6 = 11, 6 + 5 = 11,
#       11 + 0 = 11, 0 + 11 = 11, 12 + -1 = 11, -1 + 12 = 11
 
intarr1 = [4, 9, 3, 2, 5, 6, 11, 0, 12, -1]
target1 = 11
 
for i in range(len(intarr1)):
    for j in range(len(intarr1)):
        if intarr1[i] + intarr1[j] == target1:
            print(f"{intarr1[i]} + {intarr1[j]} = {target1}")