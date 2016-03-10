$(document).ready(
  function() {
var graph;
   function myGraph() {

       // Add and remove elements on the graph object
       this.addNode = function (id, x, y) {
           nodes.push({"id": id, "x": x, "y": y, "fixed": true});
           update();
       };

       this.removeNode = function (id) {
           var i = 0;
           var n = findNode(id);
           while (i < links.length) {
               if ((links[i]['source'] == n) || (links[i]['target'] == n)) {
                   links.splice(i, 1);
               }
               else i++;
           }
           nodes.splice(findNodeIndex(id), 1);
           update();
       };

       this.removeLink = function (source, target) {
           for (var i = 0; i < links.length; i++) {
               if (links[i].source.id == source && links[i].target.id == target) {
                   links.splice(i, 1);
                   break;
               }
           }
           update();
       };

       this.removeallLinks = function () {
           links.splice(0, links.length);
           update();
       };

       this.removeAllNodes = function () {
           nodes.splice(0, links.length);
           update();
       };

       this.addLink = function (source, target, value) {
          var color_map = lookup(value);
           links.push({"source": findNode(source), "target": findNode(target), "value": value, "color": color_map});
           update();
       };

       var findNode = function (id) {
           for (var i in nodes) {
               if (nodes[i]["id"] === id) return nodes[i];
           }
           ;
       };

       var findNodeIndex = function (id) {
           for (var i = 0; i < nodes.length; i++) {
               if (nodes[i].id == id) {
                   return i;
               }
           }
           ;
       };

       // set up the D3 visualisation in the specified element
       var w = 1095,
               h = 850;

       var color = d3.scale.category10();

       var vis = d3.select("#graphLink")
               .append("svg:svg")
               .attr("width", w)
               .attr("height", h)
               .attr("id", "svg")
               .attr("pointer-events", "all")
               .attr("viewBox", "0 0 " + w + " " + h)
               .attr("perserveAspectRatio", "xMinYMid")
               .append('svg:g');

       var force = d3.layout.force();

       var nodes = force.nodes(),
               links = force.links();

       var update = function () {

         var defs = vis.selectAll("defs")
               .data(links, function (d) {
                   return d.source.id + "-" + d.target.id;
               });
          var marker = defs.enter().append("svg:defs")
              .attr("id", function (d) {
                        return d.source.id + "-" + d.target.id;
                    })
              .selectAll("marker")
             .data(["end"]) ;     // Different link/path types can be defined here

           marker.enter().append("svg:marker")    // This section adds in the arrows
             .attr("id", String)
             .attr("viewBox", "0 -5 10 10")
             .attr("refX", 15)
             .attr("refY", -1.5)
             .attr("markerWidth", 8)
             .attr("markerHeight", 8)
             .attr("orient", "auto")
             .attr("fill", function(d) { return "#e5e500";})
           .append("svg:path")
             .attr("d", "M0,-5L10,0L0,5");

            //marker.exit().remove();

            var link = vis.append("svg:g").selectAll("path")
                    .data(links, function (d) {
                        return d.source.id + "-" + d.target.id;
                    });


           link.enter().append("svg:path")
                   .attr("id", function (d) {
                       return d.source.id + "-" + d.target.id;
                   })
                   .attr("class", "link")
                   .attr("stroke-width", "3px")
                   .attr("marker-end", "url(#end)")
                   .attr("stroke", function(d) { return d.color;})
                   .attr("fill", "none");

           link.append("title")
                   .text(function (d) {
                       return d.value;
                   });
           link.exit().remove();

           var node = vis.selectAll("g.node")
                   .data(nodes, function (d) {
                       return d.id;
                   });

           var nodeEnter = node.enter().append("g")
                   .attr("class", "node")
                   .call(force.drag);

           nodeEnter.append("svg:circle")
                   .attr("r", 12)
                   .attr("id", function (d) {
                       return "Node;" + d.id;
                   })
                   .attr("class", "nodeStrokeClass")
                   .attr("fill", function(d) { return color(d.id); });

           nodeEnter.append("svg:text")
                   .attr("class", "textClass")
                   .attr("x", 14)
                   .attr("y", ".31em")
                   .text(function (d) {
                       return d.id;
                   });

           node.exit().remove();

           force.on("tick", function () {

               node.attr("transform", function (d) {
                   return "translate(" + d.x + "," + d.y + ")";
               });

               link.attr("d", function(d) {
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
           });

          var buckets = 5,
          colors = ['#1DBF22' ,'#036601','#054105','#EEA100','#B30001']; // alternatively colorbrewer.YlGnBu[9]


          var width = 1095 ,
          height = 850-150,
          gridSize = Math.floor(width / 24);
           var legendElementWidth = gridSize*2;
           var colorScale = d3.scale.quantile()
          .domain([0, 20, 40, 60, 80, 100])
          .range(colors);

           var legend = vis.selectAll(".legend")
              .data([0].concat(colorScale.quantiles()), function(d) { return d; });

          legend.enter().append("g")
              .attr("class", "legend");

          legend.append("rect")
            .attr("x", function(d, i) { return legendElementWidth * i; })
            .attr("y", height)
            .attr("width", legendElementWidth)
            .attr("height", gridSize / 2)
            .style("fill", function(d, i) { return colors[i]; });

          legend.append("text")
            .attr("class", "mono")
            .text(function(d) { return "≥ " + Math.round(d); })
            .attr("x", function(d, i) { return legendElementWidth * i; })
            .attr("y", height + gridSize);

          legend.exit().remove();

           // Restart the force layout.
           force
                   .gravity(.01)
                   .charge(-80000)
                   .friction(0)
                   .linkDistance( function(d) { return d.value * 5} )
                   .size([w, h])
                   .start();
       };

       var color_mapping = ['#1DBF22' ,'#036601','#054105','#EEA100','#B30001']; // alternatively colorbrewer.YlGnBu[9]

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
           return color_mapping[0];
         }
         if(weight <= 40) {
           return color_mapping[1];
         }
         if(weight <= 60) {
           return color_mapping[2];
         }
         if(weight <= 80) {
           return color_mapping[3];
         }
         if(weight <= 100) {
           return color_mapping[4];
         }
       };

       // Make it all go
       update();
   }
   function keepNodesOnTop() {
       $(".nodeStrokeClass").each(function( index ) {
           var gnode = this.parentNode;
           gnode.parentNode.appendChild(gnode);
       });
   }
   function addNodes() {
       d3.select("svg")
               .remove();
        drawGraph();
   }
   function drawGraph() {

      graph = new myGraph("#graphLink");


      graph.addNode('BGP-Proxy', 108, 141);
      graph.addNode('Router-A', 169, 470);
      graph.addNode('Main', 555, 389);
      graph.addNode('Outbound', 327, 127);
      graph.addNode('InBound', 648, 142);
      graph.addNode('ARP-Proxy', 953, 141);
      graph.addNode('Router-C1', 847, 471);
      graph.addNode('Router-C2', 874, 676);
      graph.addNode('Router-B', 520, 686);

/*
      graph.addLink('BGP-Proxy', 'Router-A', '20');
      graph.addLink('Router-A', 'Main', '20');
      graph.addLink('SF', 'DALLAS', '60');
      graph.addLink('DALLAS', 'LA', '30');
      graph.addLink('DALLAS', 'HOUSTON', '20');
      graph.addLink('DALLAS', 'MIAMI', '80');
      graph.addLink('CHICAGO', 'MIAMI', '10');
      graph.addLink('CHICAGO', 'NY', '70');
      graph.addLink('LA', 'HOUSTON', '90');
      graph.addLink('MIAMI', 'NY', '20');
      graph.addLink('MIAMI', 'TAMPA', '90');
      graph.addLink('MIAMI', 'HOUSTON', '10');
      graph.addLink('TAMPA', 'NY', '10');
      graph.addLink('DALLAS', 'CHICAGO', '20');*/
      keepNodesOnTop();

      // callback for the changes in the network
      var step = -1;
      function nextval()
      {
          step++;
          return 2000 + (1500*step); // initial time, wait time
      }

      setTimeout(function() {
        graph.removeLink('BGP-Proxy', 'Main');
        graph.addLink('Main', 'Router-B', '90');
          keepNodesOnTop();
      }, 3000);


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

      		if(type == "ng")
      		{
      			source = message.split("|")[1];
      			target = message.split("|")[2];
            weight = message.split("|")[3];
            graph.removeLink(source, target);
            graph.addLink(source, target, weight);
            keepNodesOnTop();
      		}
      }) ;

      socket.on('disconnect', function() {
      		console.log('disconnected');
      });

      socket.connect();

/*
      setTimeout(function() {
          graph.addLink('Sophia', 'Daniel', '20');
          keepNodesOnTop();
      }, nextval());

      setTimeout(function() {
          graph.addLink('Daniel', 'Alex', '20');
          keepNodesOnTop();
      }, nextval());

      setTimeout(function() {
          graph.addLink('Suzie', 'Daniel', '30');
          keepNodesOnTop();
      }, nextval());

      setTimeout(function() {
          graph.removeLink('Dylan', 'Mason');
          graph.addLink('Dylan', 'Mason', '8');
          keepNodesOnTop();
      }, nextval());

      setTimeout(function() {
          graph.removeLink('Dylan', 'Emma');
          graph.addLink('Dylan', 'Emma', '8');
          keepNodesOnTop();
      }, nextval());*/

  }
  drawGraph();

});
