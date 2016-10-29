var SUCCESS_COLOR = "#CCFFCC";
var ERROR_COLOR = "#FDE0E0"; //#c04848 stackoverflow error color
var FORM_ERROR_CLASS = "errorlist";
var FORM_HINT_CLASS = "hintlist";
var TIP_OFFSET_LEFT = 10;

String.prototype.rsplit = function (delimiter, limit) {
  delimiter = this.split (delimiter || /s+/);
  return limit ? delimiter.splice (-limit) : delimiter;
} 

var FormFields = {
    sfzh :{
        hint:'请填写18位身份证号(只能由数字和字母X组成)', 
        validators:[require(),regex(/^\d{17}[\dXx]$/),max_val(5),max_val(5)]
    }, 
    email :{
        hint:'请填写18位身份证号(只能由数字和字母X组成)', 
        validators:[require(),regex(/^\d{17}[\dXx]$/),max_val(5)]
    }, 
    password:{
        hint:'请填写6到32位密码, 只能由数字, 英文字母或半角符号@$_!-组成', 
        validators:[regex(/^[\da-zA-Z@$_!-]{6,32}$/)]
    },
    bscj:{
        validators:[min_val(0),max_val(100), blur_ajax_post()],
    }, 
    message:{
        validators:[require(),  blur_ajax_post()],
    }, 
    jtzycyqk:{
        hint:'按"姓名, 称谓, 工作单位, 职务"格式填写,逗号分隔,\n多个成员换行,没有的项目填\'无\',例如:\n\n父亲,李四,乙企业,总经理\n母亲,张三,甲公司,办公室主任\n弟弟,李五,无,无',
    }, 
    lxdh:{
        hint:'7到11位纯数字',
        validators:[regex(/^\d{7, 11}$/)]
    }
}

function require(message){
    return function(value, name){
        name = name || '';
        message = message || '您还没填写{name}';
        if (value===''){
            return message.replace('{name}',name);
        }
    }
}
function regex(limit, message){
    return function(value, name){
        name = name || '';
        message = message || '{name}格式不正确';
        if (!value.match(limit)){
            return message.replace('{name}',name);
        }
    }
}
function min_len(limit, message){
    return function(value, name){
        name = name || '';
        message = message || '{name}不能少于{limit}个字, 您输入了{value}个';
        value = value.length;
        if (value < limit){
            return message.replace('{limit}',limit).replace('{value}',value).replace('{name}',name);
        }
    }
}
function max_len(limit, message){
    return function(value, name){
        name = name || '';
        message = message || '{name}不能多于{limit}个字, 您输入了{value}个';
        value = value.length;
        if (value > limit){
            return message.replace('{limit}',limit).replace('{value}',value).replace('{name}',name);
        }
    }
}
function min_val(limit, message){
    return function(value, name){
        name = name || '';
        message = message || '{name}值太小, 至少{limit}';
        if (value < limit){
            return message.replace('{limit}',limit).replace('{value}',value).replace('{name}',name);
        }
    }
}
function max_val(limit, message){
    return function(value, name){
        name = name || '';
        message = message || '{name}值太大, 最多{limit}';
        if (value > limit){
            return message.replace('{limit}',limit).replace('{value}',value).replace('{name}',name);
        }
    }
}
function blur_ajax_post(){
    return function(value, name){
        var self = $(this);
        var pk = self.attr('pk');
        name = name || '';
        console.log({name:name, pk:pk, value:value});
        $.ajax({
            type: "POST",
            dataType: "json",
            url: window.location.href,
            data: {name:name, pk:pk, value:value},
            success: function(res) {
                if (res.valid === true) {
                    self.parent('td').css({"background-color":SUCCESS_COLOR}); 
                } else { 
                    $.each(res.errors, function(field, value) {
                        // var self = $('#id_'+field);
                        var ul = $(make_errorlist(value)); 
                        ul.insertAfter(self);
                        ul.css({
                            top  : self.offset().top,
                            left : self.offset().left + self.outerWidth() + 10, 
                            display:'block', 
                            position:'absolute', 
                        });
                    });
                }               
            },
            error: function(xhr, textStatus, errorThrown) {
                alert(textStatus)
            },
        });
    }
}   

function make_validator_calls(validators){
    return function(){
        var self = $(this);
        var value = self.val(); // input value
        var name  = $('label[for="'+self.attr('id')+'"').html() || self.attr('name') || '';
        var li_string = '';
        for (var i = 0; i < validators.length; i++){
            var error_message = validators[i].call(this, value, name);
            if (error_message){
                li_string += '<li>'+error_message+'</li>';
                break;
            }
        }
        self.next('.'+FORM_ERROR_CLASS+', .'+FORM_HINT_CLASS).remove(); // remove existing error or hint
        if (li_string.length != 0){
            // tr.css({"background-color":ERROR_COLOR});
            var ul = $('<ul class="'+FORM_ERROR_CLASS+'">'+li_string+'</ul>');
            ul.insertAfter(self);
            //console.log(self.offset().top, self.offset().left,self.width())
            ul.css({
                top  : self.offset().top,
                left : self.offset().left + self.outerWidth() + TIP_OFFSET_LEFT, 
                display:'block', 
                position:'absolute', 
            });
        }
    }
}
function make_hint_call(hint_message){
    return function(){
            var self  = $(this);
        //console.log(self.next().length);
        if (self.next().length===0){
            var ul = $('<ul class="'+FORM_HINT_CLASS+'"><li>'+hint_message+'</li></ul>');
            ul.insertAfter(self);
            //console.log(self.offset().top, self.offset().left,self.width())
            ul.css({
                top :self.offset().top,
                left:self.offset().left + self.outerWidth() + TIP_OFFSET_LEFT, 
                display:'block', 
                position:'absolute', 
            });
        }
    }
}


// $("input[name='sfzh']").blur(function() {
//     var tr = $(this).parents('tr');
//     var color = rgb2hex(tr.css("background-color"));
//     // 只要背景色不是错误色, 就清除
//     var value=$(this).val();

//     console.log(value);
//     if (value.length!=11){
//         tr.css({"background-color":ERROR_COLOR,});
//         tr.find('pre').empty();
//         tr.find('pre').append('手机号码位数应为11位, 目前'+value.length+'位')
//     }else{
//         tr.css({"background-color":'transparent',});
//         tr.find('pre').empty();        
//     }
// })

function rgb2hex(rgbs){
    if (!rgbs){
        return '#FFFFFF';
    }
    rgb = rgbs.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
    //console.log('match', typeof(rgbs), rgbs, typeof(rgb), rgb);
    if (rgb == null) {
        return '#FFFFFF';
    }
    return "#" + rgbToHex(parseInt(rgb[1],10),parseInt(rgb[2],10),parseInt(rgb[3],10));
}
function rgbToHex(R,G,B) {return toHex(R)+toHex(G)+toHex(B)}
function toHex(n) {
    n = parseInt(n,10);
    if (isNaN(n)) return "00";
    n = Math.max(0,Math.min(n,255));
    return "0123456789ABCDEF".charAt((n-n%16)/16)  + "0123456789ABCDEF".charAt(n%16);
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function sameOrigin(url) {
    var host = document.location.host;
    var protocol = document.location.protocol;
    var sr_origin = '//' + host;
    var origin = protocol + sr_origin;
    return (url == origin || url.slice(0, origin.length + 1) == origin + '/') || (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') || !(/^(\/\/|http:|https:).*/.test(url));
}
var csrftoken = getCookie('csrftoken');
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function make_hint(name){
    var value = hint_dict[name];
    return value?'<div class="'+FORM_HINT_CLASS+'">'+value+'</div>':'';
}
function make_errorlist(value) {
    var estr = '';
    $.each(value, function(i, v) {
        estr += '<li>' + v + '</li>'
    });
    return '<ul class="'+FORM_ERROR_CLASS+'">' + estr + '</ul>';
}


function make_logout_menu() {
    var estr ="";
    estr += '<li><a href="/accounts/" title=""> 我的账号 </a></li> '
    estr += '<li><a href="/accounts/logout/" title=""> 注销 </a></li> ';
    return '<ul class="vmenu dynamic_menu">' + estr + '</ul>';
}

function make_login_menu() {
    var estr ="";
    estr += '<li><a href="/accounts/login/" title=""> 登录 </a></li> '
    estr += '<li><a href="/accounts/register/" title=""> 注册 </a></li> ';
    return '<ul class="vmenu dynamic_menu">' + estr + '</ul>';
}

$(document).ready(function() {
    $.each(FormFields, function(key, value){
        if (value.validators){
            $('*[name='+key+']').blur(make_validator_calls(value.validators));
        }
        if (value.hint){
            $('*[name='+key+']').focus(make_hint_call(value.hint));
        }
    });

    $("form.simple-form").submit(function(e) { //为了能够兼容firefox,这个函数加了e参数.
        var fm = $(this);
        var event = window.event || e;
        if (event.preventDefault){
            event.preventDefault();
        } else if(FormData===undefined){
            // event.returnValue = false;
            return; //由于IE10以下不支持FormData,这里直接返回了.
        }else{
            event.returnValue = false;
        }
        $.ajax({
            type: "POST",
            dataType: "json",
            url: window.location.href,
            data: new FormData(fm[0]),
            cache: false,
            contentType: false,// 必设定,否则出错
            processData: false,// 必设定,否则出错
            //async: false,
            success: function(res) {
                if (res.valid == true) {
                    window.location.replace(res.url);
                } else {
                    $('.'+FORM_HINT_CLASS).remove(); //清除填写提示
                    $('.'+FORM_ERROR_CLASS).remove(); //清除错误提示
                    //fm.find('tr').removeAttr("style"); //删除js设置的动态属性
                    var errors = res.errors;
                    if (errors.__all__){
                        $(make_errorlist(errors.__all__)).insertBefore($('table'));
                    }else{
                        $.each(errors, function(field, value) {
                            var self = $('#id_'+field);
                            var ul = $(make_errorlist(value)); //pre 框内插入出错信息
                            ul.insertAfter(self);
                            //console.log(self.offset().top, self.offset().left,self.width())
                            ul.css({
                                top  : self.offset().top,
                                left : self.offset().left + self.outerWidth() + 10, 
                                display:'block', 
                                position:'absolute', 
                            });
                        });
                        var fir = $('.'+FORM_ERROR_CLASS).first().prev(); //获取首个出错信息元素
                        fir.focus();
                    }
                }
            },
            error: function(xhr, textStatus, errorThrown) {
                alert(textStatus)
            },
        })
})

$(".popup").on('click', function() {
    var ms = $('.dynamic_menu');
    if (ms.length != 0){
            //console.log('move out');
            $('.dynamic_menu').remove();           
        } else {
            //console.log('move in');
            var pop_area = $(this);
            $.ajax({
                type: "get",
                dataType: "json",
                url: "/accounts/is_login/",
                success: function(res) {
                    if (res.login == true) {
                        var tmp = $(make_logout_menu());
                    } else { 
                        var tmp = $(make_login_menu());
                    }  
                    tmp.insertAfter(pop_area)             
                },
                error: function(xhr, textStatus, errorThrown) {
                    alert(textStatus)
                },
            });
        }
    })

})