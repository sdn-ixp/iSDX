var tooltip = d3.selectAll(".tooltip:not(.css)");
var SVGmouseTip = d3.select("g.tooltip.mouse");

d3.select("svg").select("g")
    .selectAll("circle")

    .attr("title", "Automatic Title Tooltip")

    .on("mouseover", function () {
        tooltip.style("opacity", "1");
        tooltip.style("color", this.getAttribute("fill") );
    })
    .on("mousemove", function () {

        var mouseCoords = d3.mouse(
            SVGmouseTip.node().parentElement);

        SVGmouseTip
            .attr("transform", "translate("
                  + (mouseCoords[0]-10) + ","
                  + (mouseCoords[1] - 10) + ")");
    })
    .on("mouseout", function () {
        return tooltip.style("opacity", "0");
    });
