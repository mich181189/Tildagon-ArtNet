from . import artnet_codes

PORT = 0x1936

def get_opcode(msg):
    if len(msg) < 10:
        return None
    return msg[8] + (msg[9] << 8)

def _parse_addr(addr):
    out = [0,0,0,0]
    idx = 0
    scratch = ''
    for c in addr:
        if c == '.':
            out[idx] = int(scratch)
            idx += 1
            scratch = ''
        else:
            scratch += c
    out[idx] = int(scratch)
    return out
        

class PacketHeader:
    def __init__(self, opcode = 0, length = 0, *, data = None):
        if data is not None:
            self.buffer = bytearray(data)
        else:
            self.buffer =  bytearray(length)
            self.buffer[0] = 0x41 # A
            self.buffer[1] = 0x72 # r
            self.buffer[2] = 0x74 # t
            self.buffer[3] = 0x2d # -
            self.buffer[4] = 0x4e # N
            self.buffer[5] = 0x65 # e
            self.buffer[6] = 0x74 # t
            self.buffer[7] = 0x00
            
            self.buffer[8] = opcode & 0xff
            self.buffer[9] = (opcode & 0xff00) >> 8
        
    
    def validate_header(self):
        return self.buffer[0] == 0x41 and self.buffer[1] == 0x72 and self.buffer[2] == 0x74 and \
            self.buffer[3] == 0x2d and self.buffer[4] == 0x4e and self.buffer[5] == 0x65 and self.buffer[6] == 0x74 and self.buffer[7] == 0x00
    
    def get_opcode(self):
        return self.buffer[8] + (self.buffer[9] << 8)

class OpPoll(PacketHeader):
    FLAG_ENABLE_TARGETTED_MODE = (1 << 5)
    FLAG_ENABLE_VLC_TRANSMISSION = (1 << 4)
    FLAG_DIANGNOSTICS_ARE_UNICAST = (1 << 3)
    FLAG_SEND_DIAGNOSTICS = (1 << 2)
    FLAG_SEND_ARTPOLLREPLY_ON_CHANGE = (1 << 1)
    
    def __init__(self, opcode = 0, length = 0, *, data = None):
        super().__init__(opcode, length, data=data)
        assert super().get_opcode() == artnet_codes.OpPoll
        assert len(self.buffer) >= 14
    
    def prot_version_hi(self):
        return self.buffer[10]
    
    def prot_version_lo(self):
        return self.buffer[11]
    
    def flags(self):
        return self.buffer[12]

    def diag_priority(self):
        return self.buffer[13]
    
    def target_port_range(self):
        if len(self.buffer) < 18:
            return 0,0
        hi = (self.buffer[14] << 8) + self.buffer[15]
        lo = (self.buffer[16] << 8) + self.buffer[17]
        return hi, lo
    
    def esta_manufactuer_code(self):
        if len(self.buffer) < 20:
            return 0
        return (self.buffer[18] << 8) + self.buffer[19]
    
    def oem_code(self):
        if len(self.buffer) < 22:
            return 0
        return (self.buffer[20] << 8) + self.buffer[21]

class OpPollReply(PacketHeader):
    
    STATUS1_INDICATOR_UNKNOWN = 0 << 6
    STATUS1_INDICATOR_LOCATE_MODE = 1 << 6
    STATUS1_INDICATOR_MUTE_MODE = 2 << 6
    STATUS1_INDICATOR_NORMAL = 3 << 6
    
    STATUS1_PORT_ADDRESS_AUTHORITY_UNKNOWN = 0 << 4
    STATUS1_PORT_ADDRESS_AUTHORITY_FRONT_PANEL = 1 << 4
    STATUS1_PORT_ADDRESS_AUTHORITY_NETWORK_WEB = 2 << 4
    
    STATUS1_ROM_BOOT = 1 << 2
    STATUS1_RDM_CAPABLE = 1 << 1
    STATUS1_UBEA_PRESENT = 1 << 0
    
    TYPE_OUTPUT = 1 << 7
    TYPE_INPUT = 1 << 6
    
    def __init__(self, *, data = None):
        if data is None:
            super().__init__(artnet_codes.OpPollReply, 239)
        else:
            super().__init__(data=data)
        
        assert len(self.buffer) >= 207
    
    def set_address(self, address, port=PORT):
        a = _parse_addr(address)
        self.buffer[10] = a[0]
        self.buffer[11] = a[1]
        self.buffer[12] = a[2]
        self.buffer[13] = a[3]
        self.buffer[14] = port & 0xff
        self.buffer[15] = (port & 0xff00) >> 8
        
    
    def set_version(self, version):
        self.buffer[16] = (version & 0xff00) >> 8
        self.buffer[17] = version & 0xff
    
    def set_switches(self, netswitch, subswitch):
        self.buffer[18] = netswitch & 0x7f
        self.buffer[19] = subswitch & 0xf
        
    def set_oem_code(self, oemcode):
        self.buffer[20] = (oemcode & 0xff00) >> 8
        self.buffer[21] = oemcode & 0xff
    
    def set_ubea_version(self, ubeaver):
        self.buffer[22] = ubeaver
        
    def set_status1(self, status1):
        self.buffer[23] = status1
    
    def set_estamanufacturer(self, estacode):
        self.buffer[24] = (estacode & 0xff00) >> 8
        self.buffer[25] = estacode & 0xff
    
    def set_port_name(self, name):
        data = name.encode('ascii')
        cursor = 0
        for c in data:
            if cursor > 16:
                break
            self.buffer[cursor + 26] = c
            cursor += 1
    
    def set_node_name(self, name):
        data = name.encode('ascii')
        cursor = 0
        for c in data:
            if cursor > 63:
                break
            self.buffer[cursor + 44] = c
            cursor += 1
        
    def set_port_count(self, count):
        self.buffer[172] = 0x00 # This is always specified to be zero in ArtNet4
        self.buffer[173] = count & 0xff
    
    def set_port_type(self, port, type):
        self.buffer[174 + port] = type
    
    def set_good_input(self, port, val):
        self.buffer[178 + port] = val
    
    def set_good_output(self, port, val):
        self.buffer[182 + port] = val
    
    def set_input_switches(self, port, val):
        self.buffer[186 + port] = val & 0xf
    
    def set_output_switches(self, port, val):
        self.buffer[190 + port] = val & 0xf

class OpOutput(PacketHeader):
    
    def __init__(self, data = None):
        super().__init__(0, 0, data=data)
        assert super().get_opcode() == artnet_codes.OpOutput
        assert len(self.buffer) >= 20
    
    def sequence(self):
        return self.buffer[12]
    
    def physical_port(self):
        return self.buffer[13]
    
    def subuni(self):
        return self.buffer[14]
    
    def net(self):
        return self.buffer[15]
    
    def length(self):
        return (self.buffer[16] << 8) + self.buffer[17]
    
    def data(self):
        return self.buffer[18:]

class ArtNet:
    universe_handler = None
    send_handler = None
    last_artpoll = None
    last_artpoll_from = None
    
    port_name = "A Port"
    node_name = "My Awesome ArtNet Node"
    
    def __init__(self, ip_address, oem_code, esta_manufacturer):
        self.ip_address = ip_address
        self.oem_code = oem_code
        self.esta_manufacturer = esta_manufacturer
    
    def set_universe_handler(self, universe_handler):
        self.universe_handler = universe_handler
        
    def set_send_handler(self, handler):
        self.send_handler = handler
        
    def _send_data(self, to, data):
        if self.send_handler is not None:
            self.send_handler(to, data)
            
    def set_port_name(self, port_name):
        self.port_name = port_name
    
    def set_node_name(self, node_name):
        self.node_name = node_name
    
    def _send_universe(self, net, subuniverse, data):
        if self.universe_handler:
            self.universe_handler(net, subuniverse, data)
    
    def on_data(self, data, source):
        opcode = get_opcode(data)
        if opcode is None:
            return
        
        if opcode == artnet_codes.OpPoll:
            msg = OpPoll(data=data)
            if msg.validate_header():
                print("Got artnet poll")
                self.last_artpoll = msg
                self.last_artpoll_from = source
                self._send_artpollreply()
        elif opcode == artnet_codes.OpPollReply:
            # We have no real reason to handle this, at least for now
            pass
        elif opcode == artnet_codes.OpOutput:
            msg = OpOutput(data=data)
            if msg.validate_header():
                print("data sequence", msg.sequence())
                self._send_universe(msg.net(), msg.subuni(), msg.data())
        else:
            print("Unhandled OpCode", opcode)
    
    def _send_artpollreply(self):
        apr = OpPollReply()
        apr.set_address(self.ip_address)
        apr.set_estamanufacturer(self.esta_manufacturer)
        apr.set_oem_code(self.oem_code)
        apr.set_status1(OpPollReply.STATUS1_INDICATOR_NORMAL | OpPollReply.STATUS1_PORT_ADDRESS_AUTHORITY_UNKNOWN)
        apr.set_port_name(self.port_name)
        apr.set_node_name(self.node_name)
        
        # TODO: Use more variable setting of port details
        apr.set_port_count(1) 
        apr.set_port_type(0, OpPollReply.TYPE_OUTPUT)
        apr.set_good_output(0, 1 << 7) # Set to outputting
        apr.set_output_switches(0, 1)
        
        self._send_data(self.last_artpoll_from, apr.buffer)
        
    
    

    