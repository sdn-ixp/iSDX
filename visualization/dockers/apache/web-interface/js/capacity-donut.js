$(document).ready(
function() {
  var data = [ {name: "Available", value:  943},
               {name: "Used", value: 127.5},
  			       {name: "Unconfigured", value:  4868.5}
        ];

  var total = 5939;

  var xmlhttp = new XMLHttpRequest();
  var url = localStorage.getItem("capacity_url");
  var params = "?serial=APM00143230622"
  xmlhttp.onreadystatechange=function() {
      if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
          capacityProcessor(xmlhttp.responseText);
      }
  }
  xmlhttp.open("POST", url, false);
  xmlhttp.send(params);

  function capacityProcessor(response) {
      var arr = JSON.parse(response);
      var i;
      for(i = 0; i < arr.length; i++) {
          unconfigcap = arr[i].unconfigcap;
          freecap = arr[i].freecap;
          usedcap = arr[i].usedcap;

          data = [ {name: "Available", value:  freecap},
                   {name: "Used", value: usedcap},
      			       {name: "Unconfigured", value: unconfigcap}
                ];
          total = arr[i].syscap;
      }
  }

  var socket = io.connect(localStorage.getItem("nodejs"));

  socket.on('connect', function() {
  	console.log("Node.js - Connected to Server");
  });

  socket.on('channel', function() {
  	console.log("Node.js - Connected to Server");
  });

  socket.on('message', function(message){
  		//console.log("Node.js - " + JSON.stringify(message));
  		type = message.split("|")[0];

  		if(type == "capacity")
  		{
  			ts = message.split("|")[1];
  			syscap = message.split("|")[2];
  			usedcap = message.split("|")[3];
  			freecap = message.split("|")[4];
  			unconfigcap = message.split("|")[5];

        data = [{ name: "Available", value: freecap },
                { name: "Used", value: usedcap     },
        			  { name: "Unconfigured", value: unconfigcap}];
        change(data);
        total = syscap;
  			console.log("" + syscap + "" + usedcap + "" + freecap + "" + unconfigcap);
  			//fix_liquid_gauge(score);
  		}
  }) ;

  socket.on('disconnect', function() {
  		console.log('disconnected');
  });

  socket.connect();

  change(data);

  function change(data) {

  var margin = {top: 10, right: 80, bottom: 50, left: 80};
  	width = 650 - margin.left - margin.right;
  	height = width - margin.top - margin.bottom;

    document.getElementById("capacity_donut").innerHTML = "";


  var chart = d3.select("#capacity_donut")
  				.append('svg')
  			    .attr("width", width + margin.left + margin.right)
  			    .attr("height", height + margin.top + margin.bottom)
  			   .append("g")
      			.attr("transform", "translate(" + ((width/2)+margin.left) + "," + ((height/2)+margin.top) + ")");



  var radius = Math.min(width, height)/2;


  var color = d3.scale.ordinal()
  	.range(["#76d46e", "#02a792", "#7d8a98"]);

  var arc = d3.svg.arc()
  	.outerRadius(radius * 0.8)
  	.innerRadius(radius * 0.65);

  var outerArc = d3.svg.arc()
  	.innerRadius(radius * 0.9)
  	.outerRadius(radius * 0.9);

  var pie = d3.layout.pie()
  	.sort(null)
  	.value(function(d) {
  		return d.value;
  	});

  var key = function(d){ return d.data.name; };

  chart.append("g")
  	.attr("class", "slices");

  chart.append("g")
  	.attr("class", "labels");

  chart.append("g")
  	.attr("class", "lines");

  function midAngle(d){
  		return d.startAngle + (d.endAngle - d.startAngle)/2;
  	}

      var slice = chart.select(".slices").selectAll("path.slice")
  		.data(pie(data), key);

  	slice.enter()
  		.insert("path")
  		.style("fill", function(d) { return color(d.data.name); })
  		.attr("class", "slice");
  	slice
  		.transition().delay(function(d, i) { return i * 500; }).duration(500)
  		.attrTween("d", function(d) {
  			this._current = this._current || d;
  			var interpolate = d3.interpolate(this._current, d);
  			this._current = interpolate(0);
  			return function(t) {
  				return arc(interpolate(t));
  			};
  		});


  	slice.exit()
  		.remove();

      var slices = d3.select(".slices").selectAll("path.slice")
                  .data(pie(data), key)
                  .on("mouseover", function(d){ ttext.text(''); mtext.text(d.data.value + " GB");})
                  .on("mousemove", function(d){ ttext.text(''); mtext.text(d.data.value + " GB");})
                  .on("mouseout", function()  { ttext.text('Total'); mtext.text(total.toString() + " GB");});

  		/* ------- TEXT LABELS -------*/
  var text = chart.select(".labels").selectAll("text")
  		.data(pie(data), key);

  text.enter()
  	.append("text")
  	.attr("dy", ".35em")
    .attr("font-family","'Times New Roman', Georgia, Serif")
    .attr("fill", "#7b7e7e")
    .attr("font-weight", "bold")
    .attr("font-size", "16px")
  	.text(function(d) {
  	 return d.data.name;
  	});

  	text.transition().duration(1000)
  		.attrTween("transform", function(d) {
  			this._current = this._current || d;
  			var interpolate = d3.interpolate(this._current, d);
  			this._current = interpolate(0);
  			return function(t) {
  				var d2 = interpolate(t);
  				var pos = outerArc.centroid(d2);
  				pos[0] = radius * (midAngle(d2) < Math.PI ? 1 : -1);
  				return "translate("+ pos +")";
  			};
  		})
  		.styleTween("text-anchor", function(d){
  			this._current = this._current || d;
  			var interpolate = d3.interpolate(this._current, d);
  			this._current = interpolate(0);
  			return function(t) {
  				var d2 = interpolate(t);
  				return midAngle(d2) < Math.PI ? "start":"end";
  			};
  		});

  	text.exit()
  		.remove();

  /* ------- SLICE TO TEXT POLYLINES -------*/

  var polyline = chart.select(".lines").selectAll("polyline")
  		.data(pie(data), key);

  	polyline.enter()
  		.append("polyline");

  	polyline.transition().duration(1000)
  		.attrTween("points", function(d){
  			this._current = this._current || d;
  			var interpolate = d3.interpolate(this._current, d);
  			this._current = interpolate(0);
  			return function(t) {
  				var d2 = interpolate(t);
  				var pos = outerArc.centroid(d2);
  				pos[0] = radius * 0.95 * (midAngle(d2) < Math.PI ? 1 : -1);
  				return [arc.centroid(d2), outerArc.centroid(d2), pos];
  			};
  		})
        .style("opacity", ".3")
        .style("stroke", "black")
        .style("stroke-width", "2px")
        .style("fill", "none");

  	polyline.exit()
  		.remove();

  var mtext = chart.append("text")
    .attr("dy", "-0.3em")
    .style("text-anchor", "middle")
    .attr("class", "inner-circle")
    .attr("fill", "#36454f")
    .attr("font-size", "50px")
  //  .attr("font-weight", "bold")
    .text(total.toString() + " GB");

  var ttext = chart.append("text")
    .attr("dy", "1.0em")
    .style("text-anchor", "middle")
    .attr("class", "inner-circle")
    .attr("font-size", "40px")
    .attr("fill", "#3299CC")
    .text(function(d) { return 'Total'; });
  };
});
