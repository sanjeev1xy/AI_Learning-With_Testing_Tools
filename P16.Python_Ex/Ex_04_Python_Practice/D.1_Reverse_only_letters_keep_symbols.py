# output=vee@#j$na%^&S
 
s9 = "My na@m!e is San)jeev"
letter = ""
 
for i in range(len(s9)):
    if s9[i].isalpha():
        letter = s9[i] + letter
 
index = 0
revstr7 = ""
 
for i in range(len(s9)):
    if s9[i].isalpha():
        revstr7 = revstr7 + letter[index]
        index += 1
    else:
        revstr7 = revstr7 + s9[i]
 
print(revstr7)