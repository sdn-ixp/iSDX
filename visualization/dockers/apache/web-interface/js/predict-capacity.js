;( function() {
  var data = {
    lineChart : [
      {
        date  : '2014-08-22',
        label : 'past',
        value : 4639
      },
      {
        date  : '2015-08-22',
        label : 'current',
        value : 5868
      },
      {
        date  : '2016-08-22',
        label : 'future',
        value : 7589
      }
    ]
  };

  var DURATION = 1500;
  var DELAY    = 500;
  /**
   * draw the fancy line chart
   *
   * @param {String} elementId elementId
   * @param {Array}  data      data
   */
  function drawLineChart( elementId, data ) {
    // parse helper functions on top
    var parse = d3.time.format( '%Y-%m-%d' ).parse;
    // data manipulation first
    data = data.map( function( datum ) {
      datum.date = parse( datum.date );
      return datum;
    } );

    // TODO code duplication check how you can avoid that
    var containerEl = document.getElementById( elementId ),
        width       = containerEl.clientWidth,
        height      = width * 0.4,
        margin      = {
          top    : 40,
          right  : 10,
          left   : 10
        },

        detailWidth  = 128,
        detailHeight = 50,
        detailMargin = 5,

        container   = d3.select( containerEl ),
        svg         = container.select( 'svg' )
                                .attr( 'width', width )
                                .attr( 'height', height + margin.top ),

        x          = d3.time.scale().range( [ 0, width - detailWidth ] ),
        xAxis      = d3.svg.axis()
                    .scale(x)
                    .orient("bottom"),

        xAxisTicks = d3.svg.axis().scale( x )
                                  .ticks( 3 )
                                  .tickSize( -height )
                                  .tickFormat( '' )
                                  .orient('bottom'),

        y          = d3.scale.linear().range( [ height, 0 ] ),

        yScale = d3.scale.linear()
	                 .domain([0, height])    // values between 0 and 100
		              .range([height - 10, 10]),   // map these to the chart height, less padding.
                 //REMEMBER: y axis range has the bigger number first because the y value of zero is at the top of chart and increases as you go down.

       yAxis = d3.svg.axis()
                .scale(y)
                .orient("left")
                .ticks(5),

        yAxisTicks = d3.svg.axis().scale( y )
                                  .ticks( 12 )
                                  .orient( 'left' ),

        area = d3.svg.area()
                      .interpolate( 'linear' )
                      .x( function( d )  { return x( d.date ) + detailWidth / 2; } )
                      .y( function( d ) { return y( d.value ); } ),

        line = d3.svg.line()
                  .interpolate( 'linear' )
                  .x( function( d ) { return x( d.date ) + detailWidth / 2; } )
                  .y( function( d ) { return y( d.value ); } ),

        startData = data.map( function( datum ) {
                      return {
                        date  : datum.date,
                        value : 0
                      };
                    } ),

        circleContainer;

        // Compute the minimum and maximum date, and the maximum price.
        x.domain( [ data[ 0 ].date, data[ data.length - 1 ].date ] );
        // hacky hacky hacky :(
        y.domain( [ 0, d3.max( data, function( d ) { return d.value; } ) + 3000 ] );

        svg.append( 'g' )
            .attr( 'class', 'axis' )
            .attr( 'transform', 'translate(' + detailWidth / 2 + ',' + ( height + 7 ) + ')' )
            .attr("font-size", "16px")
            .attr("font-family","'Times New Roman', Georgia, Serif")
            .call( xAxis );

          svg.append("g")
              .attr("class", "axis")
              .attr("transform", "translate(" + 50 + ",0)")
              .attr("font-size", "16px")
              .attr("font-family","'Times New Roman', Georgia, Serif")
              .call(yAxis);

          // Add the line path.
          svg.append( 'path' )
              .datum( startData )
              .attr( 'class', 'line' )
              .attr( 'd', line )
              .transition()
              .duration( DURATION )
              .delay( DURATION / 2 )
              .attrTween( 'd', tween( data, line ) )
              .each( 'end', function() {
                drawCircles( data );
              } );

    // Helper functions!!!
    function drawCircle( datum, index ) {
      circleContainer.datum( datum )
                    .append( 'circle' )
                    .attr( 'class', 'lineChart--circle' )
                    .attr( 'r', 0 )
                    .attr(
                      'cx',
                      function( d ) {
                        return x( d.date ) + detailWidth / 2;
                      }
                    )
                    .attr(
                      'cy',
                      function( d ) {
                        return y( d.value );
                      }
                    )
                    .on( 'mouseenter', function( d ) {
                      d3.select( this )
                        .attr(
                          'class',
                          'lineChart--circle lineChart--circle__highlighted'
                        )
                        .attr( 'r', 7 );
                        d.active = true;

                        showCircleDetail( d );
                    } )
                    .on( 'mouseout', function( d ) {
                      d3.select( this )
                        .attr(
                          'class',
                          'lineChart--circle'
                        )
                        .attr( 'r', 6 );

                      if ( d.active ) {
                        hideCircleDetails();

                        d.active = false;
                      }
                    } )
                    .on( 'click touch', function( d ) {
                      if ( d.active ) {
                        showCircleDetail( d )
                      } else {
                        hideCircleDetails();
                      }
                    } )
                    .transition()
                    .delay( DURATION / 10 * index )
                    .attr( 'r', 6 );
    }

    function drawCircles( data ) {
      circleContainer = svg.append( 'g' );

      data.forEach( function( datum, index ) {
        drawCircle( datum, index );
      } );
    }

    function hideCircleDetails() {
      circleContainer.selectAll( '.lineChart--bubble' )
                      .remove();
    }

    function showCircleDetail( data ) {
      var details = circleContainer.append( 'g' )
                        .attr( 'class', 'lineChart--bubble' )
                        .attr(
                          'transform',
                          function() {
                            var result = 'translate(';

                            result += x( data.date );
                            result += ', ';
                            result += y( data.value ) - detailHeight - detailMargin;
                            result += ')';

                            return result;
                          }
                        ).attr("font-size", "14px")
                        .attr("font-family","'Times New Roman', Georgia, Serif");

      details.append( 'path' )
              .attr( 'd', 'M2.99990186,0 C1.34310181,0 0,1.34216977 0,2.99898218 L0,47.6680579 C0,49.32435 1.34136094,50.6670401 3.00074875,50.6670401 L44.4095996,50.6670401 C48.9775098,54.3898926 44.4672607,50.6057129 49,54.46875 C53.4190918,50.6962891 49.0050244,54.4362793 53.501875,50.6670401 L94.9943116,50.6670401 C96.6543075,50.6670401 98,49.3248703 98,47.6680579 L98,2.99898218 C98,1.34269006 96.651936,0 95.0000981,0 L2.99990186,0 Z M2.99990186,0' )
              .attr( 'width', detailWidth )
              .attr( 'height', 0 );

      var text = details.append( 'text' )
                        .attr( 'class', 'lineChart--bubble--text' )
                        .attr("font-size", "14px")
                        .attr("text-shadow", "None")
                        .attr("font-family","'Times New Roman', Georgia, Serif");

      text.append( 'tspan' )
          .attr( 'class', 'lineChart--bubble--label' )
          .attr( 'x', detailWidth / 2 )
          .attr( 'y', detailHeight / 3 )
          .attr( 'text-anchor', 'middle' )
          .attr("font-family","'Times New Roman', Georgia, Serif")
          .text( data.label );

      text.append( 'tspan' )
          .attr( 'class', 'lineChart--bubble--value' )
          .attr( 'x', detailWidth / 2 )
          .attr( 'y', detailHeight / 4 * 3 )
          .attr( 'text-anchor', 'middle' )
          .attr("font-family","'Times New Roman', Georgia, Serif")
          .text( data.value + " GB" );
    }

    function tween( b, callback ) {
      return function( a ) {
        var i = d3.interpolateArray( a, b );

        return function( t ) {
          return callback( i ( t ) );
        };
      };
    }
  }

  function ಠ_ಠ() {
    drawLineChart(    'lineChart',    data.lineChart );
  }
  // yeah, let's kick things off!!!
  ಠ_ಠ();

})();
