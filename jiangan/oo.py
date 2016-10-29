from jiangan.models import hetong

def check():
    with open('jiangan/data') as f:
        for line in f:
            zkzh, cj, _ = line.split()
            try:
                h = hetong.objects.get(zkzh=zkzh)
                h.bscj = cj
                h.save()
            except Exception as e:
                print(e)
                print(zkzh)

    print('passed...')

            
