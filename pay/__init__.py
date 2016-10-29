# from urllib import urlencode, urlopen
from urllib.request import urlopen
from urllib.parse import urlencode

from hashlib import md5

appname = __file__.replace('\\','/').rsplit('/',2)[1]

GATEWAY = 'https://mapi.alipay.com/gateway.do?'
KEY = 'q0iw5a2wgpfut4b69ilhbpat969cs3rh'
SIGN_TYPE  =  'MD5'

config = dict(
    service = "create_direct_pay_by_user",
    partner = "2088121051398798",
    seller_id = "2088121051398798",
    _input_charset = "utf-8",
    notify_url = "http://www.wdksw.com/pay/notify/",
    return_url = "http://www.wdksw.com/pay/return/",
    payment_type = "1",
    it_b_pay = "7d", 
)


# 对数组排序并除去数组中的空值和签名参数
# 返回数组和链接串
def kwargs_filter(kwargs):
    newkwargs = {}
    prestr = ''
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        if k not in ('sign','sign_type') and v != '':
            newkwargs[k] = v
            prestr += '%s=%s&' % (k, v)
    return newkwargs, prestr[:-1]

# 生成签名结果
def build_mysign(prestr):
    return md5((prestr + KEY).encode(encoding='u8')).hexdigest()


'''
service 接口名称    String  接口名称。   不可空
partner 合作者身份ID String(16)  签约的支付宝账号对应的支付宝唯一用户号。    不可空
_input_charset  参数编码字符集 String  商户网站使用的编码格式，如utf-8、gbk、gb2312等。 不可空
sign_type   签名方式    String  DSA、RSA、MD5三个值可选，必须大写。  不可空
sign    签名  String  请参见签名。  不可空
out_trade_no    商户网站唯一订单号   String(64)  支付宝合作商户网站唯一订单号。 不可空
subject 商品名称    String(256) 商品的标题/交易标题/订单标题/订单关键字等。 不可空
payment_type    支付类型    String(4)   取值范围请参见附录收款类型。  不可空
total_fee   交易金额    Number  该笔订单的资金总额，单位为RMB-Yuan。取值范围为[0.01，100000000.00]，精确到小数点后两位。   不可空
seller_id   卖家支付宝用户号    String(16)  seller_id是以2088开头的纯16位数字。   不可空
'''

def get_pay_url(**kwargs):
    # kwargs是订单号,费用和主题.来自考试app的pay视图
    kwargs.update(config)
    kwargs, prestr = kwargs_filter(kwargs)
    kwargs['sign'] = build_mysign(prestr)
    kwargs['sign_type'] = SIGN_TYPE
    return GATEWAY + urlencode(kwargs)

# http://www.wdksw.com/return/?body=%E8%80%83%E8%AF%95%E7%BC%B4%E8%B4%B9&buyer_email=xiangnanscu%40163.com&buyer_id=2088312457738495&exterface=create_direct_pay_by_user&is_success=T&notify_id=RqPnCoPT3K9%252Fvwbh3InVZqz1t%252FVKqeGJsCb1L5%252Bj77ZQqq%252BbrfufTnQQCOMd3QVilXPU&notify_time=2015-11-25+18%3A55%3A47&notify_type=trade_status_sync&out_trade_no=20151125185132886944&payment_type=1&seller_email=lzwlkj%40aliyun.com&seller_id=2088121051398798&subject=%E6%B1%9F%E5%AE%89%E5%8E%BF2015%E5%B9%B4%E7%AC%AC%E4%B8%89%E6%AC%A1%E5%85%AC%E5%BC%80%E6%8B%9B%E8%81%98%E5%8A%B3%E5%8A%A8%E5%90%88%E5%90%8C%E5%88%B6%E5%B7%A5%E4%BD%9C%E4%BA%BA%E5%91%98&total_fee=0.10&trade_no=2015112521001004490251562565&trade_status=TRADE_SUCCESS&sign=a2044643729c505b3bf6831b47fd2180&sign_type=MD5
def notify_verify(post):
    # 初级验证--签名
    _, prestr = kwargs_filter(post)
    mysign = build_mysign(prestr)
    if mysign != post.get('sign'):
        return False
    # 二级验证--查询支付宝服务器此条信息是否有效
    params = {}
    params['partner'] = config['partner']
    params['service'] = 'notify_verify'
    params['notify_id'] = post.get('notify_id')
    veryfy_result = urlopen(GATEWAY + urlencode(params)).read()
    #print('in notify_verify, veryfy_result is:',veryfy_result)
    if veryfy_result.lower().strip() == b'true':
        return True
    return False