s4 = "My name is Sanjeev Kumar MY"
count4 = {}
 
for ch in s4:
    if ch in count4:
        count4[ch] += 1
    else:
        count4[ch] = 1
 
for key in count4:
    if count4[key] > 1:
        print(f"{key} = {count4[key]}")