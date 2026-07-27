s14 = "madam"
orgstr14 = s14
revstr14 = ""
 
for i in range(len(s14) - 1, -1, -1):
    revstr14 = revstr14 + s14[i]
 
if orgstr14 == revstr14:
    print("palindrome String")
else:
    print("this is not a Palindrom String")