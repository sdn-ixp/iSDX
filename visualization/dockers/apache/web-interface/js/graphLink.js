$(document).ready(
  function() {/*Own Rickshaw Series - Start*/

var w = 960, h = 700;
    var data = [
      {
        "source": "SF",
        "target": "Chicago",
        "weight": 1
      },
      {
        "source": "SF",
        "target": "LA",
        "weight": 1
      },
      {
        "source":"SF",
        "target":"Dallas",
        "weight":1
      },
      {
        "source":"Dallas",
        "target":"LA",
        "weight":1
      },
      {
        "source":"Dallas",
        "target":"Houston",
        "weight":1
      },
      {
        "source":"Dallas",
        "target":"Miami",
        "weight":1
      },
      {
        "source":"Chicago",
        "target":"Miami",
        "weight":1
      },
      {
        "source":"Chicago",
        "target":"NY",
        "weight":1
      },
      {
        "source":"LA",
        "target":"Houston",
        "weight":1
      },
      {
        "source":"Miami",
        "target":"NY",
        "weight":1
      },
      {
        "source":"Miami",
        "target":"Tampa",
        "weight":1
      },
      {
        "source":"Miami",
        "target":"Houston",
        "weight":1
      },
      {
        "source":"Houston",
        "target":"Tampa",
        "weight":1
      },
      {
        "source":"Tampa",
        "target":"NY",
        "weight":1
      },
      {
        "source":"NY",
        "target":"Tampa",
        "weight":1
      },
      {
        "source":"Dallas",
        "target":"Chicago",
        "weight":1
      }
    ];
    var labelDistance = 0;

    var vis = d3.select("#graphLink").append("svg:svg").attr("width", w).attr("height", h);

    var nodes = [];
    var labelAnchors = [];
    var labelAnchorLinks = [];
    var links = [];

    nodeCities = [
        { key: 'SF'},
        { key: 'LA'},
        { key: 'Houston'},
        { key: 'Tampa'},
        { key: 'NY'},
        { key: 'Miami'},
        { key: 'Dallas'},
        { key: 'Chicago'}
    ]

    nodeCities.forEach(function(d,i) {
      var node = {
        label :  nodeCities[i].key
      };
      nodes.push(node);
      labelAnchors.push({
        node : node
      });
      labelAnchors.push({
        node : node
      });
    });

  //  var redraw = function(color){

      data.forEach(function(d,i){
        var source_index = 0;
        var target_index = 0;
        nodes.forEach(function(d,j){
          if(nodes[j].label == data[i].source)
          {
            source_index = j;
          }
          if(nodes[j].label == data[i].target)
          {
            target_index = j;
          }
        });
        console.log(source_index, target_index);
  			links.push({
          source: source_index,
          target: target_index,
          weight: Math.random()
        });
        console.log(links);
  		});

    console.log(links);

    for(var i = 0; i < nodes.length; i++) {
      labelAnchorLinks.push({
        source : i * 2,
        target : i * 2 + 1,
        weight : 1
      });
    };

    var force = d3.layout.force().size([w, h]).nodes(nodes).links(links).gravity(1).linkDistance(50).charge(-3000).linkStrength(function(x) {
      return x.weight * 10
    });


    force.start();

    var force2 = d3.layout.force().nodes(labelAnchors).links(labelAnchorLinks).gravity(0).linkDistance(0).linkStrength(8).charge(-100).size([w, h]);
    force2.start();

    var link = vis.selectAll("line.link").data(links).enter().append("svg:line").attr("class", "link").style("stroke", "#CCC");

    var node = vis.selectAll("g.node").data(force.nodes()).enter().append("svg:g").attr("class", "node");
    node.append("svg:circle").attr("r", 5).style("fill", "#555").style("stroke", "#FFF").style("stroke-width", 3);
    node.call(force.drag);


    var anchorLink = vis.selectAll("line.anchorLink").data(labelAnchorLinks)//.enter().append("svg:line").attr("class", "anchorLink").style("stroke", "#999");

    var anchorNode = vis.selectAll("g.anchorNode").data(force2.nodes()).enter().append("svg:g").attr("class", "anchorNode");
    anchorNode.append("svg:circle").attr("r", 0).style("fill", "#FFF");
      anchorNode.append("svg:text").text(function(d, i) {
      return i % 2 == 0 ? "" : d.node.label
    }).style("fill", "#555").style("font-family", "Arial").style("font-size", 12);

    var updateLink = function() {
      this.attr("x1", function(d) {
        return d.source.x;
      }).attr("y1", function(d) {
        return d.source.y;
      }).attr("x2", function(d) {
        return d.target.x;
      }).attr("y2", function(d) {
        return d.target.y;
      });

    }

    var updateNode = function() {
      this.attr("transform", function(d) {
        return "translate(" + d.x + "," + d.y + ")";
      });

    }


    force.on("tick", function() {

      force2.start();

      node.call(updateNode);

      anchorNode.each(function(d, i) {
        if(i % 2 == 0) {
          d.x = d.node.x;
          d.y = d.node.y;
        } else {
          var b = this.childNodes[1].getBBox();

          var diffX = d.x - d.node.x;
          var diffY = d.y - d.node.y;

          var dist = Math.sqrt(diffX * diffX + diffY * diffY);

          var shiftX = b.width * (diffX - dist) / (dist * 2);
          shiftX = Math.max(-b.width, Math.min(0, shiftX));
          var shiftY = 5;
          this.childNodes[1].setAttribute("transform", "translate(" + shiftX + "," + shiftY + ")");
        }
      });
      anchorNode.call(updateNode);
      link.call(updateLink);
      anchorLink.call(updateLink);
    });
//  }
//  redraw('#fff');

  //Repeat every 3 seconds
/*setInterval(function(){
	redraw('#000')
}, 3000);*/
});
