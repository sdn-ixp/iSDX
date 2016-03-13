var app = require("express")();

app.use(function(req, res, next) {
  res.append("Access-Control-Allow-Origin", "*");
  res.append("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
  res.append('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, PATCH, DELETE');
  res.append('Access-Control-Allow-Credentials', true);
  next();
});
  var http = require('http')
  , server = http.Server(app)
  , io = require('socket.io');


var redis = require('redis');

var socket  = io.listen(server);

server.listen(8080, '0.0.0.0');
socket.on('connection', function(client) {
        console.log("WebSocket Connected to server");
        var subscribe1 = redis.createClient('6379', 'redis');
        var subscribe2 = redis.createClient('6379', 'redis');

        subscribe1.subscribe('stats'); //    listen to messages from channel pubsub
        subscribe2.subscribe('sdx_stats'); //    listen to messages from channel pubsub

        subscribe1.on("message", function(channel, message) {
            console.log(message);   // Debug output
            client.send(message);
        });

        subscribe2.on("message", function(channel, message) {
            console.log(message);   // Debug output
            client.send(message);
        });

        client.on('message', function(msg) {
        });

        client.on('disconnect', function() {
            subscribe1.quit();
            subscribe2.quit();
        });
    });
