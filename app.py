from . import artnet

import app
import wifi
import socket

from tildagonos import tildagonos
from system.eventbus import eventbus
from system.patterndisplay.events import PatternDisable

class ArtNetApp(app.App):
    data = b''

    def _on_data(self, net, subuniverse, data):
        if net == 0 and subuniverse == 1:
            self.data = data
    
    def _on_transmit(self, dest, data):
        self.socket.sendto(data, dest)
    
    def __init__(self):
        wifi.connect()
        self.artnet = artnet.ArtNet(wifi.get_ip(), 0x0000, 0x7ff0)
        self.artnet.set_node_name("Tildagon ArtNet")
        self.artnet.set_port_name("LEDs")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', artnet.PORT))
        self.socket.setblocking(False)
        self.artnet.send_handler = self._on_transmit
        self.artnet.universe_handler = self._on_data
        
        eventbus.emit(PatternDisable())
        
    def update(self, delta):
        while True:
            try:
                msg, src = self.socket.recvfrom(0x1000)
                self.artnet.on_data(msg, src)
            except OSError:
                break
    
    def draw(self, ctx):
        ctx.save()
        ctx.rgb(0.2, 0, 0).rectangle(-120, -120, 240, 240).fill()
        ctx.rgb(1, 0, 0).move_to(-80, 0).text("ArtNet Demo")
        ctx.restore()
        
        for led in range(0,12):
            if len(self.data) > (led*3)+2:
                tildagonos.leds[led+1] = (self.data[(led*3)], self.data[(led*3)+1], self.data[(led*3)+2])
            
        
__app_export__ = ArtNetApp