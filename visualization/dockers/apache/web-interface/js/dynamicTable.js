$(document).ready(
function() {
  var make_key_value = function(k, v) {
    return { key: k,
             value: v
           };
  };

  // Join a key array with a data array.
  // Return an array of key-value objects.
  var merge = function(keys, values) {
    var l = keys.length;
    var d = [], v, k;
    for(var i = 0; i < l; i++) {
      v = values[i].slice();
      k = keys[i];
      d.push( make_key_value( k, v ));
    }
    return d;
  };


  // Shuffles the input array.
  function shuffle(array) {
    var m = array.length, t, i;
    while (m) {
      i = Math.floor(Math.random() * m--);
      t = array[m], array[m] = array[i], array[i] = t;
    }
    return array;
  }

  // Returns a random integer between min and max
  // Using Math.round() will give you a non-uniform distribution!
  function get_random_int(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  // Resize the array, append random numbers if new_size is larger than array.
  function update_array(a, new_size) {

    a = a || [];

    if (a.length > new_size) {
      return a.slice(0, new_size);
    }

    var delta = new_size - a.length;
    for(var i = 0; i < delta; i++) {
      a.push(get_random_int(0, 9));
    }

    return a;
  };


  ////////////////////////////////////////////////////////////
  // GENERATE DATA
  var alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");

  var letter_to_data = {}; // store row data

  var generate_data = function(row_data) {

    return merge(["LSP-Names","LSP-1","LSP-2","LSP-3","LSP-4"], row_data);
  };

  /////////////////////////////////////////////
  // DEFINE HELPER FUNCTIONS
  // Extract key from key-value object.
  var get_key = function(d) { return d && d.key; };

  // Extract data from a key-value object.
  // Prepend the key so it is the first item in the values array.
  var extract_row_data = function(d) {

    var values = d.value.slice();

    // Prepend the key
    values.unshift(d.key);
    return values;

  };

  // Use data as is.
  var ident = function(d) { return d; };


  /////////////////////////////////////////////
  // UPDATE THE TABLE

  // Select the table element
  var table = d3.select('#pathsF');
  table.attr("line-height", "0");


  // Define function to update data
  var update = function(new_data) {

    var rows = table.selectAll('tr').data(new_data, get_key);

    //////////////////////////////////////////
    // ROW UPDATE SELECTION

    // Update cells in existing rows.
    var cells = rows.selectAll('td').data(extract_row_data);

    cells.attr('class', 'update');

    // Cells enter selection
    cells.enter().append('td')
      .style('opacity', 0.0)
      .attr("dy",".35em")
      .attr("dx","0.5em")
      .attr("border-spacing", "10px")
      .attr("margin", "12px 12px 12px 12px")
      .attr("padding","12px 12px 12px 12px")
      .attr("line-height", "0")
      .attr('class', 'enter')
      .transition()
      .delay(900)
      .duration(500)
      .style('opacity', 1.0)
      .style("line-height", "0");

    cells.text(ident);

    // Cells exit selection
    cells.exit()
      .attr('class', 'exit')
      .transition()
      .delay(200)
      .duration(500)
      .style('opacity', 0.0)
      .remove();

    //////////////////////////////////////////
    // ROW ENTER SELECTION
    // Add new rows
    var cells_in_new_rows = rows.enter().append('tr')
                                .selectAll('td')
                                .data(extract_row_data);

    cells_in_new_rows.enter().append('td')
      .style('opacity', 0.0)
      .attr('class', 'enter')
      .transition()
      .delay(900)
      .duration(500)
      .style('opacity', 1.0);

    cells_in_new_rows.text(ident);

    /////////////////////////////////////////
    // ROW EXIT SELECTION
    // Remove old rows
    rows.exit()
      .attr('class', 'exit')
      .transition()
      .delay(200)
      .duration(500)
      .style('opacity', 0.0)
      .remove();

    table.selectAll('tr').select('td').classed('row-header', true);

  };


    var row_data = []
    row1 = []
    row1 = ["East-to-West","West-to-East"];
    row2 = ["Chicago-to-sf", "sf-to-chicago"];
    row3= ["Chicago-to-sf", "sf-to-chicago"];
    row4= ["Chicago-to-sf", "sf-to-chicago"];
    row5= ["Chicago-to-sf", "sf-to-chicago"];

    row_data.push(row1);
    row_data.push(row2);
    row_data.push(row3);
    row_data.push(row4);
    row_data.push(row5);
  // Generate and display some random table data.
  update(generate_data(row_data));

  //renderData("#pathsB", datab);

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

      if(type == "pathf")
      {
        key = message.split("|")[1];
        val = message.split("|")[2];
        if(key === "lsp1")
        {
          row_data[1][0] = val;
        }
        if(key === "lsp2")
        {
          row_data[2][0] = val;
        }
        if(key === "lsp3")
        {
          row_data[3][0] = val;
        }
        if(key === "lsp4")
        {
          row_data[4][0] = val;
        }

        update(generate_data(row_data));
      }
      else if(type == "pathb")
      {
        key = message.split("|")[1];
        val = message.split("|")[2];
        if(key === "lsp1")
        {
          row_data[1][1] = val;
        }
        if(key === "lsp2")
        {
          row_data[2][1] = val;
        }
        if(key === "lsp3")
        {
          row_data[3][1] = val;
        }
        if(key === "lsp4")
        {
          row_data[4][1] = val;
        }
        update(generate_data(row_data));
      }
  }) ;

  socket.on('disconnect', function() {
      console.log('disconnected');
  });

  socket.connect();
});
