import re
import os


def replace():
    for old, new in [('sfzh','sfzh')]:
        arr = []
        for root,dirs,files in os.walk(os.getcwd()):
            for filespath in files:
                change = False
                p = os.path.join(root,filespath)
                if p[-3:] in ['pyc']:
                    continue
                with open(p,encoding='u8') as f:
                    s = f.read()
                    if old in s:
                        change = True

                if change:
                    print(p)
                    open(p,'w',encoding='u8').write(s.replace(old, new))
                    

def search():
    for old in ['changning',]:
        arr = []
        for root,dirs,files in os.walk(os.getcwd()):
            for filespath in files:
                p = os.path.join(root,filespath)
                if p[-3:] not in ['.py','html','css','.js']:
                    continue
                with open(p,encoding='u8') as f:
                    s = f.read()
                    if old in s:
                        print(p)

#search()


    
