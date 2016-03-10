<?php
error_reporting(E_ALL);

function doSomething() {
    echo 'Guess this is working';
}
function doSomething2() {
    echo 'Guess this is working2';
}
if(count($_POST) > 0 && isset($_POST['execfunction'])) {
    doSomething();
}
if(count($_POST) > 0 && isset($_POST['execfunction2'])) {
    doSomething2();
}
?>
<!DOCTYPE html>
<html lang="en" class="no-js">
<style>
text.mono {
	font-size: 9pt;
	font-family: Consolas, courier;
	fill: #aaa;
}
.node {
    stroke: #fff;
    stroke-width: 2px;
}
.textClass {
    stroke: #fff;
		fill: #fff;
    font-family: "Lucida Grande", "Droid Sans", Arial, Helvetica, sans-serif;
    font-weight: normal;
    stroke-width: .5;
    font-size: 16px;
}
#everything{
	width:600px;
	margin:20px;
}
#barchart{
	width:600px;
	height:350px;
}
text.label{
	fill: #ffa500;
	color: #ffa500;
	font-size: 22px;
}

text.pathLabel{
	fill: #ffa500;
	color: #ffa500;
	font-size: 22px;
}

text.category{
	fill: #ffa500;
	font-size: 19px;
}
#axis0 {
   position: absolute;
   height: 700px;
   width: 40px;
 }
 #chart {
  left: 50px;
  width: 650px;
  right: 50px;
  position: relative;
  display: inline-block;
	border: 1px solid #f0f0f0;
}
#axis1 {
   position: absolute;
   height: 700px;
   width: 40px;
 }
 #chart1 {
  left: 50px;
  width: 650px;
  right: 50px;
  position: relative;
  display: inline-block;
	border: 1px solid #f0f0f0;
}
#axis2 {
   position: absolute;
   height: 700px;
   width: 40px;
 }
 #chart2 {
  left: 50px;
  width: 650px;
  right: 50px;
  position: relative;
  display: inline-block;
	border: 1px solid #f0f0f0;
}
div, span, p, td {
	font-family: Arial, sans-serif;
}
#preview {
  left: 50px;
  width: 750px;
  position: relative;
}
#preview1 {
  left: 50px;
  width: 750px;
  position: relative;
}
#preview2 {
  left: 50px;
  width: 750px;
  position: relative;
}
#legend {
	background-color: white;
	padding: 0;
	display: inline-block;
	position: relative;
	left: 8px;
}
#legend .label {
	color: #404040;
}
#legend1 {
	background-color: white;
	padding: 0;
	display: inline-block;
	position: relative;
	left: 8px;
}
#legend1 .label {
	color: #404040;
}
#legend2 {
	background-color: white;
	padding: 0;
	display: inline-block;
	position: relative;
	left: 8px;
}
#legend2 .label {
	color: #404040;
}
#legend_container {
	position: absolute;
	right: 0;
	bottom: 26px;
	width: 0;
}
#chart_container {
	float: left;
	position: relative;
}

#axis0-util{
   position: absolute;
   height: 700px;
   width: 40px;
 }
 #util{
  left: 50px;
  width: 800px;
  position: relative;
  display: inline-block;
}

#preview-util{
  left: 50px;
  width: 800px;
  position: relative;
}
#legend-util{
	display: inline-block;
	position: relative;
	left: 8px;
}

.chart-gauge {
  width: 400px;
  margin: 100px auto;
}

.chart-color1 {
  fill: #e92213;
}

.chart-color2 {
  fill: #ffff00;
}

.chart-color3 {
  fill: #78AB46;
}

.needle,
.needle-center {
  fill: #464A4F;
}
#main {
    width: 800px;
    margin: 0 auto;
}
#sidebar    {
    width: 150px;
    height: 400px;
    float: left;
}

#page-wrap  {
    width: 450px;
    height: 400px;
    margin-left: 200px;
}
#capacity_donut {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  width: 1000px;
  height: 500px;
  position: relative;
}
.liquidFillGaugeText { font-family: Helvetica; font-weight: bold; }


.chart {
  min-height: 400px;
  border-bottom: 1px solid #eee;
  padding: 1em;
}

.chart--headline, .chart--subHeadline {
  text-align: center;
}

.chart--headline {
  position: relative;
  font-weight: 100;
  font-size: 28px;
}
.chart--headline:before {
  position: absolute;
  content: '';
  bottom: 133%;
  left: 50%;
  width: 25%;
  margin: 0 0 0 -12.5%;
  border-top: 1px dashed #999999;
}

.chart--subHeadline {
  font-weight: 400;
  font-size: 14px;
  letter-spacing: 1px;
}

.charts--container {
  background-color: #fff;
  width: 100%;
}
@media screen and (min-width: 700px) {
  .charts--container {
    max-width: 800px;
    top: 10%;
    margin: 5em auto;
    box-shadow: 0 2em 2em #333;
  }
}

.charts--headline {
  text-align: center;
  color: #fff;
  background-color: #fff;
  padding: 1em;
}

.lineChart--area {
  fill: url(#lineChart--gradientBackgroundArea);
}

.lineChart--areaLine {
  fill: none;
  stroke: #6bb7c7;
  stroke-width: 3;
}

.lineChart--bubble--label {
  fill: none;
  stroke: #6bb7c7;
  font-size: 16px;
  font-style: italic;
  /*font-weight: 100;*/
}

.lineChart--bubble--value {
  fill: #fff;
  stroke: #fff;
  font-size: 16px;
  /*font-weight: 100;*/
}

.lineChart--circle {
  fill: #6bb7c7;
  stroke: #fff;
  stroke-width: 3;
}

.lineChart--circle__highlighted {
  fill: #fff;
  stroke: #3f94a7;
}

.lineChart--gradientBackgroundArea--top {
  stop-color: #fff;
  stop-opacity: 0.1;
}

.lineChart--gradientBackgroundArea--bottom {
  stop-color: #6bb7c7;
  stop-opacity: 0.6;
}

.lineChart--svg {
  border: 1px solid #eee;
}

.lineChart--xAxisTicks .domain, .lineChart--xAxis .domain, .lineChart--yAxisTicks .domain {
  display: none;
}

.lineChart--xAxis .tick line {
  display: none;
}

.lineChart--xAxisTicks .tick line, .lineChart--yAxisTicks .tick line {
  fill: none;
  stroke: #b3b3b3;
  stroke-width: 1;
  stroke-dasharray: 2,2;
}

/**
 * Helper classes
 */
.hidden {
  display: none;
}

.axis path,
.axis line {
  fill: none;
  stroke: #000;
  shape-rendering: crispEdges;
}

.x.axis path {
  display: none;
}
.y.axis path {
  display: none;
}
.line {
  fill: none;
  stroke: steelblue;
  stroke-width: 1.5px;
}

.content-box-gray .content {
  /*  overflow: hidden;
    padding: 10px;
    font-size: 15px;
    border-bottom-left-radius: 5px;
    border-bottom-right-radius: 5px;
    border: 1px solid gray;
    color: #3385FF;*/
}
.content-box-gray .wtitle {
    height:30px;
    line-height:30px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    font-size:28px;
    /*font-weight:bold;*/
    font-family:"Trebuchet MS", Helvetica, sans-serif;
    display:block;
    color: #cccccc;
    display:block;
    padding:10px;
    border-bottom:none;
}

.tooltip {
    pointer-events:none;
    opacity:0;
    transition: opacity 0.3s;
}
/*.tooltip {
  background: #fff;
  box-shadow: 0 0 5px #999999;
  color: #eee;
  fill: #eee;
  display: none;
  font-size: 12px;
  left: 130px;
  padding: 10px;
  position: absolute;
  text-align: center;
  top: 95px;
  width: 80px;
  z-index: 10;
}*/
g.tooltip:not(.css) {
  fill:currentColor;
}
g.tooltip rect {
    fill: #fff;
    stroke: gray;
}
circle:hover + g.tooltip.css {
  opacity:1;
}
.allows-overflow {
    width:100%;
    max-height:100%;
    overflow:visible;
}
</style>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<meta name="description" content="Simple d3.js proof of concept dashboard.">
	<meta name="viewport" content="width=device-width, initial-scale=1">

	<link rel="stylesheet" href="css/normalize.css">
	<link rel="stylesheet" href="css/main.css">
	<link rel="shortcut icon" href="favicon.ico">
	<link type="text/css" rel="stylesheet" href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8/themes/base/jquery-ui.css">
	<link type="text/css" rel="stylesheet" href="css/graph.css">
	<link type="text/css" rel="stylesheet" href="css/detail.css">
	<link type="text/css" rel="stylesheet" href="css/line.css">
	<link type="text/css" rel="stylesheet" href="css/extension.css">
  <link type="text/css" rel="stylesheet" href="css/font-awesome.css">
	<link type="text/css" rel="stylesheet" href="css/legend.css">
  <link type="text/css" rel="stylesheet" href="css/jquery-ui.css">
    <head>
      <meta charset="UTF-8" />
      <title>SDX</title>
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta name="description" content="Login and Registration Form with HTML5 and CSS3" />
      <meta name="keywords" content="html5, css3, form, switch, animation, :target, pseudo-class" />
      <meta name="author" content="Codrops" />
      <link rel="shortcut icon" href="../favicon.ico">
      <link rel="stylesheet" type="text/css" href="css/demo.css" />
      <link rel="stylesheet" type="text/css" href="css/style.css" />
  		<link rel="stylesheet" type="text/css" href="css/animate-custom.css" />
      <link href="css/bootstrap.css" rel="stylesheet">
      <link href="css/agency.css" rel="stylesheet">
      <script type="text/javascript" src="//ajax.cloudflare.com/cdn-cgi/nexp/dok3v=7e13c32551/cloudflare.min.js"></script>
      <script type="text/rocketscript" data-rocketsrc="https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js" data-rocketoptimized="true"></script>
      <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
      <script type="text/rocketscript" data-rocketsrc="https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js" data-rocketoptimized="true"></script>
      <script src="js/globals.js"></script>
      <script src="js/gauge.js"></script>
      <script src="js/updateBarChart.js"></script>
			<script src="js/updateBarChart2.js"></script>
			<script src="js/dynamicTable.js"></script>
			<script src="js/animatedGraph.js"></script>
			<script src="js/time-series1.js"></script>
			<script src="js/time-series2.js"></script>
			<script type="text/javascript" src="http://mbostock.github.com/d3/d3.js?2.6.0"></script>
			<script type="text/javascript" src="http://mbostock.github.com/d3/d3.layout.js?2.6.0"></script>
			<script type="text/javascript" src="http://mbostock.github.com/d3/d3.geom.js?2.6.0"></script>
      <script src="http://d3js.org/d3.v3.min.js"></script>
      <script src="http://labratrevenge.com/d3-tip/javascripts/d3.tip.v0.6.3.js"></script>
      <script type="text/javascript" src="js/gauge-render.js"></script>
      <script type="text/javascript">
            window.onload=onLoadPage;
      </script>
      <script type="text/javascript" src="js/fixedduration-movable.js"></script>
      <script src="js/liquidFillGauge.js"></script>
      <style>
          .liquidFillGaugeText { font-family: Helvetica; font-weight: bold; }
      </style>
      <script src="js/health-check.js"></script>
      <script>
            function autoRefresh()
            {
            // reload_request_list();
            }
              $(document).ready(
                      function() {
                          setInterval('autoRefresh()', 3000);
                      });
    function ExposeList() {
                  var status = document.getElementById('cbChoices').checked;
                  if (status == true) { document.getElementById('ScrollCB').style.display = "block"; }
                  else { document.getElementById('ScrollCB').style.display = 'none'; }
              };

              function doSomething() {
                  console.log("something1");
                  var xmlhttp = new XMLHttpRequest();
                  var url = localStorage.getItem("execute_url");
                  var params = "?cmd1=iperf1"
                  xmlhttp.onreadystatechange=function() {
                      if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
                          console.log(xmlhttp.responseText);
                      }
                  }
                  xmlhttp.open("POST", url, true);
                  xmlhttp.send(params);
              }
              function doSomething2() {
                console.log("something2");
                var xmlhttp = new XMLHttpRequest();
                var url = localStorage.getItem("execute_url");
                var params = "?cmd2=iperf2"
                xmlhttp.onreadystatechange=function() {
                    if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
                        console.log(xmlhttp.responseText);
                    }
                }
                xmlhttp.open("POST", url, true);
                xmlhttp.send(params);
              }
      </script>

      <meta name="viewport" content="initial-scale=1.0, maximum-scale=1.0, user-scalable=0" />
        <link rel="stylesheet" type="text/css" media="all" href="css/app.css" />
        <link href='http://fonts.googleapis.com/css?family=Josefin+Slab:100,400' rel='stylesheet' type='text/css'>
        <link href='http://fonts.googleapis.com/css?family=Lato' rel='stylesheet' type='text/css'>


      </head>
      <body style="overflow-x:hidden;">

    <div>
            <div class="container" >
                <div id="header" style="background: rgb(78, 80, 82);">
                  <header class="">
                   <img alt="" src="Princeton_shield.png" height="80" width="80" align="left" style="padding-left: 20px;margin-top:-15px;  position:relative;" />
                      <h1 style="margin-top:10px;font-family:ArchitectsDaughter;font-weight:normal;">iSDX</h1>

                  </header>
                </div>
            </div>
    </div>
  <table>
    <tr>
      <td>
				<table>
					<tr>
					<td>
				<div id="Div1">
              <div class="widget3 content-box-gray">
                    <div class="wtitle"> </div>
                    <div class="content">
      									    <div id="graphLink"></div>
                    </div>
              </div>
          </div>
				</td>
						</tr>
						<tr>
				<td>
					<div class="widgetc content-box-gray">
								<div class="wtitle"> Paths</div>

								<div class="content">
                  <form method="post" action="<?php echo $_SERVER['PHP_SELF']; ?>">
                      <button type="button" onclick="doSomething()">Execute</button>
                      <button type="button" onclick="doSomething2()">Execute2</button>
                  </form>
				</div>
			</div>
				</td>
				</tr>
			</table>
				</td>
					<td>
						<table>
							<tr>
							<td>
								<div class="widget2 content-box-gray">
											<div class="content">
												<section><div id="legend"></div></section>
														<div id="axis0"></div>
														<div id="chart"></div>
														<div id="timeline"></div>
														<div id="preview"></div>
							</div>
					</div>
	</td>
	</tr>
	<tr>
	<td>
<div class="widget2 content-box-gray">
	<div class="content">
		<section><div id="legend1"></div></section>
				<div id="axis1"></div>
				<div id="chart1"></div>
				<div id="timeline1"></div>
				<div id="preview1"></div>
</div>
</div>
</td>
</tr>
<tr>
<td>
<div class="widget2 content-box-gray">
<div class="content">
	<section><div id="legend2"></div></section>
			<div id="axis2"></div>
			<div id="chart2"></div>
			<div id="timeline2"></div>
			<div id="preview2"></div>
</div>
</div>
</td>
</tr>
</table>
			</td>

    </tr>
  </table>
	<table>
		<tr>

	</td>
		</tr>
		</table>
    </div>
        </body>
    <footer>
      <script type="text/rocketscript" data-rocketsrc="https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js" data-rocketoptimized="true"></script>
      <script type="text/rocketscript" data-rocketsrc="js/tabs.js" data-rocketoptimized="true"></script>
      <script src="js/d3.min.js"></script>
      <script src="js/rickshaw.min.js"></script>
      <script src="js/socket.io.js"></script>
      <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.2/jquery.min.js"></script>
      <script  type="text/javascript" src="js/jquery-1.9.0.js"></script>
      <script  type="text/javascript" src="js/bootstrap.min.js"></script>
      <script src="js/d3/d3.min.js"></script>
      <script src="js/angular/angular.js"></script>
      <script src="js/angular-route/angular-route.js"></script>
      <script src="js/underscore/underscore.js"></script>
      <script src="js/app.js"></script>
      <script src="js/routes.js"></script>
      <script src="js/services.js"></script>
      <script src="js/controllers.js"></script>
      <script src="js/filters.js"></script>
      <script src="js/directives.js"></script>
      <script src="js/directives/breadcrumb.js"></script>
      <script src="js/directives/sunburst-perspective.js"></script>
      <script src="js/directives/sunburst.js"></script>
  </footer>
</html>
