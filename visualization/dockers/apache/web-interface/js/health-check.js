 $(document).ready(
function() {
  var config1 = liquidFillGaugeDefaultSettings();
  config1.circleColor = "#659D32";
  config1.textColor = "#586949";
  config1.waveTextColor = "#586949";
  config1.waveColor = "#BCED91";
  config1.circleThickness = 0.1;
  config1.circleFillGap = 0.2;
  config1.textVertPosition = 0.5;
  config1.waveAnimateTime = 3000;
  config1.waveHeight = 0.3;
  config1.waveCount = 1;
  config1.displayPercent = false;

  var config2 = liquidFillGaugeDefaultSettings();
  config2.circleColor = "#D4AB6A";
  config2.textColor = "#553300";
  config2.waveTextColor = "#805615";
  config2.waveColor = "#AA7D39";
  config2.circleThickness = 0.1;
  config2.circleFillGap = 0.2;
  config2.textVertPosition = 0.8;
  config2.waveAnimateTime = 3000;
  config2.waveHeight = 0.3;
  config2.waveCount = 1;
  config2.displayPercent = false;

  var config3 = liquidFillGaugeDefaultSettings();
  config3.circleColor = "#FF7777";
  config3.textColor = "#FF4444";
  config3.waveTextColor = "#FFAAAA";
  config3.waveColor = "#FFDDDD";
  config3.circleThickness = 0.1;
  config3.circleFillGap = 0.2;
  config3.textVertPosition = 0.2;
  config3.waveAnimateTime = 3000;
  config3.waveHeight = 0.3;
  config3.waveCount = 1;
  config3.displayPercent = false;

  var xmlhttp = new XMLHttpRequest();
  var url = localStorage.getItem("healthcheck_url");
  var params = "?serial=APM00143230622"
  xmlhttp.onreadystatechange=function() {
      if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
          healthProcessor(xmlhttp.responseText);
      }
  }
  xmlhttp.open("POST", url, true);
  xmlhttp.send(params);

  function healthProcessor(response) {
      var arr = JSON.parse(response);
      var i;
      for(i = 0; i < arr.length; i++) {
          score = arr[i].score;
          note = arr[i].note;
          if(score == 100)
      		{
      			loadLiquidFillGauge("fillgauge3", 100, config1, note);
      		}
      		else if(score >= 85 && score < 100)
      		{
      			loadLiquidFillGauge("fillgauge3", score, config2, note);
      		}
      		else
      		{
      			loadLiquidFillGauge("fillgauge3", score, config3, note);
      		}
      }
  }
});
