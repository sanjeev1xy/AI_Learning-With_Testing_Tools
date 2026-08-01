n = 121
temp = n
rem = 0
rev = 0
 
while temp != 0:
    rem = temp % 10
    rev = rev * 10 + rem
    temp = temp // 10
 
if n == rev:
    print("This is palindrome number")
else:
    print("This is not a palindrome number")