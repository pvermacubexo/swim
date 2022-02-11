
jQuery.fn.autoHeight1 = function (options) {
  var defaults = {
    textColor: "#000"
  };
  var opt = $.extend({}, defaults, options);
  return this.each(function () {
    var ele = $(this);

    function setHeight() {
      var windowHeight1 = $(window).height();
      ele.css({"height": windowHeight1});
    }

    setHeight();
    $(window).resize(function () {
      setHeight();
    });
  });
};

$(function () {
  $(".autoHeight").autoHeight1();
});

jQuery.fn.autoHeight2 = function (options) {
  var defaults = {
    textColor: "#000"
  };
  var opt = $.extend({}, defaults, options);
  return this.each(function () {
    var ele = $(this);

    function setHeight() {
      var windowHeight2 = $(window).height();
      ele.css({"height": windowHeight2 - 270});
    }

    setHeight();
    $(window).resize(function () {
      setHeight();
    });
  });
};

$(function () {
  $(".autoHeight-appo").autoHeight2();
});

jQuery.fn.autoHeight = function (options) {
  var defaults = {
    textColor: "#000"
  };
  var opt = $.extend({}, defaults, options);
  return this.each(function () {
    var ele = $(this);

    function setHeight() {
      var windowHeight = $(window).height();
      ele.css({"max-height": windowHeight - 220});
    }

    setHeight();
    $(window).resize(function () {
      setHeight();
    });
  });
};
let indDate = [];
let newarr = [];
$(function () {
  $(".autoHeight-ins").autoHeight();
});

function DeleteDTW(){
  indDate = []
}

var myDates = [];
for (var j = 0; j <= 11; j++) {
  myDates[j] = [];
}

$(function () {
  $('#calendar').datepicker({
    // beforeShowDay: $.datepicker.noWeekends,
    // minDate: 0,
  });
  initCalendar();
});

var individualDate = [];

function initCalendar() {
  $('div.ui-widget-header').append('\
        <a class="ui-datepicker-clear-month" id="clear_date" title="Clear Date" >\X\ </a>\
    ');

  var thisMonth = $($($('#calendar tbody tr')[2]).find('td')[0]).attr('data-month');
  var dateDragStart = undefined; // We'll use this variable to identify if the user is mouse button is pressed (if the user is dragging over the calendar)
  individualDate = [];
  var calendarTds = $('.ui-datepicker-calendar td:not(.ui-datepicker-unselectable)');
  $('#calendar td').attr('data-event', '');
  $('#calendar td').attr('data-handler', '');
  $('#calendar td a').removeClass('ui-state-active');
  $('#calendar td a.ui-state-highlight').removeClass('ui-state-active').removeClass('ui-state-highlight').removeClass('ui-state-hover');
  $('#calendar td').off();
  for (var i = 0; i < myDates[thisMonth].length; i++) { // Repaint
    var a = calendarTds.find('a').filter('a:textEquals(' + myDates[thisMonth][i].getDate() + ')').addClass('ui-state-active');
    individualDate.push(new Date(a.parent().attr('data-year'), thisMonth, a.html()));
  }


function removeFirstZero(dd){
  var date = String(dd);
  // if ((date.slice(0,1)) === "0" ){
  //   dd = date.slice(1);
  // }
  console.log(date)
  return dd;
}


  // $('#calendar > div > table > tbody > tr > td').click( function ()
   $('#calendar td a').click( function ()
      {
        var today =new Date($(this).parent().attr('data-year'), $(this).parent().attr('data-month'), $(this).html());
        var dd = String(today.getDate()).padStart(2, '0');
        var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
        var yyyy = today.getFullYear();
        today = yyyy + '-' + mm + '-' + dd;
        //console.log(today)

console.log("First")
        if(indDate.length ===0){
          $(this).addClass('ui-state-active');
            //  console.log("0")
              indDate.push(today)
              localStorage.setItem('individual_Date', JSON.stringify(indDate))
          console.log(indDate)
            }
        else{
            if(indDate.find(element => element === today)){
              indDate = indDate.filter(e => e !== today);
              // dd=removeFirstZero(dd)
             // console.log(dd);
              console.log('#calendar > div > table > tbody > tr > td > a:contains('+ dd +')');
              $(this).removeClass('ui-state-active');
              localStorage.setItem('individual_Date', JSON.stringify(indDate))
              console.log("else if", indDate)
            }
            else{
              $(this).addClass('ui-state-active');
              indDate.push(today)
              localStorage.setItem('individual_Date', JSON.stringify(indDate))
              console.log("else else", indDate)

            }

             }
      console.log(today)

  })

  //   $('#calendar td').click(function () { // Click or start of dragging
  //   dateDragStart = new Date($(this).attr('data-year'), $(this).attr('data-month'), $(this).find('a').html());
  //   $(this).find('a').addClass('ui-state-active');
  //   console.log("Second")
  //   return false;
  // });

  //           if(indDate.length ===0){
  //           //  console.log("0")
  //             indDate.push(today)
  //         //    console.log('PUSH', indDate)
  //             localStorage.setItem('individual_Date', JSON.stringify(indDate))
  //           }
  //           else{
  //
  //               for(var i = 0; i<=indDate.length ; i++){
  //                // console.log((indDate[i]),(today))
  //                 if(indDate.includes(today)){
  //                  // console.log('a:contains('+ dd +')');
  //                   var cls = $('a:contains('+ "12" +')').attr("class");
  //                 //  console.log(cls);
  //                   if (cls === "ui-state-default"){
  //                       $('a:contains('+ dd +')').removeClass('ui-state-active');
  //                       console.log(dd)
  //                      // indDate.pop()
  //                   }
  //                  else{
  //
  //                   }
  //                 //  console.log('indDate',indDate)
  //                   indDate.pop(today)
  //               //    console.log('else if', indDate)
  //                   break;
  //                 }
  //                 else{
  //                   console.log("else")
  //                   indDate.push(today)
  //                   console.log('else', indDate)
  //                   localStorage.setItem('individual_Date', JSON.stringify(indDate))
  //                   break;
  //                 }
  //               }
  //            }
  //   });
  //   dateDragStart = undefined;
  //   return false;
  // });
  // $(document).mouseup(function () {
  //   dateDragStart = undefined;
  // });

  // $('#calendar td').mouseenter(function () { // Drag over day on calendar
  //   var thisDate = new Date($(this).attr('data-year'), $(this).attr('data-month'), $(this).find('a').html());
  //   if (dateDragStart !== undefined && thisDate > dateDragStart) { // We are dragging forwards
  //     for (var d = new Date(dateDragStart); d <= thisDate; d.setDate(d.getDate() + 1)) {
  //       calendarTds.find('a').filter('a:textEquals(' + d.getDate() + ')').addClass('ui-state-active');
  //     }
  //     $(this).find('a').addClass('ui-state-active');
  //   } else if (dateDragStart !== undefined && thisDate < dateDragStart) { // We are dragging backwards
  //     for (var d = new Date(dateDragStart); d >= thisDate; d.setDate(d.getDate() - 1)) {
  //       calendarTds.find('a').filter('a:textEquals(' + d.getDate() + ')').addClass('ui-state-active');
  //     }
  //     $(this).find('a').addClass('ui-state-active');
  //   }
  // });
  //
  // $('#calendar td').mouseleave(function () {
  //   var thisDate = new Date($(this).attr('data-year'), $(this).attr('data-month'), $(this).find('a').html());
  //   if (dateDragStart !== undefined && thisDate > dateDragStart) {
  //     for (var d = new Date(dateDragStart); d <= thisDate; d.setDate(d.getDate() + 1)) {
  //       if (individualDate.find(item => item.getTime() === d.getTime()) === undefined) {
  //         calendarTds.find('a').filter('a:textEquals(' + d.getDate() + ')').removeClass('ui-state-active');
  //       }
  //     }
  //   } else if (dateDragStart !== undefined && thisDate < dateDragStart) {
  //     for (var d = new Date(dateDragStart); d >= thisDate; d.setDate(d.getDate() - 1)) {
  //       if (individualDate.find(item => item.getTime() === d.getTime()) === undefined) {
  //         calendarTds.find('a').filter('a:textEquals(' + d.getDate() + ')').removeClass('ui-state-active');
  //       }
  //     }
  //   }
  // });

  // $('.ui-datepicker-clear-month').click(function () {
  //   individualDate = [];
  //   calendarTds.find('a').removeClass('ui-state-active');
  //   console.log(individualDate);
  // });

  $('a.ui-datepicker-next, a.ui-datepicker-prev').click(function () {
    myDates[thisMonth] = individualDate;
    initCalendar();
  });
}




$.expr[':'].textEquals = function (el, idx, selector) {
  var regExp = new RegExp('^' + selector[3] + '$');
  return regExp.test($(el).text());
};


$(document).ready(function () {
  $('.registration-form fieldset:first-child').fadeIn('slow');

  $('.registration-form input[type="text"]').on('focus', function () {
    $(this).removeClass('input-error');
  });

  // next step
  $('.registration-form .btn-next').on('click', function () {
    console.log('send date and time for confirm booking', individualDate);
    var parent_fieldset = $(this).parents('fieldset');
    var next_step = true;


    if (next_step) {
      parent_fieldset.fadeOut(400, function () {
        $(this).next().fadeIn();
      });
    }

  });

  // previous step
  $('.registration-form .btn-previous').on('click', function () {
    $(this).parents('fieldset').fadeOut(400, function () {
      $(this).prev().fadeIn();
    });
  });


  /**********************add this js also**************************/
  $('.registration-form .btn-first').on('click', function () {
    $(this).parents('fieldset').fadeOut(400, function () {
      $('.first-step').fadeIn();
    });
  });

  // submit


});




$(window).scroll(function() {
  var scroll = $(window).scrollTop();

  //>=, not <=
  if (scroll >=200) {
    //clearHeader, not clearheader - caps H
    $(".main-header").addClass("darkHeader");
  }
  else
  {
    $(".main-header").removeClass("darkHeader");
  }
});

$(document).ready(function(){
  $('.head-menu-tag a[href^="#"]').on('click',function (e) {
    e.preventDefault();
    var target = this.hash;
    var $target = $(target);
    $('html, body').stop().animate({
      'scrollTop': $target.offset().top
    }, 900, 'swing', function () {
      // window.location.hash = target;
    });
  });
});

new WOW().init();

// #####################################################################

var selectedDates = [];
 $(function () {

   $('#calendar').datepicker({
    altField: '#Date3',
    // minDate: 0,
    // beforeShowDay: $.datepicker.noWeekends,
    dateFormat: "yy-mm-dd",
  })
   $('.ui-datepicker-clear-month').click(function(){
     console.log("Hello World")
     $('#calendar').find(".ui-state-default").removeClass("ui-state-active");
     document.querySelector("#accordion").innerHTML = "";
     selectedDates = [];
     indDate = [];
     localStorage.removeItem("individual_Date")
     localStorage.removeItem("Date");
   });


   //  $(".ui-datepicker-next").click(function (){
   //    console.log("rene")
   // });



   setInterval(()=>{
$('.ui-datepicker-clear-month').click(function(){
     console.log("Hello World")
     $('#calendar').find(".ui-state-default").removeClass("ui-state-active");
     document.querySelector("#accordion").innerHTML = "";
     selectedDates = [];
     indDate = [];
     localStorage.removeItem("individual_Date")
     localStorage.removeItem("Date");
   });
},1000);
  // $("#calendar").on("click", function () {
  //   var x = $(this).val();
  //   console.log(x)
  // });
  // $('#calendar table>tbody>tr>td>a').click(function () {
  //   // console.log(individualDate)
  //   var i = $(this).text();
  //   if(selectedDates.find(element => element === i)){
  //     $(this).removeClass('ui-state-active')
  //     selectedDates = selectedDates.filter((x) => x !== i)
  //   }
  //
  // });
});


// ----------------------------Select Complete Course---------------------


var CompleteDate = [];
$(function () {
  $('#calendar2').datepicker({
    altField: '#Date3',
    // minDate: 0,
    // beforeShowDay: $.datepicker.noWeekends,
    dateFormat: "yy-mm-dd",
  })
  $('#calendar2').find(".ui-state-default").removeClass("ui-state-active");
  CompleteDate = [$(this).val()];


  $("#clearDates").click(function(){
    $('#calendar2').find(".ui-state-default").removeClass("ui-state-active");
    CompleteDate = [$(this).val()];
    console.log("clear complete course dates", CompleteDate)
  });

  $("#calendar2").on("change", function () {
    CompleteDate = [$(this).val()];
    localStorage.setItem('Date', JSON.stringify(CompleteDate[0]))
    console.log("Select complete date for complete course", CompleteDate)
    var class_instructor = window.localStorage.getItem('class_instructor_id')
    console.error("class_instructor",class_instructor)
  });

});

//############################################################

function funsd(event){
  console.log()
  className = $(event).attr("class")
  console.log("hiii")
  console.log(className)
  $("."+className).css("background-color","red");
  // document.getElementsByClassName("ttime"+i).style.backgroundColor = "";
}
 function openModalSelectTime () {
   document.getElementById("calendar_popup").style.display = "none";
   document.getElementById("individual_date_time").style.display = "block";
 }

function openModalConfirmBooking () {
  document.getElementById("individual_date_time").style.display = "none";
  document.getElementById("booking_confirm").style.display = "block";
}

function openModalPaymentScreen () {
  document.getElementById("booking_confirm").style.display = "none";
  document.getElementById("payment_screen").style.display = "block";
}


function openModalPaymentConfirmData () {
  document.getElementById("payment_screen").style.display = "none";
  document.getElementById("paymentConfirm_data").style.display = "block";
}



function openCompleteModalConfirmBooking  () {
  document.getElementById("calendar_popup").style.display = "none";
  document.getElementById("booking_confirm").style.display = "block";
}

function openPrevious  () {
  document.getElementById("booking_confirm").style.display = "none";
  document.getElementById("individual_date_time").style.display = "block";
}

function openPreviousCalender  () {
  document.getElementById("booking_confirm").style.display = "none";
  document.getElementById("individual_date_time").style.display = "block";
}

function signupPopup () {
   $("#signup").modal({
     show:true
   })
}
