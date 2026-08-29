n4 = 5
a2 = 0
b2 = 1
 
print("Fibonacci numbers are : ")
print(f"{a2} {b2}")
 
for i in range(1, n4 + 1):
    c2 = a2 + b2
    print(f"{c2}")
    a2 = b2
    b2 = c2