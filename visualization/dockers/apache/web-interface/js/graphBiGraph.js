$(document).ready(
  function() {
    var links = [
      {
        "source": "SF",
        "target": "Chicago",
        "weight": 10
      },
      {
        "source": "SF",
        "target": "LA",
        "weight": 20
      },
      {
        "source":"SF",
        "target":"Dallas",
        "weight":30
      },
      {
        "source":"Dallas",
        "target":"LA",
        "weight":40
      },
      {
        "source":"Dallas",
        "target":"Houston",
        "weight":50
      },
      {
        "source":"Dallas",
        "target":"Miami",
        "weight":60
      },
      {
        "source":"Chicago",
        "target":"Miami",
        "weight":70
      },
      {
        "source":"Chicago",
        "target":"NY",
        "weight":80
      },
      {
        "source":"LA",
        "target":"Houston",
        "weight":90
      },
      {
        "source":"Miami",
        "target":"NY",
        "weight":100
      },
      {
        "source":"Miami",
        "target":"Tampa",
        "weight":90
      },
      {
        "source":"Miami",
        "target":"Houston",
        "weight":10
      },
      {
        "source":"Houston",
        "target":"Tampa",
        "weight":20
      },
      {
        "source":"Tampa",
        "target":"NY",
        "weight":40
      },
      {
        "source":"NY",
        "target":"Tampa",
        "weight":90
      },
      {
        "source":"Dallas",
        "target":"Chicago",
        "weight":60
      }
    ];

    var color = ['#e7e1ef' ,'#df65b0','#ce1256','#980043','#67001f'];

    // Compute the distinct nodes from the links.
    var lookup = function(weight) {
      if(weight === 105) {
        return "#FFFF00";
      }
      if(weight < 0 )
      {
        return "#FFF"
      }
      if(weight <= 20) {
        return color[0];
      }
      if(weight <= 40) {
        return color[1];
      }
      if(weight <= 60) {
        return color[2];
      }
      if(weight <= 80) {
        return color[3];
      }
      if(weight <= 100) {
        return color[4];
      }
    };

    var setup = function(targetID){



    //console.log(links);
    var width = 960,
        height = 500;

    var svg = d3.select(targetID).append("svg")
        .attr("width", width)
        .attr("height", height);
        var force = d3.layout.force();


        //Package and export settings
        var settings = {
         width:width, height:height,svg:svg, force: force
        }
        return settings;
      }

      var redrawChart = function(settings, links) {
      	//Import settings
        nodes = {}
      	var width=settings.width, height=settings.height,svg=settings.svg, force=settings.force;
        links.forEach(function(link) {
            link.source = nodes[link.source] ||
                (nodes[link.source] = {name: link.source});
            link.target = nodes[link.target] ||
                (nodes[link.target] = {name: link.target});
            link.value = +link.weight;
            link.color = lookup(link.weight)
        });



    // build the arrow.
    var marker = svg.append("svg:defs").selectAll("marker")
        .data(["end"])      // Different link/path types can be defined here
      .enter().append("svg:marker")    // This section adds in the arrows
        .attr("id", String)
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 15)
        .attr("refY", -1.5)
        .attr("markerWidth", 8)
        .attr("markerHeight", 8)
        .attr("orient", "auto")
        .attr("fill", function(d) { return "red";})
      .append("svg:path")
        .attr("d", "M0,-5L10,0L0,5");

    // add the links and the arrows
    var path = svg.append("svg:g").selectAll("path")
        .data(force.links())
      .enter().append("svg:path")
    //    .attr("class", function(d) { return "link " + d.type; })
        .attr("class", "link")
        .attr("marker-end", "url(#end)")
        .attr("stroke", function(d) { return d.color;} )
        .attr("stroke-width", "2px")
        .attr("fill", "none");

    // define the nodes
    var node = svg.selectAll(".node")
        .data(force.nodes())
      .enter().append("g")
        .attr("class", "node")
        .call(force.drag);

    // add the nodes
    node.append("circle")
        .attr("r", 16);

    // add the text
    node.append("text")
        .attr("x", 16)
        .attr("dy", ".35em")
        .text(function(d) { return d.name; });

    // add the curvy lines
    function tick() {
        path.attr("d", function(d) {
            var dx = d.target.x - d.source.x,
                dy = d.target.y - d.source.y,
                dr = Math.sqrt(dx * dx + dy * dy);
            return "M" +
                d.source.x + "," +
                d.source.y + "A" +
                dr + "," + dr + " 0 0,1 " +
                d.target.x + "," +
                d.target.y;
        });

        node
            .attr("transform", function(d) {
      	    return "translate(" + d.x + "," + d.y + ")"; });
    }
    force
        .nodes(d3.values(nodes))
        .links(links)
        .size([width, height])
        .linkDistance(100)
        .charge(-12000)
        .on("tick", tick)
        .start();
  }
    var settings = setup('#graphLink');
    redrawChart(settings,links);

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
    		if(type == "ng")
    		{
          console.log(message);
    			source = message.split("|")[1];
    			target = message.split("|")[2];
          weight = message.split("|")[3];
          console.log(source, target);
          index = 0;
          for (var i = 0; i < links.length; i++) {
                if (links[i].source.id == source && links[i].target.id == target) {
                    links.splice(i, 1);
                    break;
                }
            }
    			redrawChart(settings,links);
          links.push({"source": source, "target": target, "weight": weight })
          redrawChart(settings,links);

    		}
    }) ;

    socket.on('disconnect', function() {
    		console.log('disconnected');
    });

    socket.connect();

});
