$(document).ready(
function() {/*Own Rickshaw Series - Start*/


Rickshaw.namespace('Rickshaw.SeriesXDateTime.FixedDurationMovable');

Rickshaw.SeriesXDateTime = Rickshaw.Class.create( Rickshaw.Series, {

	initialize: function (data, palette, options) {

		options = options || {};

		this.palette = new Rickshaw.Color.Palette(palette);

		this.timeBase = typeof(options.timeBase) === 'undefined' ?
			Math.floor(new Date().getTime() / 1000) :
			options.timeBase;

		var timeInterval = typeof(options.timeInterval) == 'undefined' ?
			1000 :
			options.timeInterval;

		this.setTimeInterval(timeInterval);

		if (data && (typeof(data) == "object") && Array.isArray(data)) {
			data.forEach( function(item) { this.addItem(item) }, this );
		}
	},

	addItem: function(item) {

		if (typeof(item.name) === 'undefined') {
			throw('addItem() needs a name');
		}

		item.color = (item.color || this.palette.color(item.name));
		item.data = (item.data || []);

		// backfill, if necessary
		if ((item.data.length === 0) && this.length && (this.getIndex() > 0)) {
			this[0].data.forEach( function(plot) {
				item.data.push({ x: plot.x, y: 0 });
			} );
		} else if (item.data.length === 0) {
			item.data.push({ x: this.timeBase - (this.timeInterval || 0), y: 0 });
		}

		this.push(item);

		if (this.legend) {
			this.legend.addLine(this.itemByName(item.name));
		}
	},

	addData: function(data, x) {

		var index = this.getIndex();

		Rickshaw.keys(data).forEach( function(name) {
			if (! this.itemByName(name)) {
				this.addItem({ name: name });
			}
		}, this );

		this.forEach( function(item) {
			item.data.push({
				x: x,
				y: (data[item.name] || 0)
			});
		}, this );
	},

	getIndex: function () {
		return (this[0] && this[0].data && this[0].data.length) ? this[0].data.length : 0;
	},

	itemByName: function(name) {

		for (var i = 0; i < this.length; i++) {
			if (this[i].name == name)
				return this[i];
		}
	},

	setTimeInterval: function(iv) {
		this.timeInterval = iv / 1000;
	},

	setTimeBase: function (t) {
		this.timeBase = t;
	},

	dump: function() {

		var data = {
			timeBase: this.timeBase,
			timeInterval: this.timeInterval,
			items: []
		};

		this.forEach( function(item) {

			var newItem = {
				color: item.color,
				name: item.name,
        ts: item.ts,
				data: []
			};

			item.data.forEach( function(plot) {
				newItem.data.push({ x: plot.x, y: plot.y });
			} );

			data.items.push(newItem);
		} );

		return data;
	},

	load: function(data) {

		if (data.timeInterval) {
			this.timeInterval = data.timeInterval;
		}

		if (data.timeBase) {
			this.timeBase = data.timeBase;
		}

		if (data.items) {
			data.items.forEach( function(item) {
				this.push(item);
				if (this.legend) {
					this.legend.addLine(this.itemByName(item.name));
				}

			}, this );
		}
	}
} );

Rickshaw.SeriesXDateTime.zeroFill = function(series) {
	Rickshaw.SeriesXDateTime.fill(series, 0);
};

Rickshaw.SeriesXDateTime.fill = function(series, fill) {

	var x;
	var i = 0;

	var data = series.map( function(s) { return s.data } );

	while ( i < Math.max.apply(null, data.map( function(d) { return d.length } )) ) {

		x = Math.min.apply( null,
			data
				.filter(function(d) { return d[i] })
				.map(function(d) { return d[i].x })
		);

		data.forEach( function(d) {
			if (!d[i] || d[i].x != x) {
				d.splice(i, 0, { x: x, y: fill });
			}
		} );

		i++;
	}
};

/*Own Rickshaw Series - End*/

/*Own Rickshaw FixedDuration - Start*/

Rickshaw.SeriesXDateTime.FixedDurationMovable = Rickshaw.Class.create(Rickshaw.SeriesXDateTime, {

	initialize: function (data, palette, options) {

		options = options || {};

		if (typeof(options.timeInterval) === 'undefined') {
			throw new Error('FixedDuration series requires timeInterval');
		}

		if (typeof(options.maxDataPoints) === 'undefined') {
			throw new Error('FixedDuration series requires maxDataPoints');
		}

		this.palette = new Rickshaw.Color.Palette(palette);
		this.timeBase = typeof(options.timeBase) === 'undefined' ? Math.floor(new Date().getTime() / 1000) : options.timeBase;
		this.setTimeInterval(options.timeInterval);

		if (this[0] && this[0].data && this[0].data.length) {
			this.currentSize = this[0].data.length;
			this.currentIndex = this[0].data.length;
		} else {
			this.currentSize  = 0;
			this.currentIndex = 0;
		}

		this.maxDataPoints = options.maxDataPoints;


		if (data && (typeof(data) == "object") && Array.isArray(data)) {
			data.forEach( function (item) { this.addItem(item) }, this );
			this.currentSize  += 1;
			this.currentIndex += 1;
		}

		// reset timeBase for zero-filled values if needed
		this.timeBase -= (this.maxDataPoints - this.currentSize) * this.timeInterval;

		// zero-fill up to maxDataPoints size if we don't have that much data yet
		if ((typeof(this.maxDataPoints) !== 'undefined') && (this.currentSize < this.maxDataPoints)) {
			for (var i = this.maxDataPoints - this.currentSize - 1; i > 1; i--) {
				this.currentSize  += 1;
				this.currentIndex += 1;
				this.forEach( function (item) {
					item.data.unshift({ x: ((i-1) * this.timeInterval || 1) + this.timeBase, y: 0, i: i });
				}, this );
			}
		}
	},

	addData: function($super, data, x) {

		$super(data, x);

		this.currentSize += 1;
		this.currentIndex += 1;

		if (this.maxDataPoints !== undefined) {
			while (this.currentSize > this.maxDataPoints) {
				this.dropData();
			}
		}
	},

	dropData: function() {

		this.forEach(function(item) {
			item.data.splice(0, 1);
		} );

		this.currentSize -= 1;
	},

	getIndex: function () {
		return this.currentIndex;
	}
} );
/*Own Rickshaw Series - End*/

var tv = 60;
var hspa = {};
var hspb = {};
//update hash (associative array) with incoming word and count

var s1 = d3.scale.linear().domain([0, 100]).nice();
var palette = new Rickshaw.Color.Palette( { scheme: 'colorwheel' } );

var throughput = new Rickshaw.Graph({
    element: document.querySelector("#chart2"),
    width: "650",
    height: "200",
    renderer: "line",
    stroke: true,
  	preserve: true,
    series: new Rickshaw.SeriesXDateTime.FixedDurationMovable([{
        name: 'Router-B', color: '#000000', scale: s1
    }], undefined, {
        timeInterval: tv,
        maxDataPoints: 20,
        timeBase: new Date().getTime() / 100
    })
});

throughput.render();

var ticksTreatment = 'glow';


var xAxis = new Rickshaw.Graph.Axis.Time( {
  graph: throughput,
	timeFixture: new Rickshaw.Fixtures.Time.Local()
  } );
xAxis.render();


var hoverDetail = new Rickshaw.Graph.HoverDetail( {
	graph: throughput,
	xFormatter: function(x) {
		return new Date(x * 1000).toString();
	}
} );



var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
  element: document.getElementById('axis2'),
  graph: throughput,
  orientation: 'left',
  scale: s1,
  grid: false,
  tickFormat: Rickshaw.Fixtures.Number.formatKMBT
});
yAxis.render();

var legend = new Rickshaw.Graph.Legend( {
	graph: throughput,
	element: document.getElementById('legend2')

} );


var xmlhttp = new XMLHttpRequest();
var url = localStorage.getItem("cpu_url");
var params = "?serial=APM00143230622"
xmlhttp.onreadystatechange=function() {
    if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
        cpuProcessor(xmlhttp.responseText);
    }
}
xmlhttp.open("POST", url, true);
xmlhttp.send(params);

function cpuProcessor(response) {
    var arr = JSON.parse(response);
    var i;
    for(i = 0; i < arr.length; i++) {
        hspa[arr[i].ts] = arr[i].spa;
        hspb[arr[i].ts] = arr[i].spb;
        addCPUData(throughput, arr[i].ts);
    }
		throughput.render();
//		previewXAxis.render();
		xAxis.render();
		yAxis.render();
}

function getSeconds(ts)
{
    return (new Date(Date.parse(ts + " UTC"))/ 1000);
}

var lastCPUTS_sec = 0;
var timeBase = new Date().getTime()/1000;

function addCPUData(chart, ts) {
    var data = {
        B: hspa[ts],
    };
    currentTS_sec = getSeconds(ts);
    if(currentTS_sec > lastCPUTS_sec)
    {
      xValue = currentTS_sec;
      chart.series.addData(data, xValue);
      lastCPUTS_sec = currentTS_sec;
    }
}
/*
var preview = new Rickshaw.Graph.RangeSlider.Preview( {
	graph: throughput,
	element: document.getElementById('preview2')
} );

var previewXAxis = new Rickshaw.Graph.Axis.Time({
	graph: preview.previews[0],
	timeFixture: new Rickshaw.Fixtures.Time.Local(),
	ticksTreatment: ticksTreatment
});

previewXAxis.render();
*/
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
		source = message.split("|")[1];
		graph = message.split("|")[2];
		type2 = message.split("|")[3];
		console.log(message);
		if(type == "time_series" && graph == "Router-B")
		{
			B = message.split("|")[4];
			value = (B*1500)/1000000000;
			var now = new Date;
			var ts = now.getUTCFullYear()+"-"+now.getUTCMonth()+"-"+now.getUTCDate()+" "+ now.getUTCHours() + ":" + now.getUTCMinutes() +":" + now.getUTCSeconds();
			console.log("plot: ",ts, value)
			hspa[ts] = value;
			addCPUData(throughput, ts);
			throughput.render();
			//previewXAxis.render();
			xAxis.render();
			yAxis.render();
		}
}) ;


socket.on('disconnect', function() {
		console.log('disconnected');
});

socket.connect();
});
