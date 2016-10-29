var SUCCESS_COLOR = "#CCFFCC";
var ERROR_COLOR = "#FDE0E0"; //#c04848 stackoverflow error color
var FORM_ERROR_CLASS = "errorlist";
var FORM_HINT_CLASS = "hintlist";
var TIP_OFFSET_LEFT = 10;
var PASS_THIS = {};

var form_fields = {
    zgzs :{
        hint:'有何资格证书, 例如教师资格证. 没有则不用填写.'
    },
    bysj :{
        hint:'按年-月-日格式填写, 例如:2010-9-10', 
        validators:[required, regex(/^[12]\d{3}-\d{1,2}-[0123]?\d$/)]
    },
    sfzh :{
        hint:'18位, 只能由数字和字母X组成.', 
        validators:[required, regex(/^\d{17}[\dXx]$/)]
    }, 
    email :{
        hint:'请填写常用邮箱, 用于找回密码', 
        validators:[required, regex(/^\S+@\S+[\.][0-9a-z]+$/)]
    }, 
    xm :{
        validators:[required]
    },
    password:{
        hint:'请填写6到32位密码, 只能由数字, 英文字母或半角符号@$_!-组成', 
        validators:[regex(/^[\da-zA-Z@$_!-]{6,32}$/)]
    },
    password1:{
        hint:'请填写6到32位密码, 只能由数字, 英文字母或半角符号@$_!-组成', 
        validators:[required, regex(/^[\da-zA-Z@$_!-]{6,32}$/)]
    },
    password2:{
        hint:'重复密码', 
        validators:[required, match_password1, regex(/^[\da-zA-Z@$_!-]{6,32}$/)]
    },
    bscj:{
        validators:[not_required, min_val(0),max_val(100), blur_post],
        label:'笔试成绩'
    }, 
    mscj:{
        validators:[not_required, min_val(0),max_val(100), blur_post],
        label:'面试成绩'
    }, 
    check_status:{
        validators:[blur_post_choices],
    }, 
    message:{
        validators:[not_required, min_len(3),max_len(100), blur_post],
        label:'消息'
    }, 
    jtzycyqk:{
        hint:'按"姓名, 称谓, 工作单位, 职务"格式填写,逗号分隔,\n'+
        '多个成员换行,没有的项目填\'无\',例如:\n\n'+
        '父亲,李四,乙企业,总经理\n'+
        '母亲,张三,甲公司,办公室主任\n'+'弟弟,李五,无,无',
    }, 
    lxdh:{
        hint:'7到11位纯数字',
        validators:[required, regex(/^\d{7,11}$/)]
    }
}
function match_password1(value, name){
    var password1 = $('input[name="password1"]').val();
    if (value!==password1){
        return '两次输入的密码不一致';
    }
}
function required(value, name){
    if (value===''){
        return '您还没填写{name}'.replace('{name}',name);
    }
}
function not_required(value, name){
    if (value===''){
        return PASS_THIS;
    }
}
function regex(limit, message){
    return function(value, name){
        message = message || '{name}格式不正确';
        if (!value.match(limit)){
            return message.replace('{name}',name);
        }
    }
}
function min_len(limit, message){
    return function(value, name){
        message = message || '至少{limit}个字, 您输入了{value}个';
        value = value.length;
        if (value < limit){
            return message.replace('{limit}',limit).replace('{value}',value).replace('{name}',name);
        }
    }
}
function max_len(limit, message){
    return function(value, name){
        message = message || '最多{limit}个字, 您输入了{value}个';
        value = value.length;
        if (value > limit){
            return message.replace('{limit}',limit).replace('{value}',value).replace('{name}',name);
        }
    }
}
function min_val(limit, message){
    return function(value, name){
        message = message || '太小, 至少{limit}';
        if (value < limit){
            return message.replace('{limit}',limit).replace('{value}',value).replace('{name}',name);
        }
    }
}
function max_val(limit, message){
    return function(value, name){
        message = message || '太大, 最多{limit}';
        if (value > limit){
            return message.replace('{limit}',limit).replace('{value}',value).replace('{name}',name);
        }
    }
}
function blur_post(value, name){
    var self = $(this);
    return _blur_post(self, {pk:self.attr('pk'), name:self.attr('name'), value:value})
}
function blur_post_choices(value, name){
    var self = $(this);
    var arr = self.attr('name').split('-');
    return _blur_post(self, {name:arr[0], pk:arr[1], value:value})
}
function _blur_post(self, data){
    $.ajax({
        type: "POST",
        dataType: "json",
        url: window.location.href,
        data: data,
        success: function(res) {
            if (res.valid === true) {
                self.parents('td').css({"background-color":SUCCESS_COLOR}); 
            } else { 
                self.parents('td').css({"background-color":'transparent'}); 
                $.each(res.errors, function(field, value) {
                    make_tip(self, make_tips_ul(value));
                });
            }               
        },
        error: function(xhr, textStatus, errorThrown) {
            alert(textStatus);
        },
    });
}
function clear_hint(){
    $('.'+FORM_HINT_CLASS).remove();
}
function make_tips_ul(messages, class_name) {
    class_name = class_name || FORM_ERROR_CLASS
    var estr = '';
    $.each(messages, function(i, message) {
        estr += '<li><pre>' + message + '</pre></li>'
    });
    return $('<ul class="'+class_name+'">' + estr + '</ul>');
}
function make_tip(widget, tip){
    tip.insertAfter(widget);
    tip.css({
        top :widget.offset().top,
        left:widget.offset().left + widget.outerWidth() + TIP_OFFSET_LEFT, 
        position:'absolute', 
        display:'block', 
        'min-height': widget.outerHeight()+'px'
    });    
}

function add_validators(validators, show_name){
    return function(){
        var self = $(this);
        var messages = [];
        for (var i = 0; i < validators.length; i++){
            var error_message = validators[i].call(this, self.val(), show_name);
            if (error_message===undefined){
                continue;
            }else if ($.type(error_message)==='string'){
                messages.push(error_message);
                break;
            }else if (error_message===PASS_THIS){
                break;
            }
        }
        self.nextAll('.'+FORM_ERROR_CLASS).remove(); 
        if (messages.length !== 0){
            make_tip(self, make_tips_ul(messages));
        }
    }
}
function add_hint(message){
    return function(){
        var self  = $(this);
        if (self.nextAll().length===0){
            make_tip(self, make_tips_ul([message], FORM_HINT_CLASS));
        }
    }
}

$(document).ready(function() {
    
    $('input, textarea').each(function(i, input){
        input = $(input);
        var ok = input.attr('name');
        if (!ok){
            return;
        }
        var name = ok.split('-')[0];
        var field = form_fields[name];
        if (field){
            if (field.validators){
                var show_name = field.label || $('label[for="'+input.attr('id')+'"]').html() || '';
                input.blur(add_validators(field.validators, show_name));
            }
            if (field.hint){
                input.focus(clear_hint);
                input.focus(add_hint(field.hint));
            }
        }
    });

    $("form.simple-form").submit(function(e) {
        var fm = $(this);
        var event = window.event || e;
        if (event.preventDefault){
            event.preventDefault();
            console.log('chrome');
        } else if(FormData===undefined){
            console.log('no FormData');
            return; 
        }else{
            event.returnValue = false;
            console.log('have return value but no preventDefault');
        }
        // if ($('table .'+FORM_ERROR_CLASS).length>0){
        //     var button=$('input[type="submit"]');
        //     make_tip(button, make_tips_ul(["还有错误没有处理,无法提交"]));
        //     $('.'+FORM_ERROR_CLASS).first().prev().focus(); 
        //     return;
        // }
        var button=$('input[type="submit"]');
        button.attr({"disabled":"disabled","value":"已提交,请稍等..."}).css({'background-color':'#ccc'});
        $.ajax({
            type: "POST",
            dataType: "json",
            url: window.location.href,
            data: new FormData(fm[0]),
            cache: false,
            contentType: false,
            processData: false,
            success: function(res) {
                if (res.valid == true) {
                    window.location.replace(res.url);
                } else {
                    $('.'+FORM_HINT_CLASS).remove(); 
                    $('.'+FORM_ERROR_CLASS).remove(); 
                    var errors = res.errors;
                    if (errors.__all__){
                        $(make_tips_ul(errors.__all__)).insertBefore($('table'));
                    }else{
                        $.each(errors, function(field, value) {
                            make_tip($('#id_'+field), make_tips_ul(value));
                        });
                        $('.'+FORM_ERROR_CLASS).first().prev().focus(); 
                    }
                    button.removeAttr("disabled").attr({"value":"提交"}).css({'background-color':'#0C7B33'});
                }
            },
            error: function(xhr, textStatus, errorThrown) {
                alert(textStatus)
            },
        })
    });

    $(".popup").on('click', function() {
        var self=$(this);
        var ms = $('#nav .visible');
        if (ms.length != 0){
            ms.removeClass('visible');           
        } else {
            $.ajax({
                type: "get",
                dataType: "json",
                url: "/accounts/is_login/",
                success: function(res) {
                    var pos = self.offset();
                    var top = pos.top + self.outerHeight();
                    $('#nav .'+res.status).addClass('visible').css({'top':top}) ;           
                },
                error: function(xhr, textStatus, errorThrown) {
                    alert(textStatus)
                },
            });
        }
    });

})

function rgb2hex(rgbs){
    if (!rgbs){
        return '#FFFFFF';
    }
    rgb = rgbs.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
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