function printDiv(divName) {
     var printContents = document.getElementById(divName).innerHTML;
     var originalContents = document.body.innerHTML;

     document.body.innerHTML = printContents;

     window.print();

     document.body.innerHTML = originalContents;
}

$(document).ready(function() {
    var tds = $('.detail-table').find('td[colspan]');
    $.each(tds, function(){
            var td = $(this);
            var num = td.attr('colspan');
            td.find('div,pre').css('width',num*5+'em');
        }
    )
    var zkz_rules_height = $('.zkz-rules').height();
    var zkz_flag_height  = $('.zkz-flag').height();
    var diff  =  Math.floor((zkz_rules_height-zkz_flag_height)/2);
    if (diff>0){
        $('.single').css({'margin-top':diff, 'margin-bottom':diff});
    }
})