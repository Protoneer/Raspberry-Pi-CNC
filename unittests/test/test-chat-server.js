var should = require('should');
var io = require('socket.io-client');
//,   server = require('../chat-server');



var socketURL = 'http://0.0.0.0:5000/test';

var options ={
  transports: ['websocket'],
  'force new connection': true
};

describe("RPI CNC Server",function(){

  /* Test 1 - A Single User */
  it('Connection should return ports',function(done){
    //var client = io.connect(socketURL, options);
    var client = io.connect(socketURL);

    client.on('connect',function(data){
	client.on('ports',function(portData){
	  console.log(portData['comName']);
	  client.disconnect();
	  done();
	});
    });
  });





});
