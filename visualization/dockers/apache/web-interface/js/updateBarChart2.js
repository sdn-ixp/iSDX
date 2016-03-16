$(document).ready(
function() {/*Own Rickshaw Series - Start*/
	var barData = [];


var setup = function(targetID){
	//Set size of svg element and chart
	var margin = {top: 10, right: 40, bottom: 10, left: 60},
		width = 700 - margin.left - margin.right,
		height = 350 - margin.top - margin.bottom,
		categoryIndent = -70,
		defaultBarWidth = 2000;

	//Set up scales
	var x = d3.scale.linear()
	  .domain([0,defaultBarWidth])
	  .range([0,width]);
	var y = d3.scale.ordinal()
	  .rangeRoundBands([0, height], 0.1, 0);

	//Create SVG element
	d3.select(targetID).selectAll("svg").remove()
	var svg = d3.select(targetID).append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height + margin.top + margin.bottom)
	  .append("g")
		.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	//Package and export settings
	var settings = {
	  margin:margin, width:width, height:height, categoryIndent:categoryIndent,
	  svg:svg, x:x, y:y
	}
	return settings;
}

var redrawChart = function(targetID, newdata) {

	//Import settings
	var margin=settings.margin, width=settings.width, height=settings.height, categoryIndent=settings.categoryIndent,
	svg=settings.svg, x=settings.x, y=settings.y;

	//Reset domains
  y.domain(newdata
	.map(function(d) { return d.key; }));
	x.domain([0,100]);

	/////////
	//ENTER//
	/////////

	//Bind new data to chart rows

	//Create chart row and move to below the bottom of the chart
	var chartRow = svg.selectAll("g.chartRow")
	  .data(newdata, function(d){ return d.key});
	var newRow = chartRow
	  .enter()
	  .append("g")
	  .attr("class", "chartRow")
	  .attr("transform", "translate(0," + height + margin.top + margin.bottom + ")");

	//Add rectangles
	newRow.insert("rect")
	  .attr("class","bar")
	  .attr("x", 0)
	  .attr("opacity",0)
    .attr("fill",function(d) { return d.color;})
	  .attr("height", y.rangeBand()-20)
	  .attr("width", function(d) { return x(d.value);})

	//Add value labels
	newRow.append("text")
	  .attr("class","label")
	  .attr("y", y.rangeBand()/2)
		.attr("x",function(d) { return x(d.value)+12;})
	  .attr("opacity",0)
	  .attr("dy",".35em")
	  .attr("dx","0.5em")
	  .text(function(d){return d.value;});

	//Add Headlines
	newRow.append("text")
	  .attr("class","category")
	  .attr("text-overflow","ellipsis")
	  .attr("y", y.rangeBand()/2)
	  .attr("x",categoryIndent)
	  .attr("opacity",0)
	  .attr("dy",".35em")
	  .attr("dx","0.5em")
	  .text(function(d){return "LSP-" + d.key});


	//////////
	//UPDATE//
	//////////

	//Update bar widths
	chartRow.select(".bar").transition()
	  .duration(300)
	  .attr("width", function(d) { return x(d.value);})
	  .attr("opacity",1);

	//Update data labels
	chartRow.select(".label").transition()
	  .duration(300)
	  .attr("opacity",1)
		.attr("x",function(d) { return x(d.value) + 12;})
		.text(function(d){return d.value + "\%";});


	//Fade in categories
	chartRow.select(".category").transition()
	  .duration(300)
	  .attr("opacity",1);


	////////
	//EXIT//
	////////

	//Fade out and remove exit elements
	chartRow.exit().transition()
	  .style("opacity","0")
	  .attr("transform", "translate(0," + (height + margin.top + margin.bottom) + ")")
	  .remove();


	////////////////
	//REORDER ROWS//
	////////////////

	var delay = function(d, i) { return 200 + i * 30; };

	chartRow.transition()
		.delay(delay)
		.duration(300)
		.attr("transform", function(d){ return "translate(0," + y(d.key) + ")"; });
};


//Pulls data
//Since our data is fake, adds some random changes to simulate a data stream.
//Uses a callback because d3.json loading is asynchronous
var pullData = function(settings,callback){
	d3.json("fakeData.json", function (err, data){
		if (err) return console.warn(err);

		barData = data;
		barData.forEach(function(d,i){
      barData[i].value =  d.value;
			barData[i].color = d.color;
  		})

		//barData = formatData(barData);

		callback(settings,barData);
	})
}

//Sort data in descending order and take the top 10 values
var formatData = function(data){
    return data.sort(function (a, b) {
        return b.value - a.value;
      })
	  .slice(0, 10);
}

//I like to call it what it does
var redraw = function(settings){
	pullData(settings,redrawChart)
}

//setup (includes first draw)
var settings = setup('#barchart2');
redraw(settings);


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
		console.log(message);

		if(type == "barb")
		{
			key = message.split("|")[1];
			val = message.split("|")[2];
			barData.forEach(function(d,i){
				if(barData[i].key === key)
				{
					barData[i].value =  val;
				}
			})
			//barData = formatData(barData);
			redrawChart(settings,barData);
		}
}) ;

socket.on('disconnect', function() {
		console.log('disconnected');
});

socket.connect();
});
