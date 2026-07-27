n5 = [1, 2, 4, 5, 6]
 
sum2 = 0
for i in range(len(n5)):
    sum2 = sum2 + n5[i]
print("Sum2 is numbers : " + str(sum2))
 
sum3 = 0
for i in range(1, 7):
    sum3 = sum3 + i
print("Sum3 is numbers : " + str(sum3))
 
print("Missing number is : " + str(sum3 - sum2))