s = "my nanaym issi sanjeev"
count = {}

for c in s:
    if c == " ":
        continue

    if c in count:
        count[c] += 1
    else:
        count[c] = 1

Maxchar = ""
Maxcount = 0

for key in count:
    print(f"{key}={count[key]}")

    if count[key] > Maxcount:
        Maxcount = count[key]
        Maxchar = key

print("Maxchar " + Maxchar)
print("Maxcount " + str(Maxcount))

index = s.index(Maxchar)
print("index " + str(index))