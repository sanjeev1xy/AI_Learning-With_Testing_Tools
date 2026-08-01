# O/P: S=1 a=1 n=1 j=1 e=2 v=1
 
str5 = "Sanjeev"
count5 = {}
 
for ch in str5:
    if ch in count5:
        count5[ch] += 1
    else:
        count5[ch] = 1
 
for key in count5:
    print(f"{key} = {count5[key]}")