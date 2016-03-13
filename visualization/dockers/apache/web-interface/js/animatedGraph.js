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

       this.removeLink = function (source, target, type) {
           console.log(links);
           for (var i = 0; i < links.length; i++) {
             console.log("removing: " , links[i].source.id , " ", links[i].target.id);
               if (links[i].source.id == source && links[i].target.id == target && links[i].type == type) {
                   console.log("removing: " , links[i].source.id , " ", links[i].target.id);
                   links.splice(i, 1);
                   console.log(links, i);
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

       this.addLink = function (source, target, type, value) {
          var color_map = lookup(type);
          var size = lookupSize(parseInt(value));
           links.push({"source": findNode(source), "target": findNode(target), "value": value, "color": color_map, "type": type, "size": size});
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
               .attr("height", h);
               // Per-type markers, as they don't inherit styles.
        vis.append("svg:defs").selectAll("marker")
        .data(["bgp", "arp", "default"])
          .enter().append("svg:marker")
            .attr("id", String)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 5)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
          .append("svg:path")
            .attr("d", "M0,-5L10,0L0,5");


       var vis = vis.append("svg:g");

       var force = d3.layout.force();

       var nodes = force.nodes(),
           links = force.links();

       var update = function () {


            var link = vis.selectAll("path")
                    .data(links, function (d) {
                        return d.source.id + "_" + d.target.id;
                    });


           link.enter().append("svg:path")
                   .attr("id", function (d) {
                       return d.source.id + "_" + d.target.id;
                   })
                   .attr("class", "link")
                   .attr("stroke-width", function(d) { return d.size; })
                   .attr("marker-end", function(d) { return "url(#" + d.type + ")"; })
                   .attr("stroke", function(d) { return d.color;})
                   .attr("fill", "none");

           link.exit().remove();



           var node = vis.selectAll("g.node")
                   .data(nodes, function (d) {
                       return d.id;
                   });

           var nodeEnter = node.enter().append("g")
                   .attr("class", "node")
                   .call(force.drag);

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

           var width = 1095 ,
           height = 850-225;
           var color = d3.scale.ordinal()
           .domain(["arp", "bgp", "default"])
           .range(['#0063ff' ,'#B30001','#000000']);

           var legendRectSize = 40;
           var legendSpacing = 20;
           var legend = vis.selectAll(".legend")
               .data(color.domain())



              legend.enter()
               .append('g')
                 .attr('class', 'legend')
                 .attr('transform', function(d, i) {
                   var height = legendRectSize;
                   var x = 0;
                   var y = i * height;
                   return 'translate(' + x + ',' + y + ')';
               });

          legend.append('rect')
              .attr('width', legendRectSize)
              .attr('height', legendRectSize)
              .attr('y', function(d,i) { return height+legendRectSize;})
              .style('fill', color)
              .style('stroke', color);

          legend.append('text')
              .attr('x', legendRectSize + legendSpacing)
              .attr('y', height+legendRectSize+20)
              .attr("class", "mono")
              .text(function(d) { return d; });

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
       var lookup = function(type) {

         if(type == "bgp")
         {
           return "#B30001";
         }
         if(type == "arp")
         {
           return "#0063ff";
         }
         if(type == "default")
         {
           return "#000000";
         }
       };

       var lookupSize = function(value) {

         if(value < 100)
         {
           return "3px";
         }
         if(value < 100000)
         {
           return "5px";
         }
         else
         {
           return "7px";
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
      	console.log("Node.js - Connected to Server animatedGraph");
      });

      socket.on('channel', function() {
      	console.log("Node.js - Connected to Server");
      });

      socket.on('message', function(message){

      		console.log(message);
          type = message.split("|")[0];
          if(type == "network_graph")
          {
      			source = message.split("|")[1];
      			target = message.split("|")[2];
            type = message.split("|")[3];
            weight = message.split("|")[4];
            if(weight == "0")
            {
              console.log("deleting stuff");
              graph.removeLink(source, target,type);
              keepNodesOnTop();
            }
            else {
              console.log(source,target);
              graph.removeLink(source, target,type);
              graph.addLink(source, target, type, weight);
              keepNodesOnTop();
            }

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
