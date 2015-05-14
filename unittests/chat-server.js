var io = require('socket.io').listen(5000);
var clients = {};

io.sockets.on('connection', function (socket) {
  var userName;
  socket.on('connection name',function(user){
    userName = user.name;
    clients[user.name] = socket;
    io.sockets.emit('new user', user.name + " has joined.");
  });

  socket.on('message', function(msg){
    io.sockets.emit('message', msg);
  });

  socket.on('private message', function(msg){
    fromMsg = {from:userName, txt:msg.txt}
    clients[msg.to].emit('private message', fromMsg);  
  });

  socket.on('disconnect', function(){
    delete clients[userName];
  });
});