n7 = 6754
temp7 = n7
rev7 = 0
 
while temp7 != 0:
    rem7 = temp7 % 10
    rev7 = rev7 * 10 + rem7
    temp7 = temp7 // 10
 
print("Original Number is " + str(n7))
print("Reverse Number is " + str(rev7))