# I/P = My name is Sanjeev Kumar Thakur
# O/P = My eman is veejnaS Kumar rukahT
 
st = "My name is Sanjeev Kumar Thakur"
st1 = st.split(" ")
revstr1 = ""
 
for i in range(len(st1)):
    revword = st1[i]
    if i % 2 == 1:
        revstr2 = ""
        for j in range(len(revword) - 1, -1, -1):
            revstr2 = revstr2 + revword[j]
        revstr1 = revstr1 + revstr2 + " "
    else:
        revstr1 = revstr1 + revword + " "
 
print(revstr1)