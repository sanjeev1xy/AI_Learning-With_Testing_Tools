# O/P: My=2 name=2 is=1
 
str_ = "My name is My name"
words = str_.split(" ")
count = {}
 
for word in words:
    if word in count:
        count[word] += 1
    else:
        count[word] = 1
 
for key in count:
    print(f"{key} = {count[key]}")