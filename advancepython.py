import io
text="hi lets start"
file1=io.StringIO(text)
chk=file1.read()
print(file1)
print(chk)

import os
chk2=os.getcwd()
print(chk2)
chk3=os.listdir()
print(chk3,"\n","------")
print(dir(io))
print("------\n\n\n")
print(dir(os))
print("-----------end-----------")
