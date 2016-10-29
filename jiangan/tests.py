# -*- coding:utf-8 -*-
import xlrd
import os
import itertools
import random
from django.utils.timezone import localtime

# from django.test import TestCase
from accounts.models import User
from .models import hetong, Config

jn = os.path.join
grjls=['''2010年9月-2013年7月，就读于四川中医药高等专科学校
2013年7月-2014年10月，就职于阳春镇上阳村卫生站
2015年2月至今就职于江安县医疗保险局''',
'''2010年9月-2013年6月，就读于成都中医药大学附属医院针灸学校，
2013年6月-2013年9月，就职于中国人民解放军成都军区后勤部第57所护理职位，
2013年9月-2015年7月就职于江安县新农合中心驻怡乐镇合管办工作员，
2015年7月-今就职于江安县医疗保险局驻蟠龙乡医保办工作员。''',
'''1971年9月-1973年7月，就读于桐梓镇中心校
1973年7月-1978年7月，就读于庆福乡阳春小学
1978年7月-1980年7月，就读于庆福乡白沙小学
1980年7月-1982年7月，就读于江安中学
1982年7月-1983年11月，庆福乡阳春村务农
1983年11月-1992年10月，就职于江安县二龙口乡镇府
1992年10月至今，就职于江安县怡乐镇人民政府''',
'''2007年9月-2011年6月在四川农业大学系统学习环境工程专业知识；
2011年6月-2013年4月在江安县工业园区管理委员会办公室规建股任工作员，协助负责园区规划及基础设施建设；
2013年4月-2014年4月在江安县工业园区管理委员会安全管理和环境保护工作组任工作员，协助负责园区安全、环保及基层设施建设；
2014年4月-2015年9月在在江安县工业园区管理委员会安全监管和环境保护局任股长，协助负责园区安全、环保及其他事宜；
2015年9月至今在江安阳春投资开发有限责任公司运营科任科长，协助负责园区污水处理厂、工业渣场等设施运营。''',
'''2002年9月-2005年7月，就读于西昌学院
2005年9月-2015年12月，在四川省江安县产品质量监督检验所就职
2016年1月-2016年3月25日，在四川省江安县食品检测中心就职
2016年3月28日至今，在江安县计量测试所就职''',
'''1995年9月-1998年7月，就读于宜宾农业学校。
1998年8月-2003年8月，就职于江安县国土资源局桐梓国土所。
2003年9月-2003年10月，就职于江安县国土资源局留耕国土资源所。
2003年10月-今，就职于江安县国土资源局工作。''',
]
def s2n(s):
    n=0
    s=s.upper()
    for i, a in enumerate(s[::-1]):
        n+= (ord(a)-64)*26**i
    return n

def n2s(n):
    s=''
    while n:
        div, mod = divmod(n-1, 26)
        s = chr(65+mod) + s
        n = div
    return s

def getset(cell):
    return {v for v in cell.value.split('、') if v}

def getlist(cell):
    return [v for v in cell.value.split('、') if v]

def col(sht, s):
    return sht.col(s2n(s)-1)


def main():
    cd = os.getcwd()
    workbook = xlrd.open_workbook('jiangan/fixture.xlsx')
    sheet = workbook.sheet_by_name('Sheet1')
    User.objects.all().delete()
    for rdex in range(sheet.nrows):
        row = sheet.row_values(rdex)
        xm, sfzh, xb, lxdh, bkgw, xl, byyx, zy, config_id = row
        user = User.objects.create_user('test%s@jarsj.cn' % rdex, row[1], '111111')
        user.is_active = True
        user.save()
        md = hetong
        md.objects.create(
            creater = user,
            check_status = 1,
            config=config_id, 
            bscj = random.randrange(40,70),
            mscj = random.randrange(68,81),
            xm = xm,
            xb   = xb,
            hf    = random.choice(('是', '否')),
            lxdh = lxdh,
            bkgw = bkgw,
            mz   = '汉',
            zzmm = random.choice(('中共党员', '群众')),
            xl = xl,
            xw = random.choice(('学士', '硕士', '研究生','无')),
            bysj = random.choice(('2010-6-22', '1999-6-20','2014-6-1')),
            byyx = byyx,
            zy   = zy,
            stzk = '好',
            cjgzsj = random.choice(('2010-6-22', '1999-6-20','2014-6-1')),
            xgzdwjgw = random.choice(('人社局工作员', '组织部主任','府办主任')),
            jtzz = '四川省宜宾市江安县竹都大道',
            grjl = random.choice(grjls), 
            jcqk = '无',
            jtzycyqk = random.choice((
                '李XX,弟弟,某公司,职员',
                '张XX,母亲,某公司,职员\n李XX,父亲,某政府,主任',
                '张XX,母亲,某公司,职员\n李XX,父亲,某政府,主任\n李XX,弟弟,某公司,职员\n李XX,弟弟,某公司,职员\n李XX,弟弟,某公司,职员\n李XX,弟弟,某公司,职员'
            )), 
        )
    User.objects.create_superuser('admin@jarsj.cn','000000000000000000','111111')
def make_config():
    from datetime import datetime, timedelta
    import pytz

    Config.objects.all().delete()
    now = datetime.now()
    pacific = pytz.timezone('Asia/Shanghai')
    start = now.replace(hour=9,minute=0,second=0)# + timedelta(1)
    end = now.replace(hour=17,minute=0,second=0) + timedelta(4)
    start=pacific.localize(start)
    end=pacific.localize(end)
    cdd={
        'bsmenu':[
            '2016年5月28日(星期六) 上午8:00-12:00, 江安职业技术学校, 公共基础知识',
            '2016年5月29日(星期日) 上午9:00-11:00, 江安县政府, 公共知识',
        ],
        'title':[
            '二O一六年第一次公开招聘劳动合同制工作人员',
            '二O一六年第一次公开考调机关事业单位工作人员',
        ],
        'bkgw':[
            '合同岗位一,1\n合同岗位二,2',
            '考调岗位一,1\n考调岗位二,2\n考调岗位三,3',
        ],
    }
    for index in range(2):
        c=Config(
            title=cdd['title'][index],
            bkgw = cdd['bkgw'][index],
            bsmenu = cdd['bsmenu'][index],
            special_rules = "考生应带好有效居民身份证和准考证及其他考试用品。\n"\
                "考生应在考试当日早上8:30之前到达考室。\n"\
                "考试当日9:30之后考生不得再进入考试参加考试。\n",
            enable = True, 
            model_name = 'hetong',
            submit0 = start,
            submit1 = end,
            pay0 = start,
            pay1 = end,
            detail0 = start,
            detail1 = end,
            zkz0 = start,
            zkz1 = end,
            bscj0 = start,
            bscj1 = end,
            all0 = start,
            all1 = end,
        )
        c.save()
def replace():
    arr=[('proj_create','proj_create'),('proj_update','proj_update'),('proj_detail','proj_detail'),('proj_write_zkzh','proj_write_zkzh')
    ,('proj_write_bspm','proj_write_bspm'),('proj_write_zpm','proj_write_zpm')]
    cd = os.getcwd()
    workbook = xlrd.open_workbook(os.path.join(cd, 'replaces.xls'))
    sheet = workbook.sheet_by_name('Sheet1')
    for r in range(sheet.nrows):
        arr.append([sheet.cell(r,0).value, sheet.cell(r,1).value,])
    print(arr)
    return

    for pt, dirs, fns in os.walk(os.getcwd()):
        for fn in fns:
            p =os.path.join(pt,fn)

            with open(p,'r',encoding='u8') as f:
                s = f.read()
                olds = s
                for old, new in arr:
                    s = s.replace(old, new)


            if s==olds:
                continue
            with open(p,'w',encoding='u8') as f:
                f.write(s)
                print(p)




if __name__ == '__main__':
    main()
    make_config()


