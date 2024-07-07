import artnet
import artnet_codes

# Sample from DMXWorkshop
SAMPLE_ARTPOLL = b'Art-Net\x00\x00 \x00\x0e\x06\x00\x7f\xff\x00\x00Sy"i'

def test_generic_artnet_packet():
    pkt = artnet.PacketHeader(0xabcd, 42)
    assert len(pkt.buffer) == 42
    assert pkt.get_opcode() == 0xabcd
    assert pkt.validate_header()

def test_generic_artnet_packet_from_bytes():
    data = b'Art-Net\x00\xcd\xab'
    pkt = artnet.PacketHeader(data=data)
    assert len(pkt.buffer) == len(data)
    assert pkt.get_opcode() == 0xabcd
    assert pkt.validate_header()
    
    # Now the same, but with a bad header
    pkt = artnet.PacketHeader(data=b'a bad packet of junk is here')
    assert not pkt.validate_header()

def test_parse_artpoll():
    assert artnet.get_opcode(SAMPLE_ARTPOLL) == artnet_codes.OpPoll
    op = artnet.OpPoll(data=SAMPLE_ARTPOLL)
    assert op.get_opcode() == artnet_codes.OpPoll
    assert op.validate_header()
    assert op.prot_version_hi() == 0x00
    assert op.prot_version_lo() == 14
    assert not op.flags() & artnet.OpPoll.FLAG_ENABLE_TARGETTED_MODE
    assert not op.flags() & artnet.OpPoll.FLAG_ENABLE_VLC_TRANSMISSION
    assert not op.flags() & artnet.OpPoll.FLAG_DIANGNOSTICS_ARE_UNICAST
    assert op.flags() & artnet.OpPoll.FLAG_SEND_DIAGNOSTICS
    assert op.flags() & artnet.OpPoll.FLAG_SEND_ARTPOLLREPLY_ON_CHANGE
    assert op.diag_priority() == 0
    top, bottom = op.target_port_range()
    assert top == 32767
    assert bottom == 0
    assert op.esta_manufactuer_code() == 0x5379
    assert op.oem_code() == 0x2269

def test_parse_addr():
    assert [127,0,0,1] == artnet._parse_addr('127.0.0.1')
    assert [2,0,0,1] == artnet._parse_addr('2.0.0.1')
    assert [192, 168, 42, 255] == artnet._parse_addr('192.168.42.255')

def test_artpoll_reply():
    apr = artnet.OpPollReply()
    apr.set_address('192.168.42.200')
    assert apr.buffer[10] == 192
    assert apr.buffer[11] == 168
    assert apr.buffer[12] == 42
    assert apr.buffer[13] == 200
    assert apr.buffer[14] == 0x36
    assert apr.buffer[15] == 0x19
    
    
    apr.set_version(0xabcd)
    assert apr.buffer[16] == 0xab
    assert apr.buffer[17] == 0xcd
    
    apr.set_switches(0x12, 0x4)
    assert apr.buffer[18] == 0x12
    assert apr.buffer[19] == 4
    
    apr.set_oem_code(0x1234)
    assert apr.buffer[20] == 0x12
    assert apr.buffer[21] == 0x34
    
    apr.set_ubea_version(42)
    assert apr.buffer[22] == 42
    
    sample = artnet.OpPollReply.STATUS1_INDICATOR_NORMAL | artnet.OpPollReply.STATUS1_PORT_ADDRESS_AUTHORITY_NETWORK_WEB
    apr.set_status1(sample)
    assert apr.buffer[23] == sample
    
    apr.set_estamanufacturer(0x1234)
    assert apr.buffer[24] == 0x12
    assert apr.buffer[25] == 0x34
    
    apr.set_port_name("abc")
    assert apr.buffer[26] == ord('a')
    assert apr.buffer[27] == ord('b')
    assert apr.buffer[28] == ord('c')
    assert apr.buffer[29] == 0x00
    
    apr.set_node_name("def")
    assert apr.buffer[44] == ord('d')
    assert apr.buffer[45] == ord('e')
    assert apr.buffer[46] == ord('f')
    assert apr.buffer[47] == 0x00
    
    apr.set_port_count(1)
    assert apr.buffer[172] == 0
    assert apr.buffer[173] == 1
    
    
    