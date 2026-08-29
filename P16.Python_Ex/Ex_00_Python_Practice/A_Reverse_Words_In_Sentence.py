# I/P = My name is Sanjeev
# O/P = yM eman si veejnaS
 
s = "My name is Sanjeev"
s1 = s.split(" ")
revstr = ""
 
for w in s1:
    revword = ""
    for i in range(len(w) - 1, -1, -1):
        revword = revword + w[i]
        
    revstr = revstr + revword + " "
 
print(revstr)