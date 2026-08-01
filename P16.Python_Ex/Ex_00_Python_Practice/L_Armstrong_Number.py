n13 = 153
temp13 = n13
rev13 = 0
 
while n13 > 0:
    rem13 = n13 % 10
    rev13 = (rem13 ** 3) + rev13
    n13 = n13 // 10
 
if rev13 == temp13:
    print("Armstrong Number")
else:
    print("Not a Armstrong Number")