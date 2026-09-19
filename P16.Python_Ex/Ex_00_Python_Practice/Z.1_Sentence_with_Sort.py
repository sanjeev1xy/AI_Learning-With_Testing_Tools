arr=["kiwi","sweet","fig"," ","orange","banana"," "];

for i in range(len(arr)):
  for j in range(i+1,len(arr)):
    if arr[i]>arr[j]:
      t=arr[i];
      arr[i]=arr[j];
      arr[j]=t;
for i in range(len(arr)):

  #print("["+arr[i]+"],");
  print(arr[i]+",");
