n6 = 7
t = 0
 
for i in range(2, n6 - 1):
    if n6 % i == 0:
        t = t + 1
 
if t > 0:
    print("Not a Prime Number")
else:
    print("prime number")