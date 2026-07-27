s = "swiss"
count = {}
 
for c in s:
    if c in count:
        count[c] += 1
    else:
        count[c] = 1
 
result = None
for c in s:
    if count[c] == 1:
        result = c
        break
 
print(result)   # 'w' for "swiss", None for "aabb"