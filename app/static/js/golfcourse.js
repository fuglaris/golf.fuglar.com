$(document).ready(function() {

    moment.locale('is');


    function refresh_success(title, message) {
      $("#calendar").fullCalendar("destroy");
      init();
      $.notify({
        	// options
        	title: title,
        	message: message
        },{
          placement: {
        		from: "top",
        		align: "center"
        	},
        	z_index: 1031,
        	delay: 5000,
        	timer: 1000,
          type: 'success'
        });
    }

    function refresh_danger(title, message) {
      $("#calendar").fullCalendar("destroy");
      init();
      $.notify({
        	// options
        	title: title,
        	message: message
        },{
          placement: {
        		from: "top",
        		align: "center"
        	},
        	z_index: 1031,
        	delay: 5000,
        	timer: 1000,
          type: 'danger'
        });
    }

    function process_success(data) {
      if (data.error == 1) {
          refresh_danger(data.title, data.message)
      }
      else {
          refresh_success(data.title, data.message)
      }
    };

    Date.prototype.yyyymmdd = function () {
        var yyyy = this.getFullYear().toString();
        var mm = (this.getMonth() + 1).toString(); // getMonth() is zero-based
        var dd = this.getDate().toString();
        return yyyy + (mm[1] ? "-" + mm : "-0" + mm[0]) + (dd[1] ? "-" + dd : "-0" + dd[0]); // padding
    };

    init();

    function init(){
        $.ajax({
            url: "golfcourse/usedcards",
            type: "GET",
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                  var allData = data;
                  var jsonArray = [];
                  for (i = 0; i < allData.length; i++) {
                      var StartDate = new Date(allData[i]["date"]);
                      var FinishDate = new Date(allData[i]["date"]);
                      FinishDate.setDate(FinishDate.getDate() + 1);
                      jsonArray.push({
                          title: allData[i]["displayname"] + " - " + allData[i]["shortname"] + ", " + "Kort: " + allData[i]["number"],
                          start: StartDate.yyyymmdd().toString(),
                          end: FinishDate.yyyymmdd().toString(),
                          color: allData[i]["color"],
                          id: allData[i]["id"]
                      });

                  }
                  var item = sessionStorage['userId'];
                  initCalendarGolf(jsonArray);
              },
              error: function (xhr, status, err) {
                  console.error("error", status, err.toString());
              }
        });
    }


    $('#cards-availible').on('click','li', function(){
        if ($(this).hasClass('active')) {
          $(this).removeClass('active');
        }
        else {
          $(this).addClass('active');
        }
    });

    $('#send-availible').on('click',function() {
        var ids = $("#cards-availible").find("li.active");

        var data = "";
        for (var i = 0; i < ids.length; i++) {
            if (i > 0) {
              data += "&";
            };
            data += "id=" + ids[i].id;
        }

        var date = $("#cardsleft-date").val();

        if (data) {
          data += "&dateid=" + date;
        }

        SendGolfCards(data);
        $('#cardsleft').modal('toggle');
    });

    function SendGolfCards(query) {
        $.ajax({
            url: '/api/usecards?'+query,
            type: 'GET',
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                process_success(data);
            },
            error: function (xhr, status, err) {
                console.error("error", status, err.toString());
            }
        });
      };

    function GetAvailableGolfCards(date) {
        $.ajax({
            url: '/api/availiblecards?dateid='+moment(date.format()).format("YYYYMMDD"),
            type: 'GET',
            contentType: "application/json; charset=utf-8",
            success: function (data) {
                $("#cards-availible").html('');
                allData = data;
                for (var i = 0; i < allData.length; i++) {
                    $("#cards-availible").append('<li id="' + allData[i]['id'] + '"' + '>' + allData[i]['shortname'] + ", kort nr. " + allData[i]['number'] + '</li>');
                }

                document.getElementById("cardsleft-date-h4").textContent = moment(date.format()).format("Do MMM YYYY");
                $("#cardsleft-date").val(moment(date.format()).format("YYYYMMDD"));
                $('#cardsleft').modal('toggle');

            },
            error: function (xhr, status, err) {
                console.error("error", status, err.toString());
            }
        });
      };

      $('#delete-golfcard').on('click',function() {
          var id = $("#cardinfo-id").val();

          $.ajax({
              url: '/api/deletecard?id='+id,
              type: 'GET',
              contentType: "application/json; charset=utf-8",
              success: function (data) {
                  $('#cardinfo').modal('toggle');
                  process_success(data);
              },
              error: function (xhr, status, err) {
                  $('#cardinfo').modal('toggle');
                  console.error("error", status, err.toString());
              }
          });


      });

      function GetGolfCardInfo(id) {
          $.ajax({
              url: '/api/cardinfo?id='+id,
              type: 'GET',
              contentType: "application/json; charset=utf-8",
              success: function(data) {
                  var allData = data;
                  var date = new Date(allData[0]["date"]);
                  $("#cardinfo-id").val(allData[0]["id"]);
                  $("#cardinfo-coursename").text("Völlur: " + allData[0]["coursename"]);
                  $("#cardinfo-number").text("Númer korts: " + allData[0]["number"]);
                  $("#cardinfo-username").text("Notandi: " + allData[0]["username"]);
                  $("#cardinfo-date").text("Dagsetning: " + moment(date).format("Do MMM YYYY"));
                  $('#cardinfo').modal('toggle');
              },
              error: function(xhr, status, err) {
                  console.error("error", status, err.toString());
              }
          });
      }


    function initCalendarGolf(data) {
      $("#calendar").fullCalendar({
          header: {
              left: "prev,next",
              center: "title",
              right: 'month,basicWeek,basicDay'
          },
          defaultView: "basicWeek",
          eventLimit: 20, // allow "more" link when too many events
          events: data,
          lang: "is",
          eventClick: function (calEvent, jsEvent, view) {
              $("#delete-error-message").text('');
              GetGolfCardInfo(calEvent.id)
              $(".infoDelete").on("click", function () {
                deleteGolfCard(EventID);
              });
          },
          dayClick: function (date, jsEvent, view) {
              if (date.diff(moment(),'days')>=0) {
                  GetAvailableGolfCards(date);
              } else {
                  console.log('Dagurinn er þegar liðinn');
                  window.alert('Dagurinn er þegar liðinn')
              }


          },
          handleWindowResize: true
      });
    };

});
