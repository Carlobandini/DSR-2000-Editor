'''
Copyright 2025 Carlo Bandini

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the 
documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this 
software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE 
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT 
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

import rtmidi
import sys
import os
import dearpygui.dearpygui as dpg
import filedialpy
import time
import json
import threading
import numpy as np

### Set path
application_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(application_path) 

#region ################################################# Set variables ########################################################
midiin = rtmidi.MidiIn()
midiout = rtmidi.MidiOut()
indevicelist = midiin.get_ports() # list of midi input devices
outdevicelist = midiout.get_ports()  # list of midi output devices
prefdir='files/Preferences/prefs'
outport = '' # selected midi out
inport = '' # selected midi in
datalist = []
drawing = 0
keypressed = None
VOICENUMBER = '00'
X0 = 820
X1,Y1 = 162,212
X2,Y2,Y3,Y4 = X1+260,Y1+56,Y1+112,Y1+168
X3 = 55
X5,Y5 = 675,215
XX = 73
X6,X7,X8,X9 = X5+(XX),X5+(XX*2),X5+(XX*3),X5+(XX*4)
Y6 = 230
Y7,Y8,Y9,Y10 = Y6+68, Y6+136, Y6+200, Y6+268
X10,X11 = X3+253, X3+510
p = 63
X12 = X0+p
X13 = X0+p+100
X14,X15,X16,X17 = X13+p,X13+2*p,X13+3*p,X13+4*p
Y11 = Y6-19
X18 = 58
scp,scp2 = 485, 206 # top screen position
joyx=1105
joyy = 667
start = 1
LASTMESSAGE = 1
displaylist = ['SPECTRUM','BRILLIANCE','ATTACK 1','ATTACK 2','DECAY','RELEASE','VOLUME','VIBRATO DEPTH','VIBRATO SPEED','PORTAMENTO TIME','PITCH BEND RANGE','TOUCH SENSITIVITY']    
for i in range(len(displaylist)):
    displaylist[i] = displaylist[i].rjust(18)      
displaysqsizes = [11,24,37,50,63,76,89,102]
copybuffer = []
#endregion

#region################################################# MOUSE CALLBACKS #######################################################
def keypresscallback(sender, app_data):
    global keypressed
    if app_data == 662:
        keypressed = 662

    if app_data == 515:
        movejoy('up')
    if app_data == 516:
        movejoy('down')
    if app_data == 513:
        movejoy('left')
    if app_data == 514:
        movejoy('right')

def keyreleasecallback():
    global keypressed
    keypressed = None
    dpg.configure_item('joystick',texture_tag= 'joy')

def mouseclickCallback():
    x, y = dpg.get_mouse_pos(local=False)
##### MOVE DISPLAY ARROW
    if joyy+49 > y > joyy+5: 
        y2 = (joyy+49) - y
        if (joyx+94) + y2 > x > (joyx+49) - y2:
            movejoy('up')
        
    if joyy+142 > y > joyy+98:
        y2 = y - (joyy+98)
        if (joyx+94) + y2 > x > (joyx+49) - y2:
            movejoy('down')
    
    if joyx+48 > x > joyx+4:
        x2 = (joyx+48) - x
        if (joyy+96) + x2 > y > (joyy+52) - x2:
            movejoy('left')
        
    if joyx+142 > x > joyx+98:
        x2 = x - (joyx+98)
        if (joyy+96) + x2 > y > (joyy+52) - x2:
            movejoy('right')

def mousereleaseCallback():
    dpg.configure_item('joystick',texture_tag= 'joy')
    if LASTMESSAGE !=1:
        sendmessage(LASTMESSAGE)

#endregion

#region################################################### APP ACTIONS #########################################################
def uploadbank():
    MESSAGE = 'F0' + ''.join(datalist) + 'F7'
    sendmessage(MESSAGE)
    drawcontrols()

def Numericpad(sender):
    if len (datalist) != 6915:
        time.sleep(.05)
        dpg.configure_item('novoice_error', show=True)
        return
    global VOICENUMBER
    value = sender[-1:]
    n1 = str(int(VOICENUMBER,16)).zfill(2)[0]
    n2 = str(int(VOICENUMBER,16)).zfill(2)[1]
    if value.isdigit() == True:
        N1 = n2
        N2 = value
        decvalue = int(N1+N2)
        if decvalue > 39:
            N1 = n1
            N2 = value
            decvalue = int(N1+N2)
    if value == '+':
        decvalue = int(n1+n2) +1
        if decvalue >39:
            decvalue = 39
    if value == '-':
        decvalue = int(n1+n2) -1
        if decvalue <0:
            decvalue = 0
        
    VOICENUMBER = (hex(decvalue)[2:].zfill(2)).upper() 
    program = int(VOICENUMBER,16)
    channel = 1
    status_byte = 0xC0 | (channel - 1) #Program change status byte is 0xC0
    dpg.configure_item('voicenumber',default_value = str(int(VOICENUMBER,16)).zfill(2))
    outport.send_message([status_byte, program])
    drawcontrols()

def MergeHexToDec(H1,H2 = None):
    if H2 == None:
        H2 = H1
        H1 = '00'
    value = str(H1[1])+str(H2[1])
    decvalue = int(value,16)
    return (decvalue)

def doinnerchecksum(sender):
    voices_bytes = bytes.fromhex(sender)
    len_bytes = len(voices_bytes)
    joining = voices_bytes[1:len_bytes]
    joined = []
    for i in range(0, len(joining), 2):
        joined.append((joining[i] << 4) + joining[i + 1])
    check_sum = sum(joined) % 256
    check_sum = ~check_sum & 0xFF
    if not isinstance(check_sum, list):
        check_sum = [check_sum]
    hex_list = []
    for nibble in check_sum:
        current = nibble if nibble >= 0 else nibble + 256
        hex_list.append('0'+hex(current >> 4)[2:])
        hex_list.append('0'+hex(current & 0xF)[2:])
    return (''.join(hex_list)).upper()

def doouterchecksum(sender):
    nibble_array = bytes.fromhex(sender)
    checksum = sum(nibble_array)
    checksum = (~checksum +1) & 0x7F # paso a 7 bits
    CHECKSUM = (hex(checksum)[2:].upper())
    if len(CHECKSUM) ==1:
        CHECKSUM = '0'+CHECKSUM
    return(CHECKSUM)

def sendmessage(MESSAGE):
    global start,end, LASTMESSAGE
    if len (datalist) != 6915:
        dpg.configure_item('novoice_error', show=True)
        return
    MESSAGEok = []
    MESSAGE1 = [MESSAGE[i:i+2] for i in range(0, len(MESSAGE), 2)]
    for i in MESSAGE1:
        MESSAGEok.append(int(i,16))
    # program change
    program = int(VOICENUMBER,16)
    channel = 1
    status_byte = 0xC0 | (channel - 1) #Program change status byte is 0xC0
    PROGCHANGE = [status_byte, program]
    end = time.time()
    LASTMESSAGE = MESSAGE
    if end - start >.05:
        outport.send_message(MESSAGEok)
        outport.send_message(PROGCHANGE)
        start = time.time()
        LASTMESSAGE = 1

def buildmessage(nibble1,value1, nibble2 = None, value2 = None, nibble3 = None, value3 = None):
    global datalist
    if len (datalist) != 6915:
        time.sleep(.05)
        dpg.configure_item('novoice_error', show=True)
        return
    HEADER1 = 'F043730D06' # header
    HEADER2 = '5000000A05' # voice header
    FOOTER = 'F7'
    # extract current voice
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    # Apply parameters change. Resto 5 porque en CURRENTVOICE no esta el header1
    CURRENTVOICE[nibble1-5] = value1
    if nibble2 != None:
        CURRENTVOICE[nibble2-5] = value2
    if nibble3 != None:
        CURRENTVOICE[nibble3-5] = value3
    # Write changes on datalist
    datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)] = CURRENTVOICE
    # isolate voice data
    VOICEDATA = ''.join(CURRENTVOICE[6:-3])
    # calculate checksums
    INNERCHECKSUM = doinnerchecksum(VOICENUMBER+VOICEDATA) # inner checksum
    OUTERCHECKSUM = doouterchecksum(VOICENUMBER+VOICEDATA+INNERCHECKSUM) # outer checksum
    # combine message
    MESSAGE = HEADER1+HEADER2+VOICENUMBER+VOICEDATA+INNERCHECKSUM+OUTERCHECKSUM+FOOTER
    return(MESSAGE)

def drawcontrols():
    global drawing
    drawing = 1
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    #region DISPLAY
    displayspectrum('read')
    displaybrilliance('read')
    displayattack1('read')
    displayattack2('read')
    displaydecay('read')
    displayrelease('read')
    displayvolume('read')
    displayvibratodepth('read')
    displayvibratospeed('read')
    displayportamento('read')
    displaypitch('read')
    displaytouchsens('read')
    displaychorus('read')
    displaymonopoly('read')
    displayoctave('read')
    #endregion

    #region COMMON
    # Algorithm
    nibble1 = 12
    for i in range(8):
        dpg.set_value('algorithm',i)
        value1 = Algorithm('algorithm')
        if value1 == CURRENTVOICE[nibble1-5]:
            break
        
    # Feedback
    nibble1,nibble2 = 11,12
    for i in range(8):
        dpg.set_value('feedback',i)
        value1,value2 = Feedback('feedback')
        if value1 == CURRENTVOICE[nibble1-5] and value2 == CURRENTVOICE[nibble2-5]:
            break
        
    # Pitch Envelope Level 1
    nibble1, nibble2 = 99,100
    value1 = CURRENTVOICE[nibble1-5]
    value2 = CURRENTVOICE[nibble2-5] 
    decvalue = int(str(value1[1]+value2[1]),16)
    if decvalue < 128:
        decvalue = decvalue + 127
    else:
        decvalue = decvalue - 128
    dpg.set_value('Pitchenvlevel1',decvalue)
    Pitchenvlevel1('Pitchenvlevel1')

    # Pitch Envelope Level 2
    nibble1, nibble2 = 103,104
    value1 = CURRENTVOICE[nibble1-5]
    value2 = CURRENTVOICE[nibble2-5] 
    decvalue = int(str(value1[1]+value2[1]),16)
    if decvalue < 128:
        decvalue = decvalue + 127
    else:
        decvalue = decvalue - 128
    dpg.set_value('Pitchenvlevel2',decvalue)
    Pitchenvlevel2('Pitchenvlevel2')

    # Pitch Envelope Level 3
    nibble1, nibble2 = 107,108
    value1 = CURRENTVOICE[nibble1-5]
    value2 = CURRENTVOICE[nibble2-5] 
    decvalue = int(str(value1[1]+value2[1]),16)
    if decvalue < 127:
        decvalue = decvalue + 128
    else:
        decvalue = decvalue - 128
    dpg.set_value('Pitchenvlevel3',decvalue)
    Pitchenvlevel3('Pitchenvlevel3')

    # Pitch Envelope rate 1
    nibble1, nibble2 = 101,102
    value1 = CURRENTVOICE[nibble1-5]
    value2 = CURRENTVOICE[nibble2-5] 
    decvalue = int(str(value1[1]+value2[1]),16)
    if decvalue > 127:
        decvalue = 255 - decvalue
    else:
        decvalue = decvalue
    
    decvalue = 127-decvalue
    dpg.set_value('Pitchenvrate1',decvalue)
    Pitchenvrate1('Pitchenvrate1')        

    # Pitch Envelope rate 2
    nibble1, nibble2 = 105,106
    value1 = CURRENTVOICE[nibble1-5]
    value2 = CURRENTVOICE[nibble2-5] 
    decvalue = int(str(value1[1]+value2[1]),16)
    if decvalue > 127:
        decvalue = 255 - decvalue
    else:
        decvalue = decvalue
    decvalue = 127-decvalue
        
    dpg.set_value('Pitchenvrate2',decvalue)
    Pitchenvrate2('Pitchenvrate2')   

    #endregion
    
    #region LFO
    # LFO Waveform
    nibble1 = 98
    value = int(CURRENTVOICE[nibble1-5],16)
    Lfowave('lfowave'+str(value+1))

    # LFO Frequency
    nibble1, nibble2 = 89,90
    decvalue = MergeHexToDec(CURRENTVOICE[nibble1-5], CURRENTVOICE[nibble2-5])
    dpg.set_value('lfofreq',decvalue)
    Lfofreq('lfofreq')

    # LFO Delay
    nibble1, nibble2 = 93,94
    decvalue = MergeHexToDec(CURRENTVOICE[nibble1-5], CURRENTVOICE[nibble2-5])
    dpg.set_value('lfodelay',decvalue)
    Lfodelay('lfodelay')

    # LFO Ramp
    nibble1, nibble2 = 95,96
    decvalue = MergeHexToDec(CURRENTVOICE[nibble1-5], CURRENTVOICE[nibble2-5])
    dpg.set_value('lforamp',decvalue)
    Lforamp('lforamp')

    # LFO to pitch
    nibble1, nibble2 = 85,86
    decvalue = MergeHexToDec(CURRENTVOICE[nibble1-5], CURRENTVOICE[nibble2-5])
    dpg.set_value('lfotopitch',decvalue)
    Lfotopitch('lfotopitch')

    # LFO to Pitch Sensitivity
    nibble1 = 91
    decvalue = MergeHexToDec(CURRENTVOICE[nibble1-5])
    dpg.set_value('lfopitchsens',decvalue)
    Lfopitchsens('lfopitchsens')

    # LFO to Amp
    nibble1, nibble2 = 87,88
    decvalue = MergeHexToDec(CURRENTVOICE[nibble1-5], CURRENTVOICE[nibble2-5])
    dpg.set_value('lfotoamp',decvalue)
    Lfotoamp('lfotoamp')

    # LFO to Amp Sensitivity
    nibble1 = 92
    decvalue = MergeHexToDec(CURRENTVOICE[nibble1-5])
    dpg.set_value('lfoampsens',decvalue)
    Lfoampsens('lfoampsens')
    #endregion

    #region OPERATORS
    # OP Waveform
    n = 0
    for nibble1 in (83,79,81,77):
        n=n+1
        decvalue = (MergeHexToDec(CURRENTVOICE[nibble1-5]))-7
        SelectWaveform('op'+str(n)+'_waveform'+str(decvalue))
    
    # OP Fixed Frequency
    n = 0
    for nibble1 in (35,31,33,29):
        n=n+1
        if CURRENTVOICE[nibble1-5] in ('02','03','06','07','0A','0B','0E','0F'): # si esta en uno de estos, SI que esta activo
            dpg.configure_item('op'+str(n)+'lightonfixedfreq',show = True)
            dpg.configure_item('op'+str(n)+'lightofffixedfreq',show = False)
        else:
            dpg.configure_item('op'+str(n)+'lightonfixedfreq',show = False)
            dpg.configure_item('op'+str(n)+'lightofffixedfreq',show = True)            

    # OP Amp Mod Enable
    n = 0
    for nibble1 in (43,39,41,37):
        n=n+1
        if CURRENTVOICE[nibble1-5] in ('08','09'): # si esta en uno de estos, SI que esta activo
            dpg.configure_item('op'+str(n)+'lightonampmodenable',show = True)
            dpg.configure_item('op'+str(n)+'lightoffampmodenable',show = False)
        else:
            dpg.configure_item('op'+str(n)+'lightonampmodenable',show = False)
            dpg.configure_item('op'+str(n)+'lightoffampmodenable',show = True)

    # OP Volume
    n = 0
    for nibble1 in (27,23,25,21):
        nibble2 = nibble1+1
        n=n+1
        decvalue = 63-MergeHexToDec(CURRENTVOICE[nibble1-5], CURRENTVOICE[nibble2-5])
        dpg.set_value('op'+str(n)+'Volume',decvalue)
        Volume('op'+str(n)+'Volume')

    # OP Freq
    n = 0
    for nibble1 in (20,16,18,14):
        n=n+1
        decvalue = MergeHexToDec(CURRENTVOICE[nibble1-5])
        dpg.set_value('op'+str(n)+'Freq',decvalue)
        Freq('op'+str(n)+'Freq')

    # OP Fixed Range OCT
    n = 0
    for nibble1 in (19,15,17,13):
        n=n+1
        decvalue = MergeHexToDec(CURRENTVOICE[nibble1-5])
        dpg.set_value('op'+str(n)+'Fxrg',decvalue)
        Fixedrangeoct('op'+str(n)+'Fxrg')
    #endregion

    #region KEYSCALING
    # OP Touchsens
    n = 0
    for nibble1 in (76,72,74,70):
        n=n+1
        decvalue = (MergeHexToDec(CURRENTVOICE[nibble1-5]))
        dpg.set_value('op'+str(n)+'Touchsens',decvalue)
        Touchsens('op'+str(n)+'Touchsens')

    # OP LowLevel
    n = 0
    for nibble1 in (68,64,66,62):
        n=n+1
        decvalue = (MergeHexToDec(CURRENTVOICE[nibble1-5]))
        dpg.set_value('op'+str(n)+'Lowlevel',decvalue)
        Lowlevel('op'+str(n)+'Lowlevel')

    # OP HighLevel
    n = 0
    for nibble1 in (67,63,65,61):
        n=n+1
        decvalue = (MergeHexToDec(CURRENTVOICE[nibble1-5]))
        dpg.set_value('op'+str(n)+'Highlevel',decvalue)
        Highlevel('op'+str(n)+'Highlevel')

    # OP KeyScalingRate
    n = 0
    
    for nibble1 in (35,31,33,29):
        n=n+1
        for i in range(4):
            dpg.set_value('op'+str(n)+'KSRate',i)
            value1 = KSRate('op'+str(n)+'KSRate')
            if value1 == CURRENTVOICE[nibble1-5]:
                break
    #endregion

    #region ENVELOPE
    # Attack
    n = 0
    for nibble1 in (35,31,33,29):
        n=n+1
        nibble2 = nibble1+1
        for i in range(32):
            dpg.set_value('op'+str(n)+'Envattack',i)
            value1,value2 = EnvAttack('op'+str(n)+'Envattack')
            if value1 == CURRENTVOICE[nibble1-5] and value2 == CURRENTVOICE[nibble2-5]:
                break

    # Decay1
    n = 0
    for nibble1 in (43,39,41,37):
        n=n+1
        nibble2 = nibble1+1
        for i in range(32):
            dpg.set_value('op'+str(n)+'Envdecay1',i)
            value1,value2 = Envdecay1('op'+str(n)+'Envdecay1')
            if value1 == CURRENTVOICE[nibble1-5] and value2 == CURRENTVOICE[nibble2-5]:
                break

    # Sustain
    n = 0
    for nibble1 in (59,55,57,53):
        n=n+1
        for i in range(16):
            dpg.set_value('op'+str(n)+'Envsustain',i)
            value1 = Envsustain('op'+str(n)+'Envsustain')
            if value1 == CURRENTVOICE[nibble1-5]:
                break

    # Decay2
    n = 0
    for nibble1 in (51,47,49,45):
        n=n+1
        nibble2 = nibble1+1
        for i in range(32):
            dpg.set_value('op'+str(n)+'Envdecay2',i)
            value1,value2 = Envdecay2('op'+str(n)+'Envdecay2')
            if value1 == CURRENTVOICE[nibble1-5] and value2 == CURRENTVOICE[nibble2-5]:
                break
            
    # Release
    n = 0
    for nibble1 in (60,56,58,54):
        n=n+1
        for i in range(16):
            dpg.set_value('op'+str(n)+'Envrelease',i)
            value1 = Envrelease('op'+str(n)+'Envrelease')
            if value1 == CURRENTVOICE[nibble1-5]:
                break

    #endregion
    drawing = 0
    return

def forcemidiselect(sender):
    if sender == 'firtsstartin':
        selectmidiin('i'+dpg.get_value(sender))
    if sender == 'firtsstartout':
        selectmidiout('o'+dpg.get_value(sender))
    
def clearmidierror():
    dpg.configure_item('midi_error', show=False)
    time.sleep(.05)
    dpg.configure_item('selectmidi', show=True)

def forcebulk():
    if inport == '' or outport == '':
        return
    dpg.configure_item('selectmidi', show = False)
    time.sleep(.05)
    dpg.configure_item('request_bank', show = True)
    time.sleep(.05)
    requestbank()
#endregion

#region#################################################### CONTROLS ###########################################################

#region########## DISPLAY

# move display arrow
def movejoy(dir):
    x,y = dpg.get_item_pos('arrow')
    if dir == 'down':
        dpg.configure_item('joystick',texture_tag= 'joydown')
        if x == scp+3:
            if y == 100:
                y = 127
            else:
                y = y + 9
            if y < 100:
                y = 100
            if y > 145.8:
                x = scp+124
                y = 46
        elif x == scp+124:
            y = y + 11
            if y > 68:
                x = scp+3
                y = 100
    
    if dir == 'up':
        dpg.configure_item('joystick',texture_tag= 'joyup')
        if x == scp+3:
            if y == 127:
                y =100
            else:
                y = y - 9
            if y < 100:
                x = scp+124
                y = 68    
        elif x == scp+124:
            y = y - 11
            if y < 46:
                x = scp+3
                y = 145.8

    if dir == 'left':
        dpg.configure_item('joystick',texture_tag= 'joyleft')

    if dir == 'right':
        dpg.configure_item('joystick',texture_tag= 'joyright')

    if dir in ('left','right'):
        if len (datalist) != 6915:
            time.sleep(.05)
            dpg.configure_item('novoice_error', show=True)
            return
        if x == scp+3:
            if y == 100:
                displayvolume(dir)
            if y == 127:
                displayportamento(dir)
            if y == 136:
                displaypitch(dir)
            if y == 145:
                displaytouchsens(dir)

        if x == scp+124:
            if y == 46:
                displaychorus(dir)
            if y == 57:
                displaymonopoly(dir)
            if y == 68:
                displayoctave(dir)
            
    dpg.configure_item('arrow',pos = (x,y))

def fillwithsquares(value,dir,pos):
    if dir == 'read':
        pass
          
    if dir == 'right':
        value = value + 1
        if value > 7:
            value = 7

    if dir == 'left':
        value = value - 1
        if value < 0:
            value = 0

    sqwidth = 11+(13*value)
    if pos in (0,1,2,3,4,5,7,8):
        dpg.configure_item('displaysquarespos'+str(pos), texture_tag= 'displaysquare'+str(value)+'B',width = sqwidth ) 
    else:
        dpg.configure_item('displaysquarespos'+str(pos), texture_tag= 'displaysquare'+str(value),width = sqwidth ) 
    return(value)

def displayspectrum(dir):
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 111
    value = int(CURRENTVOICE[nibble1-5],16)
    pos = 0
    value = fillwithsquares(value,dir,pos)

def displaybrilliance(dir):
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 118
    value = int(CURRENTVOICE[nibble1-5],16)
    pos = 1
    value = fillwithsquares(value,dir,pos)
    
def displayattack1(dir): 
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 128
    value = int(CURRENTVOICE[nibble1-5],16)
    pos = 2
    value = fillwithsquares(value,dir,pos)

def displayattack2(dir):
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 127
    value = int(CURRENTVOICE[nibble1-5],16)
    pos = 3
    value = fillwithsquares(value,dir,pos)

def displaydecay(dir):
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 132
    value = int(CURRENTVOICE[nibble1-5],16)
    pos = 4
    value = fillwithsquares(value,dir,pos)

def displayrelease(dir):
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 117
    value = int(CURRENTVOICE[nibble1-5],16)
    pos = 5
    value = fillwithsquares(value,dir,pos)

def displayvolume(dir): # EDITABLE
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 112 # display volume value (00 to 07)
    nibble2 = 113 # total attenuation nibble1 (see the nibble2list)
    nibble3 = 114 # tottal attenuation nibble2 (see the nibble3list)

    # set the display volume value
    value = int(CURRENTVOICE[nibble1-5],16)
    pos = 6
    value = fillwithsquares(value,dir,pos)
    value1 = (hex(value)[2:].zfill(2)).upper() 
    
    # set the attenuation
    nibble2list = ['01','01','01','01','00','00','00','00']
    nibble3list = ['0C','08','04','00','0C','08','04','00']
    value2 = nibble2list[value]
    value3 = nibble3list[value]
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2,nibble3,value3)
        sendmessage(MESSAGE)

def displayvibratodepth(dir):
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 158
    value = int(CURRENTVOICE[nibble1-5],16)
    pos = 7
    value = fillwithsquares(value,dir,pos)

def displayvibratospeed(dir):
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 157
    value = int(CURRENTVOICE[nibble1-5])
    pos = 8
    value = fillwithsquares(value,dir,pos)

def displayportamento(dir): # EDITABLE
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 160
    nibble2 = 161
    nibble3 = 162
    value = int(CURRENTVOICE[nibble1-5],16)
    pos = 9
    value = fillwithsquares(value,dir,pos)
    value1 = (hex(value)[2:].zfill(2)).upper() 
    value2list = ['0F','0B','06','05','03','02','01','00']
    value3list = ['0F','04','0E','00','07','03','04','02']  
    value2 = value2list[value]
    value3 = value3list[value]
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2,nibble3,value3)
        sendmessage(MESSAGE) 

def displaypitch(dir): # EDITABLE
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 159
    nibble2 = 164
    value = int(CURRENTVOICE[nibble1-5],16)
    pos = 10
    value = fillwithsquares(value,dir,pos)
    value1 = (hex(value)[2:].zfill(2)).upper() 
    value2list = ['00','01','02','03','04','05','07','0C']
    value2 = value2list[value]
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE) 

def displaytouchsens(dir): # EDITABLE
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 170
    value = int(CURRENTVOICE[nibble1-5],16)
    pos = 11
    value = fillwithsquares(value,dir,pos)
    value1 = (hex(value)[2:].zfill(2)).upper() 
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE) 

def displaychorus(dir): # EDITABLE
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 166
    value = int(CURRENTVOICE[nibble1-5],16)
    if dir == 'read':
        if value == 1:
            dpg.configure_item('displaychorusimg',texture_tag = 'choruson')
        else:
            dpg.configure_item('displaychorusimg',texture_tag = 'chorusoff')
        return

    if dir == 'right':
        dpg.configure_item('displaychorusimg',texture_tag = 'choruson')
        if value == 0:
            value = 1
    if dir == 'left':
        dpg.configure_item('displaychorusimg',texture_tag = 'chorusoff')
        if value == 1:
            value = 0
    value1 = (hex(value)[2:].zfill(2)).upper() 
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE) 

def displaymonopoly(dir): # EDITABLE
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 165
    value = int(CURRENTVOICE[nibble1-5],16)
    if dir == 'read':
        if value == 0:
            dpg.configure_item('displaymonopolyimg',texture_tag = 'poly')
        else:
            dpg.configure_item('displaymonopolyimg',texture_tag = 'mono')
        return
            
    if dir == 'right':
        dpg.configure_item('displaymonopolyimg',texture_tag = 'poly')
        if value == 1:
            value = 0
    if dir == 'left':
        dpg.configure_item('displaymonopolyimg',texture_tag = 'mono')
        if value == 0:
            value = 1
    value1 = (hex(value)[2:].zfill(2)).upper() 
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE) 

def displayoctave(dir): # EDITABLE
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 167
    nibble2 = 168
    value1 = int(CURRENTVOICE[nibble1-5],16)
    value2 = int(CURRENTVOICE[nibble2-5],16)
    if dir == 'read':
        if value2 == 12:
            dpg.configure_item('displayoctaveimg',texture_tag = 'OCTAVEH')
        if value2 == 0:
            dpg.configure_item('displayoctaveimg',texture_tag = 'OCTAVEM')
        if value2 == 4:
            dpg.configure_item('displayoctaveimg',texture_tag = 'OCTAVEL')
        return

    if dir == 'right':
        if value1 == 0 and value2 == 0: # if octave M
            # do coctave H
            dpg.configure_item('displayoctaveimg',texture_tag = 'OCTAVEH')
            value1 = 0
            value2 = 12

        if value1 == 15 and value2 == 4: # if ctave L
            # do octave M
            dpg.configure_item('displayoctaveimg',texture_tag = 'OCTAVEM')
            value1 = 0
            value2 = 0
        
    if dir == 'left':
        if value1 == 0 and value2 == 0: # if octave M
            # do coctave L
            dpg.configure_item('displayoctaveimg',texture_tag = 'OCTAVEL')
            value1 = 15
            value2 = 4

        if value1 == 0 and value2 == 12: # if octave H
            # do coctave M
            dpg.configure_item('displayoctaveimg',texture_tag = 'OCTAVEM')
            value1 = 0
            value2 = 0

    value1 = (hex(value1)[2:].zfill(2)).upper() 
    value2 = (hex(value2)[2:].zfill(2)).upper() 
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE) 
#endregion

#region########## COMMON

def Algorithm(sender):
    if len (datalist) != 6915:
        time.sleep(.05)
        dpg.configure_item('novoice_error', show=True)
        return
    value = dpg.get_value(sender)
    # Algorythm: nibble 12, Hex Values: (00 to 07 + Feedback value)
    dpg.configure_item('algorithmtt',default_value = '{:d}'.format(value+1))
    dpg.configure_item(item = 'algorithmHandle', pos = (X0+1, Y11 + 119 - value*((181-62)/7)))# 181: width slider, 62: width handler , 7 = maxvalue
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1 = 12
    # ---> Feedback: suma 8 * slider a los nibbles 11,12:
    # si nibbles 11,12 = 00,00:
    # feedback 1 = 00,08
    # feedback 2 = 01,00
    # feedback 3 = 01,08 
    # etc, hasta 03,08 (0 to 7 / 38H / 56 dec.) 
    # ---- entonces:
    # El nibble 11 lo ignoramos.
    # Algorythm solo puede sumar hasta 7, de modo que si el nibble 12 es mayor que 8 es que tiene 8 sumado por feedback:
    if int(CURRENTVOICE[nibble1-5],16) >= 8:
        decvalue = value + 8 # le mantengo los 8 sumados.
        dpg.configure_item(item = 'algorithmimg', texture_tag = 'algorithm'+str(decvalue-7))
    else:
        decvalue = value # dejo el valor del slider.
        dpg.configure_item(item = 'algorithmimg', texture_tag = 'algorithm'+str(decvalue+1))
 
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 
    value1 = hexvalue.zfill(2)
    if drawing == 1:
        return(value1)
    else:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)
    
def Feedback(sender):
    if len (datalist) != 6915:
        time.sleep(.05)
        dpg.configure_item('novoice_error', show=True)
        return
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    nibble1,nibble2 = 11,12
    # ALGORITHM: 1 to 7
    # ---> Feedback: suma 8 * slider a los nibbles 11,12:
    # si nibbles 11,12 = 00,00:
    # feedback 1 = 00,08
    # feedback 2 = 01,00
    # feedback 3 = 01,08 
    # etc, hasta 03,08 (0 to 7 / 38H / 56 dec.) 

    # valor para el fader
    valueforhandle = dpg.get_value(sender)
    # calulamos vaores nuevos.
    decvalue = dpg.get_value(sender) * 8
    
    dpg.configure_item(item = 'feedbacktt',default_value = '{:d}'.format(valueforhandle))
    dpg.configure_item(item = 'FeedbackHandle', pos = (X12+1, Y11 + 119 - valueforhandle*((181-62)/7),Y7+1))# 181: width slider, 62: width handler , 7 = maxvalue

    # Si el feedback anterior tenia sumado 8, lo restamos, si no, lo dejamos igual.
    if CURRENTVOICE[nibble2-5] in ['00','01','02','03','04','05','06','07']:
        currentdecvalue = int(CURRENTVOICE[nibble2-5],16)
        # sumamos nuestro nibble2 que solo pude ser 00 o 08
    if CURRENTVOICE[nibble2-5] in ['08','09','0A','0B','0C','0D','0E','0F']:
        currentdecvalue = int(CURRENTVOICE[nibble2-5],16)-8
    # aqui sumamos el valor anterior al nuevo, como algorithm no puede cambiar el nibble1, sacamos el nibble1 del valor de FEEDBACK actual.
    value = decvalue + currentdecvalue
    hexvalue = (hex(value)[2:].zfill(2)).upper() 
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)

    if drawing == 1:
        return(value1,value2)
    else:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)

def Pitchenvlevel1(sender):
    # Nibbles
    nibble1, nibble2 = 99,100
    if keypressed == 662:
        decvalue = 127
        dpg.configure_item(item = 'Pitchenvlevel1', default_value = 127)
    else:
        decvalue = dpg.get_value(sender)
    valueforhandle = decvalue
    if decvalue > 127:
        value = decvalue - 127
    else:
        value = decvalue + 128

    dpg.configure_item(item = 'Pitchenvlevel1Handle', pos = (X13+1, Y11 + 119 - valueforhandle*((181-62)/254),Y7+1))
    dpg.configure_item(item = 'Pitchenvlevel1tt',default_value = '{:d}'.format(decvalue-127))

    hexvalue = (hex(value)[2:].zfill(2)).upper()
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)
    
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)
        Pitchenvrate1('Pitchenvrate1',1)
        Pitchenvrate2('Pitchenvrate2',1)
    else:
        return(value1,value2)
    Drawpitchenvelope()

def Pitchenvrate1(sender, nodrawdisplay = None):
    # pitch env 1 rate: nibbles 101,102: 00 to 7F (00,00 to 07,0F) 0 to 127 dec
    nibble1, nibble2 = 101,102
    value = dpg.get_value(sender)
    dpg.configure_item(item = 'Pitchenvrate1Handle', pos = (X14+1,Y11 +119 - value*((181-62)/127)))# 181: width slider, 62: width handler , 127 = maxvalue
    if nodrawdisplay != 1:
        dpg.configure_item(item = 'Pitchenvrate1tt',default_value = '{:d}'.format(value))
    if dpg.get_value('Pitchenvlevel1') >= dpg.get_value('Pitchenvlevel2'):
        value = value + 128
    else:
        value = 128 - value
    hexvalue = (hex(value)[2:].zfill(2)).upper()
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)
    Drawpitchenvelope()

def Pitchenvlevel2(sender):
    # pitch env 1 ammount: nibbles 103,104: 00 to FF (00,00 to 0F,0F) 0 to 254 dec
    nibble1, nibble2 = 103,104
    if keypressed == 662:
        decvalue = 127
        dpg.configure_item(item = 'Pitchenvlevel2', default_value = 127)
    else:
        decvalue = dpg.get_value(sender)
    dpg.configure_item(item = 'Pitchenvlevel2Handle', pos = (X15+1, Y11 +119 - decvalue*((181-62)/254)))# 181: width slider, 62: width handler , 254 = maxvalue
    dpg.configure_item(item = 'Pitchenvlevel2tt',default_value = '{:d}'.format(decvalue-127))
    if decvalue >127:
        value = decvalue - 127
    else:
        value = decvalue + 128
    hexvalue = (hex(value)[2:].zfill(2)).upper()
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)
        Pitchenvrate1('Pitchenvrate1',1)
        Pitchenvrate2('Pitchenvrate2',1)
    Drawpitchenvelope()

def Pitchenvrate2(sender,nodrawdisplay = None):
    # pitch env 1 rate: nibbles 105,106: 00 to FF (00,00 to 0F,0F) 0 to 254 dec
    nibble1, nibble2 = 105,106
    value = dpg.get_value(sender)
    dpg.configure_item(item = 'Pitchenvrate2Handle', pos = (X16+1,Y11 +119 - value*((181-62)/127)))# 181: width slider, 62: width handler , 127 = maxvalue
    if nodrawdisplay != 1:
        dpg.configure_item(item = 'Pitchenvrate2tt',default_value = '{:d}'.format(value))
    if dpg.get_value('Pitchenvlevel2') >= dpg.get_value('Pitchenvlevel3'):
        value = value + 128
    else:
        value = 128 - value
    hexvalue = (hex(value)[2:].zfill(2)).upper()
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)
    Drawpitchenvelope()

def Pitchenvlevel3(sender):
    # pitch env 1 ammount: nibbles 107,108: 00 to FF (00,00 to 0F,0F) 0 to 254 dec
    nibble1, nibble2 = 107,108
    if keypressed == 662:
        decvalue = 127
        dpg.configure_item(item = 'Pitchenvlevel3', default_value = 127)
    else:
        decvalue = dpg.get_value(sender)
    dpg.configure_item(item = 'Pitchenvlevel3Handle', pos = (X17+1, Y11 +119 - decvalue*((181-62)/254)))# 181: width slider, 62: width handler , 254 = maxvalue
    dpg.configure_item(item = 'Pitchenvlevel3tt',default_value = '{:d}'.format(decvalue-127))
    if decvalue >127:
        value = decvalue - 127
    else:
        value = decvalue + 128
    hexvalue = (hex(value)[2:].zfill(2)).upper()
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)
        Pitchenvrate2('Pitchenvrate2',1)
    Drawpitchenvelope()

def Drawpitchenvelope():
    hprop = 1.052 # proporcion horizontal para llenar la pantallita
    vprop = 0.41 # proporcion vertical
    level1 = 255-dpg.get_value('Pitchenvlevel1') # 0 to 255
    rate1 = dpg.get_value('Pitchenvrate1') # 0 to 127
    level2 = 255-dpg.get_value('Pitchenvlevel2') # 0 to 255
    rate2 = dpg.get_value('Pitchenvrate2') # 0 to 127
    level3 = 255-dpg.get_value('Pitchenvlevel3') # 0 to 255
    level1 = 16+(level1*vprop)
    level2 = 16+(level2*vprop)
    level3 = 16+(level3*vprop)
    rate1 = 975+(rate1*hprop)
    rate2 = rate1+(rate2*hprop)
    dpg.configure_item('pitchenvline1',p1 = (975,level1))
    dpg.configure_item('pitchenvline1',p2 = (rate1,level2))
    dpg.configure_item('pitchenvline2',p1 = (rate1,level2))
    dpg.configure_item('pitchenvline2',p2 = (rate2,level3))  
    dpg.configure_item('pitchcircle0',center = (975,level1))
    dpg.configure_item('pitchcircle1',center = (rate1,level2))
    dpg.configure_item('pitchcircle2',center = (rate2,level3))

#endregion

#region########## LFO
def Lfowave(sender):
    # LFO Wave: nibble 98: 00 to 03
    decvalue = int(sender[-1:]) # waveform
    for i in range(1,5,1):
        if decvalue == i:
            dpg.configure_item('lightonlfowave'+str(i),show = True)
            dpg.configure_item('lightofflfowave'+str(i),show = False)
        else:
            dpg.configure_item('lightonlfowave'+str(i),show = False)
            dpg.configure_item('lightofflfowave'+str(i),show = True)
    
    nibble1 = 98
    value1 = (hex(decvalue-1)[2:].zfill(2)).upper() 
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def Lfofreq(sender):
    # LFO Freq: nibbles 89,90: 00 to FF (00,00 to 0F,0F) 0 to 255 dec
    nibble1, nibble2 = 89,90
    value = dpg.get_value(sender)
    dpg.configure_item(item = 'lfofreqtt',default_value = '{:d}'.format(value))
    hexvalue = (hex(value)[2:].zfill(2)).upper()
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)
    dpg.configure_item(item = 'lfofreqHandle', pos = (X3 + value*((181-62)/255),Y6+1))# 181: width slider, 62: width handler , 255 = maxvalue
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)
    
def Lfodelay(sender):
    # LFO Delay: nibbles 93,94: 00 to 7F (00,00 to 07,0F) 0 to 127 dec
    nibble1, nibble2 = 93,94
    value = dpg.get_value(sender)
    dpg.configure_item(item = 'lfodelaytt',default_value = '{:d}'.format(value))
    hexvalue = (hex(value)[2:].zfill(2)).upper()
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)
    dpg.configure_item(item = 'lfodelayHandle', pos = (X10 + value*((181-62)/127),Y6+1))# 181: width slider, 62: width handler , 127 = maxvalue
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)

def Lforamp(sender):
    # LFO Ramp: nibbles 95,96: 00 to 7F (00,00 to 07,0F) 0 to 127 dec
    nibble1, nibble2 = 95,96
    value = dpg.get_value(sender)
    dpg.configure_item(item = 'lforamptt',default_value = '{:d}'.format(value))
    hexvalue = (hex(value)[2:].zfill(2)).upper()
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)
    dpg.configure_item(item = 'lforampHandle', pos = (X11 + value*((181-62)/127),Y6+1))# 181: width slider, 62: width handler , 127 = maxvalue
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)

def Lfotopitch(sender):
    # LFO to Pitch: nibbles 85, 86: 00 to 7F (00,00 to 07,0F) 0 to 127 dec
    nibble1, nibble2 = 85,86
    value = dpg.get_value(sender)
    dpg.configure_item(item = 'lfotopitchtt',default_value = '{:d}'.format(value))
    hexvalue = (hex(value)[2:].zfill(2)).upper()
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)
    dpg.configure_item(item = 'lfotopitchHandle', pos = (X10 + value*((181-62)/127),Y7+1))# 181: width slider, 62: width handler , 127 = maxvalue
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)

def Lfopitchsens(sender):
    # LFO to Pitch Sensitivity: nibble 91: 00 to 07
    nibble1= 91
    value = dpg.get_value(sender)
    dpg.configure_item(item = 'lfopitchsenstt',default_value = '{:d}'.format(value))
    value1 = (hex(value)[2:].zfill(2)).upper()
    dpg.configure_item(item = 'lfopitchsensHandle', pos = (X11 + value*((181-62)/7),Y7+1))# 181: width slider, 62: width handler , 7 = maxvalue
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        
        sendmessage(MESSAGE)

def Lfotoamp(sender):
    # LFO to Amp: nibbles 87, 88: 00 to 7F (00,00 to 07,0F) 0 to 127 dec
    nibble1, nibble2 = 87,88
    value = dpg.get_value(sender)
    dpg.configure_item(item = 'lfotoamptt',default_value = '{:d}'.format(value))
    hexvalue = (hex(value)[2:].zfill(2)).upper()
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)
    dpg.configure_item(item = 'lfotoampHandle', pos = (X10 + value*((181-62)/127),Y8+1))# 181: width slider, 62: width handler , 127 = maxvalue
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)

def Lfoampsens(sender):
    # LFO to Amp Sensitivity: nibble 92: 00 to 03 
    nibble1= 92
    value = dpg.get_value(sender)
    dpg.configure_item(item = 'lfoampsenstt',default_value = '{:d}'.format(value))
    value1 = (hex(value)[2:].zfill(2)).upper()
    dpg.configure_item(item = 'lfoampsensHandle', pos = (X11 + value*((181-62)/3),Y8+1))# 181: width slider, 62: width handler , 7 = maxvalue
    MESSAGE = buildmessage(nibble1,value1)
    if drawing == 0:
        sendmessage(MESSAGE)
#endregion

#region########## OPERATORS

def SelectWaveform(sender):
    #OP1 Wave: nibble 83: 08 to 0F (8 to 15 dec)
    op = int(sender[2:3]) # operator
    decvalue = int(sender[-1:]) # waveform
    for i in range(1,9,1):
        if decvalue == i:
            dpg.configure_item('op'+str(op)+'lightonwave'+str(i),show = True)
            dpg.configure_item('op'+str(op)+'lightoffwave'+str(i),show = False)
        else:
            dpg.configure_item('op'+str(op)+'lightonwave'+str(i),show = False)
            dpg.configure_item('op'+str(op)+'lightoffwave'+str(i),show = True)
    if op == 1:
        nibble1 = 83
    if op == 2:
        nibble1 = 79
    if op == 3:
        nibble1 = 81
    if op == 4:
        nibble1 = 77

    value1 = (hex(7+decvalue)[2:].zfill(2)).upper() 
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def FixedFrequency(sender):
    if len (datalist) != 6915:
        time.sleep(.05)
        dpg.configure_item('novoice_error', show=True)
        return
    op = int(sender[2:3]) # operator
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    # OP1 Fixed Freq. off/on: "off" no hace nada, "on" suma 2 al nibble 35...
    # OP1 Env Attack: nibbles 35,36: 00 to 1F (00,00 to 01,0F) 0 to 31 dec
    # OP1 Key Scaling Rate: nibble 35: suma (4 * valor slider) al nibble 35 attack...

    if not dpg.is_item_visible('op'+str(op)+'lightonfixedfreq'):
        dpg.configure_item('op'+str(op)+'lightonfixedfreq',show = True)
        dpg.configure_item('op'+str(op)+'lightofffixedfreq',show = False)
        active = 1
    else:
        dpg.configure_item('op'+str(op)+'lightonfixedfreq',show = False)
        dpg.configure_item('op'+str(op)+'lightofffixedfreq',show = True)
        active = 0

    if op == 1:
        nibble1 = 35
    if op == 2:
        nibble1 = 31
    if op == 3:
        nibble1 = 33
    if op == 4:
        nibble1 = 29

    if active == 1:
        if CURRENTVOICE[nibble1-5] in ('00','01','04','05','08','09','0C','0D'): # si esta en uno de estos, no esta activo
            decvalue = int(CURRENTVOICE[nibble1-5],16)+2
            value1 = (hex(decvalue)[2:].zfill(2)).upper() 
        else:
            value1 = CURRENTVOICE[nibble1-5] # lo dejo como esta
    else:
        if CURRENTVOICE[nibble1-5] in ('02','03','06','07','0A','0B','0E','0F'):
            decvalue = int(CURRENTVOICE[nibble1-5],16)-2
            value1 = (hex(decvalue)[2:].zfill(2)).upper() 
        else:
            value1 = CURRENTVOICE[nibble1-5]
    if drawing == 1:
        return(value1)
    else:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def AmpModEnable(sender):
    if len (datalist) != 6915:
        time.sleep(.05)
        dpg.configure_item('novoice_error', show=True)
        return
    op = int(sender[2:3]) # operator
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    # OP1 Amp Mod Enable off/on: "off" no hace nada, "on" suma 8 al nibble 43...

    if not dpg.is_item_visible('op'+str(op)+'lightonampmodenable'):
        dpg.configure_item('op'+str(op)+'lightonampmodenable',show = True)
        dpg.configure_item('op'+str(op)+'lightoffampmodenable',show = False)
        active = 1
    else:
        dpg.configure_item('op'+str(op)+'lightonampmodenable',show = False)
        dpg.configure_item('op'+str(op)+'lightoffampmodenable',show = True)
        active = 0

    if op == 1:
        nibble1 = 43
    if op == 2:
        nibble1 = 39
    if op == 3:
        nibble1 = 41
    if op == 4:
        nibble1 = 37
        
    if active == 1:
        if CURRENTVOICE[nibble1-5] in ('00','01'): # si esta en uno de estos, no esta activo
            decvalue = int(CURRENTVOICE[nibble1-5],16)+8
            value1 = (hex(decvalue)[2:].zfill(2)).upper() 
        else:
            value1 = CURRENTVOICE[nibble1-5] # lo dejo como esta
    else:
        if CURRENTVOICE[nibble1-5] in ('08','09'):
            decvalue = int(CURRENTVOICE[nibble1-5],16)-8
            value1 = (hex(decvalue)[2:].zfill(2)).upper() 
        else:
            value1 = CURRENTVOICE[nibble1-5]
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def Volume(sender):
    # OP1 Volume: nibbles 27,28: 00 to 3F: (00,00 to 03,0F) 0 to 63 dec
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 27
    if op == 2:
        nibble1 = 23
    if op == 3:
        nibble1 = 25
    if op == 4:
        nibble1 = 21
    nibble2 = nibble1+1

    decvalue = dpg.get_value(sender)    
    dpg.configure_item(item = 'op'+str(op)+'Volumett',default_value = '{:d}'.format(decvalue))
    dpg.configure_item(item = 'op'+str(op)+'VolumeHandle', pos = (X18+1,Y1+119 - decvalue*((181-62)/63)))# 181: width slider, 62: width handler
    decvalue = 63-decvalue
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)

def Freq(sender):
    # OP1 Freq: nibble 20: 00 to 0F (0 to 15 dec)
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 20
    if op == 2:
        nibble1 = 16
    if op == 3:
        nibble1 = 18
    if op == 4:
        nibble1 = 14

    decvalue = dpg.get_value(sender)    
    dpg.configure_item(item = 'op'+str(op)+'Freqtt',default_value = '{:d}'.format(decvalue))
    dpg.configure_item(item = 'op'+str(op)+'FreqHandle', pos = (X1 + decvalue*((181-62)/15),Y3+1))# 181: width slider, 62: width handler
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 
    value1 = hexvalue.zfill(2)
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def Fixedrangeoct(sender):
    # OP1 Fixed Range Octave: nibble 19: 00 to 07
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 19
    if op == 2:
        nibble1 = 15
    if op == 3:
        nibble1 = 17
    if op == 4:
        nibble1 = 13

    decvalue = dpg.get_value(sender)   
    dpg.configure_item(item = 'op'+str(op)+'Fxrgtt',default_value = '{:d}'.format(decvalue)) 
    dpg.configure_item(item = 'op'+str(op)+'FxrgoctHandle', pos = (X1 + decvalue*((181-62)/7),Y4+1))# 181: width slider, 62: width handler
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 
    value1 = hexvalue.zfill(2)
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def Finetune(sender):
    # Nibbles: 84,80,82,78
    # Values: 0 TO 0C
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 84
    if op == 2:
        nibble1 = 80
    if op == 3:
        nibble1 = 82
    if op == 4:
        nibble1 = 78

    decvalue = dpg.get_value(sender)
    dpg.configure_item(item = 'op'+str(op)+'Finetunett',default_value = '{:d}'.format(decvalue))
    dpg.configure_item(item = 'op'+str(op)+'FinetuneHandle', pos = (X1 + decvalue*((181-62)/15),Y1+1))
    value1 = (hex(decvalue)[2:].zfill(2)).upper() 
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def Coarsetune(sender):
    # Nibbles 51,47,49,45
    # Valores 00,04,08,0C
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 51
    if op == 2:
        nibble1 = 47
    if op == 3:
        nibble1 = 49
    if op == 4:
        nibble1 = 45

    decvalue = dpg.get_value(sender)
    dpg.configure_item(item = 'op'+str(op)+'Coarsetunett',default_value = '{:d}'.format(decvalue))
    dpg.configure_item(item = 'op'+str(op)+'CoarsetuneHandle', pos = (X1 + decvalue*((181-62)/3),Y2+1))
    value1 = (hex(decvalue*4)[2:].zfill(2)).upper() 
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)
#endregion

#region########## KEY SCALING
def Touchsens(sender):
    # OP1 Key Scaling Touch Sens nibble 76: 00 to 07
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 76
    if op == 2:
        nibble1 = 72
    if op == 3:
        nibble1 = 74
    if op == 4:
        nibble1 = 70

    decvalue = dpg.get_value(sender)  
    dpg.configure_item(item = 'op'+str(op)+'Touchsenstt',default_value = '{:d}'.format(decvalue))  
    dpg.configure_item(item = 'op'+str(op)+'TouchsensHandle', pos = (X2 + decvalue*((181-62)/7),Y1+1))# 181: width slider, 62: width handler
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 
    value1 = hexvalue.zfill(2)
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def Lowlevel(sender):
    # OP1 Key Scaling Level (Low): nibble 68: 00 to 0F: 0 to 15 dec
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 68
    if op == 2:
        nibble1 = 64
    if op == 3:
        nibble1 = 66
    if op == 4:
        nibble1 = 62

    decvalue = dpg.get_value(sender)   
    dpg.configure_item(item = 'op'+str(op)+'Lowleveltt',default_value = '{:d}'.format(decvalue),)
    dpg.configure_item(item = 'op'+str(op)+'LowlevelHandle', pos = (X2 + decvalue*((181-62)/15),Y2+1))# 181: width slider, 62: width handler
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 
    value1 = hexvalue.zfill(2)
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def Highlevel(sender):
    # OP1 Key Scaling Level (High): nibble 67: 00 to 0F: 0 to 15 dec
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 67
    if op == 2:
        nibble1 = 63
    if op == 3:
        nibble1 = 65
    if op == 4:
        nibble1 = 61

    decvalue = dpg.get_value(sender) 
    dpg.configure_item(item = 'op'+str(op)+'Highleveltt',default_value = '{:d}'.format(decvalue))   
    dpg.configure_item(item = 'op'+str(op)+'HighlevelHandle', pos = (X2 + decvalue*((181-62)/15),Y3+1))# 181: width slider, 62: width handler
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 
    value1 = hexvalue.zfill(2)
    if drawing == 0:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def KSRate(sender):
    # OP1 Key Scaling Rate: nibble 35: suma (4 * valor slider) al nibble 35 attack...
    # si attack nibbles 35,36 = 00,00: nibble35 = 00-04-08-0C (+02 si fixed freq on: 02-06-0A-0E)
    # si attack nibbles 35,36 = 00,01: nibble35 = 00-04-08-0C (+02 si fixed freq on: 02-06-0A-0E)
    # si attack nibbles 35,36 = 01,00: nibble35 = 01-05-09-0D (+02 si fixed freq on: 03-07-0B-0F)
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 35
    if op == 2:
        nibble1 = 31
    if op == 3:
        nibble1 = 33
    if op == 4:
        nibble1 = 29

    decvalue = dpg.get_value(sender)
    dpg.configure_item(item = 'op'+str(op)+'KSRatett',default_value = '{:d}'.format(decvalue))
    dpg.configure_item(item = 'op'+str(op)+'KSRateHandle', pos = (X2 + decvalue*((181-62)/3),Y4+1))# 181: width slider, 62: width handler
    if decvalue == 0:
        if CURRENTVOICE[nibble1-5] in ('00','01','02','03'): # si esta en uno de estos, no esta activo
            value = int(CURRENTVOICE[nibble1-5],16)
        if CURRENTVOICE[nibble1-5] in ('04','05','06','07'):
            value = int(CURRENTVOICE[nibble1-5],16)-4
        if CURRENTVOICE[nibble1-5] in ('08','09','0A','0B'):
            value = int(CURRENTVOICE[nibble1-5],16)-8
        if CURRENTVOICE[nibble1-5] in ('0C','0D','0E','0F'):
            value = int(CURRENTVOICE[nibble1-5],16)-16   
    if decvalue == 1:
        if CURRENTVOICE[nibble1-5] in ('00','01','02','03'): # si esta en uno de estos, no esta activo
            value = int(CURRENTVOICE[nibble1-5],16)+4
        if CURRENTVOICE[nibble1-5] in ('04','05','06','07'):
            value = int(CURRENTVOICE[nibble1-5],16)
        if CURRENTVOICE[nibble1-5] in ('08','09','0A','0B'):
            value = int(CURRENTVOICE[nibble1-5],16)-4
        if CURRENTVOICE[nibble1-5] in ('0C','0D','0E','0F'):
            value = int(CURRENTVOICE[nibble1-5],16)-8       
    if decvalue == 2:
        if CURRENTVOICE[nibble1-5] in ('00','01','02','03'): # si esta en uno de estos, no esta activo
            value = int(CURRENTVOICE[nibble1-5],16)+8
        if CURRENTVOICE[nibble1-5] in ('04','05','06','07'):
            value = int(CURRENTVOICE[nibble1-5],16)+4
        if CURRENTVOICE[nibble1-5] in ('08','09','0A','0B'):
            value = int(CURRENTVOICE[nibble1-5],16)
        if CURRENTVOICE[nibble1-5] in ('0C','0D','0E','0F'):
            value = int(CURRENTVOICE[nibble1-5],16)-4
    if decvalue == 3:
        if CURRENTVOICE[nibble1-5] in ('00','01','02','03'): # si esta en uno de estos, no esta activo
            value = int(CURRENTVOICE[nibble1-5],16)+16
        if CURRENTVOICE[nibble1-5] in ('04','05','06','07'):
            value = int(CURRENTVOICE[nibble1-5],16)+8
        if CURRENTVOICE[nibble1-5] in ('08','09','0A','0B'):
            value = int(CURRENTVOICE[nibble1-5],16)+4
        if CURRENTVOICE[nibble1-5] in ('0C','0D','0E','0F'):
            value = int(CURRENTVOICE[nibble1-5],16)

    value1 = (hex(value)[2:].zfill(2)).upper()
    if drawing == 1:
        return(value1)
    else:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)
#endregion

#region########## ENVELOPE (Es identica a la del tx81z)
def EnvAttack(sender): # Tiempo de ataque
    # OP1 Env Attack: nibbles 35,36: 00 to 1F (00,00 to 01,0F) 0 to 31 dec
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 35
    if op == 2:
        nibble1 = 31
    if op == 3:
        nibble1 = 33
    if op == 4:
        nibble1 = 29
    nibble2 = nibble1+1

    decvalue = dpg.get_value(sender)  
    dpg.configure_item(item = 'op'+str(op)+'EnvattackHandle', pos = (X5+1,Y5+119 - decvalue*((181-62)/31)))# 181: width slider, 62: width handler
    decvalue = 31-decvalue
    dpg.configure_item(item = 'op'+str(op)+'Envattacktt',default_value = '{:d}'.format(decvalue))  
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 

    if CURRENTVOICE[nibble1-5] in ('00','04','08','0C','02','06','0A','0E'):
        if hexvalue[0].zfill(2) == '01':
            value = int(CURRENTVOICE[nibble1-5],16) + 1
        if hexvalue[0].zfill(2) == '00':
            value = int(CURRENTVOICE[nibble1-5],16)
    else:
        if hexvalue[0].zfill(2) == '01':
            value = int(CURRENTVOICE[nibble1-5],16)
        if hexvalue[0].zfill(2) == '00':
            value = int(CURRENTVOICE[nibble1-5],16) -1
            
    value1 = (hex(value)[2:].zfill(2)).upper() 
    value2 = hexvalue[1].zfill(2)

    drawenvelope(op)
    if drawing == 1:
        return(value1,value2)
    else:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)

def Envdecay1(sender): # bajada hasta cero (tiempo), pero corta cuando se encuentra con el nivel de sustain
    # OP1 Env Decay 1: nibbles 43,44: 00 to 1F (00,00 to 01,1F) 0 to 31 dec
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 43
    if op == 2:
        nibble1 = 39
    if op == 3:
        nibble1 = 41
    if op == 4:
        nibble1 = 37
    nibble2 = nibble1+1

    decvalue = dpg.get_value(sender)
    dpg.configure_item(item = 'op'+str(op)+'Envdecay1Handle', pos = (X6+1,Y5+119 - decvalue*((181-62)/31)))
    decvalue = 31-decvalue
    dpg.configure_item(item = 'op'+str(op)+'Envdecay1tt',default_value = '{:d}'.format(decvalue))  
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 
    
    if CURRENTVOICE[nibble1-5] in ('00','08'):
        if hexvalue[0].zfill(2) == '01':
            value = int(CURRENTVOICE[nibble1-5],16) + 1
        if hexvalue[0].zfill(2) == '00':
            value = int(CURRENTVOICE[nibble1-5],16)
    else:
        if hexvalue[0].zfill(2) == '01':
            value = int(CURRENTVOICE[nibble1-5],16)
        if hexvalue[0].zfill(2) == '00':
            value = int(CURRENTVOICE[nibble1-5],16) -1
        
    value1 = (hex(value)[2:].zfill(2)).upper()
    value2 = hexvalue[1].zfill(2)

    drawenvelope(op)
    if drawing == 1:
        return(value1,value2)
    else:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)

def Envsustain(sender): # Volumen, en cuanto llega a este punto, decay1 deja de actuar, y empieza a actuar decay2 (si esta muy alto, se alcanza enseguida, puesto que decay1 empieza arriba del todo)
    # OP1 Env Sustain: nibble 59: 00 to 0F: 0 to 15 dec 
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 59
    if op == 2:
        nibble1 = 55
    if op == 3:
        nibble1 = 57
    if op == 4:
        nibble1 = 53

    decvalue = dpg.get_value(sender)    
    dpg.configure_item(item = 'op'+str(op)+'Envsustaintt',default_value = '{:d}'.format(decvalue))  
    dpg.configure_item(item = 'op'+str(op)+'EnvsustainHandle', pos = (X7+1,Y5+119 - decvalue*((181-62)/15)))
    decvalue = 15-decvalue
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 
    value1 = hexvalue.zfill(2)

    drawenvelope(op)
    if drawing == 1:
        return(value1)
    else:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def Envdecay2(sender): # Tiempo desde sustain hasta cero, a menos que se suelte la tecla antes.
    # OP1 Env Decay 2: nibbles 51,52: 00 to 1F (00,00 to 01,1F) 0 to 31 dec
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 51
    if op == 2:
        nibble1 = 47
    if op == 3:
        nibble1 = 49
    if op == 4:
        nibble1 = 45
    nibble2 = nibble1+1

    decvalue = dpg.get_value(sender)    
    dpg.configure_item(item = 'op'+str(op)+'Envdecay2Handle', pos = (X8+1,Y5+119 - decvalue*((181-62)/31)))
    decvalue = 31-decvalue
    dpg.configure_item(item = 'op'+str(op)+'Envdecay2tt',default_value = '{:d}'.format(decvalue))  
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 
    value1 = hexvalue[0].zfill(2)
    value2 = hexvalue[1].zfill(2)

    drawenvelope(op)
    if drawing == 1:
        return(value1,value2)
    else:
        MESSAGE = buildmessage(nibble1,value1,nibble2,value2)
        sendmessage(MESSAGE)

def Envrelease(sender): # Tiempo desde que se suelta la tecla
    # OP1 Env Release: nibble 60: 00 to 0F: 0 to 15 dec
    op = int(sender[2:3]) # operator
    if op == 1:
        nibble1 = 60
    if op == 2:
        nibble1 = 56
    if op == 3:
        nibble1 = 58
    if op == 4:
        nibble1 = 54

    decvalue = dpg.get_value(sender)    

    dpg.configure_item(item = 'op'+str(op)+'EnvreleaseHandle', pos = (X9+1,Y5+119 - decvalue*((181-62)/15)))
    decvalue = 16-decvalue # no quiero que de cero
    dpg.configure_item(item = 'op'+str(op)+'Envreleasett',default_value = '{:d}'.format(decvalue))  
    if decvalue == 16:
        decvalue = 15
    hexvalue = (hex(decvalue)[2:].zfill(2)).upper() 
    value1 = hexvalue.zfill(2)

    drawenvelope(op)
    if drawing == 1:
        return(value1)
    else:
        MESSAGE = buildmessage(nibble1,value1)
        sendmessage(MESSAGE)

def drawenvelope(op):
    ini = (X5-17) # punto de inicio desde attack
    hprop = 2.28 # proporcion horizontal para llenar la pantallita
    vprop = 3.09677 # proporcion vertical
    attack = dpg.get_value('op'+str(op)+'Envattack') # 0 to 31
    decay1 = dpg.get_value('op'+str(op)+'Envdecay1') # 0 to 31
    sustain = dpg.get_value('op'+str(op)+'Envsustain')*2.06667 # 0 to 15, igualo
    decay2 = dpg.get_value('op'+str(op)+'Envdecay2') # 0 to 31
    release = dpg.get_value('op'+str(op)+'Envrelease')*2.06667 # 0 to 15, igualo

    # ajusto a curva exponencial de 3
    attack = (attack**3)*1.55 # el 1.55 es un poquito mas que pongo para llegar a la proporcion estirando solo ataque y release
    attack = attack/1986 #--> max. largo: 15
    decay1 = decay1**3 
    decay1 = decay1/633.851 #--> max. largo: 47
    sustain = sustain**3
    sustain = sustain/961#--> max. largo: 31
    decay2 = decay2**3 
    decay2 = decay2/633.851 #--> max. largo: 47
    release = (release**3)*1.55
    release = release/1986 #--> max. largo: 15

    #### saco todos los puntos de cada linea
    # attack
    attack_x = ini+(attack*hprop)

    # decay1
    decay_x1 = ini+(attack*hprop)+(decay1*hprop)
    if decay1 >= 47: # si decay1 esta arriba del todo, nunca se detiene
        decay_y = 44
        if sustain <31: # si sustain no esta arriba del todo, el valor de sustain no afecta a decay1
            decay_x = decay_x1
        else:
            decay_x = decay_x1-((sustain*hprop)*((decay1)/31))
    
    else:
        decay_y = 140-(sustain*vprop)
        decay_x = decay_x1-((sustain*hprop)*((decay1)/31))

    if decay_x < attack_x: # decay_x nunca puede estar detras de attack_x
        decay_x = attack_x

    # decay2
    decay2_x = decay_x+(decay2*hprop)
    if decay2 >= 47:# si decay2 esta arriba del todo, nunca se detiene, si no, llega siempre hasta abajo.
        decay2_y = decay_y
    else:
        decay2_y = 140

    # release
    release_x = decay2_x + release*hprop

    # dibujamos
    dpg.configure_item('op'+str(op)+'envattackline',p2 = (attack_x,44))
    dpg.configure_item('op'+str(op)+'envdecay1line',p1 = (attack_x,44), p2 = (decay_x,decay_y))
    dpg.configure_item('op'+str(op)+'envdecay2line',p1 = (decay_x,decay_y), p2 = (decay2_x,decay2_y))
    for n in range(44,140,6): # linea discontinua
        dpg.configure_item('op'+str(op)+'envkeyreleaseline'+str(n),p1 = (decay2_x,n), p2 = (decay2_x,n+3))
    dpg.configure_item('op'+str(op)+'envreleaseline',p1 = (decay2_x,decay2_y), p2 = (release_x,140))

    circlelist = [((X5-17),140),(attack_x,44),(decay_x,decay_y),(decay2_x,decay2_y),(release_x,140)]
    # circulos
    for n in range(5):
        dpg.configure_item('op'+str(op)+'circle'+str(n),center = circlelist[n])
#endregion
#endregion

#region################################################### MENU ACTIONS #########################################################
########### FILE
def loadbank():
    global datalist
    # update midi prefs
    checkmidiprefs()
    # LOAD DATALIST
    file=filedialpy.openFile()
    if file == '':
        return
    f = open(file, 'r')
    try:
        datalist1 = json.load(f)
    except:
        dpg.configure_item('data_error', show=True)
        return
    f.close()
    if len(datalist1) == 6915:
        datalist = datalist1
        uploadbank()

def loadvoice():
    global datalist
    # update midi prefs
    checkmidiprefs()
    # LOAD DATALIST
    file=filedialpy.openFile()
    if file == '':
        return
    f = open(file, 'r')
    try:
        CURRENTVOICE1 = json.load(f)
    except:
        dpg.configure_item('data_error', show=True)
        return
    f.close()

    if len(CURRENTVOICE1) != 171:
        dpg.configure_item('data_error', show=True)
        return
    
    CURRENTVOICE = CURRENTVOICE1
    CURRENTVOICE[5] = VOICENUMBER
    HEADER1 = 'F043730D06' # header
    HEADER2 = '5000000A05' # voice header
    FOOTER = 'F7'
    VOICEDATA = ''.join(CURRENTVOICE[6:-3])
    # calculate checksums
    INNERCHECKSUM = doinnerchecksum(VOICENUMBER+VOICEDATA) # inner checksum
    OUTERCHECKSUM = doouterchecksum(VOICENUMBER+VOICEDATA+INNERCHECKSUM) # outer checksum
    # combine message
    MESSAGE = HEADER1+HEADER2+VOICENUMBER+VOICEDATA+INNERCHECKSUM+OUTERCHECKSUM+FOOTER
    sendmessage(MESSAGE)
    # write datalist
    datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)] = CURRENTVOICE
    # draw controls
    drawcontrols()

def savebank():
    file = filedialpy.saveFile(title="Save all user presets")
    if file == '':
        return
    file = file
    f = open(file, 'w')
    json.dump(datalist, f)
    f.close()

def savevoice():
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    file = filedialpy.saveFile(title="Save current voice")
    if file == '':
        return
    file = file
    f = open(file, 'w')
    json.dump(CURRENTVOICE, f)
    f.close()

def exitprogram():
    try:
        inport.close()
    except:
        pass
    try:
        outport.close()
    except:
        pass    
    os._exit(0)

########### EDIT
def copyoperator():
    global copybuffer
    for i in range(1,5,1):
        if dpg.get_value('op'+str(i)+'_tab'):
            op = i
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    if op == 1:
        nibblelist = [83,35,43,44,27,28,20,19,84,51,52,76,68,67,35,36,59,60]
    if op == 2:
        nibblelist = [79,31,39,40,23,24,16,15,80,47,48,72,64,63,31,32,55,56]
    if op == 3:
        nibblelist = [81,33,41,42,25,26,18,17,82,49,50,74,66,65,33,34,57,58]
    if op == 4:
        nibblelist = [77,29,37,38,21,22,14,13,78,45,46,70,62,61,29,30,53,54]
    
    copybuffer = []
    for i in range(len(nibblelist)):
        copybuffer.append(CURRENTVOICE[nibblelist[i]-5])

def pasteoperator():
    for i in range(1,5,1):
        if dpg.get_value('op'+str(i)+'_tab'):
            op = i
    CURRENTVOICE = (datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)])
    if op == 1:
        nibblelist = [83,35,43,44,27,28,20,19,84,51,52,76,68,67,35,36,59,60]
    if op == 2:
        nibblelist = [79,31,39,40,23,24,16,15,80,47,48,72,64,63,31,32,55,56]
    if op == 3:
        nibblelist = [81,33,41,42,25,26,18,17,82,49,50,74,66,65,33,34,57,58]
    if op == 4:
        nibblelist = [77,29,37,38,21,22,14,13,78,45,46,70,62,61,29,30,53,54]

    for i in range(len(nibblelist)):
        CURRENTVOICE[nibblelist[i]-5] = copybuffer[i]
    
    # write datalist
    datalist[4+(int(VOICENUMBER,16)*171):175+(int(VOICENUMBER,16)*171)] = CURRENTVOICE

    HEADER1 = 'F043730D06' # header
    HEADER2 = '5000000A05' # voice header
    FOOTER = 'F7'
    VOICEDATA = ''.join(CURRENTVOICE[6:-3])
    # calculate checksums
    INNERCHECKSUM = doinnerchecksum(VOICENUMBER+VOICEDATA) # inner checksum
    OUTERCHECKSUM = doouterchecksum(VOICENUMBER+VOICEDATA+INNERCHECKSUM) # outer checksum
    # combine message
    MESSAGE = HEADER1+HEADER2+VOICENUMBER+VOICEDATA+INNERCHECKSUM+OUTERCHECKSUM+FOOTER
    sendmessage(MESSAGE)
    drawcontrols()
    
########### VOICE  
def requestbank():
    global stop, thread
    if inport == '' or outport == '':
        dpg.configure_item('midi_error', show=True)
        return
    dpg.configure_item('request_bank', show=True)

    def foundmessage(msg):
        global datalist
        datalist = msg[1:-1]
        dpg.configure_item('request_bank', show=False)
        time.sleep(.1)
        drawcontrols()

    def read():
        voicedata = []
        # Request voice
        while True:  # empiezo a leer
            msg = inport.get_message()
            if msg != None:
                # descarto mensajes que no sean bulk
                ## en Windows lee el mensaje separado en bloques de 1024k y el ultimo es de 773k, en MAC lee un bloque de 6917k.
                if len(msg[0]) in (6917,1024,773): 
                    # convertimos a hex
                    for i in msg[0]:
                        nibble = hex(i)[2:].zfill(2).upper()
                        # metemos en la variable
                        voicedata.append(nibble)
                    try:
                        # si el bloque esta completo, pasamos el mensaje a foundmessage.
                        if len(voicedata) == 6917:
                            foundmessage(voicedata)
                    except:
                        pass
            if stop:
                break
            
    stop = False
    thread = threading.Thread(target=read)
    thread.start()

def cancelrequest():
    global stop
    stop = True
    try:
        thread.join()
    except:
        pass
    dpg.configure_item('request_bank', show=False) 
    if inport == '' or outport == '':
        dpg.configure_item('midi_error', show=True)

########### MIDI 
def selectmidiin(sender):
    global inport
    try:
        inport.close()
    except:
        pass
    for i in indevicelist:
        dpg.set_item_label('i'+i, i)
    for i in indevicelist:
        if i == sender[1:]:
            dpg.set_item_label(sender, '*** ' + i + ' ***')
            midiin.close_port()
            inport =  midiin.open_port(indevicelist.index(i))
            inport.ignore_types(sysex=False)
            break
    f = open(prefdir, 'r')
    data = f.readlines()
    f = open(prefdir, 'w')
    data[0] = i+'\n'
    f.writelines(data)
    f.close()
    
def selectmidiout(sender):
    global outport
    try:
        outport.close()
    except:
        pass
    for i in outdevicelist:
        dpg.set_item_label('o'+i, i)
    for i in outdevicelist:
        if i == sender[1:]:
            dpg.set_item_label(sender, '*** ' + i + ' ***')
            midiout.close_port()
            outport =  midiout.open_port(outdevicelist.index(i))
            break
    f = open(prefdir, 'r')
    data = f.readlines()
    f = open(prefdir, 'w')
    data[1] = i+'\n'
    f.writelines(data)
    f.close()

def resetmidiconfig():
    global indevicelist, outdevicelist
    # borro menus
    for i in indevicelist:
        dpg.delete_item('i'+i)
    for i in outdevicelist:
        dpg.delete_item('o'+i)

    # creo nueva lista
    indevicelist = midiin.get_ports()
    outdevicelist = midiout.get_ports()

    #Creo menus de nuevo
    for i in indevicelist:
        dpg.add_menu_item(tag = 'i'+i, label=i , callback= selectmidiin, parent = 'midi_in_menu')
    for i in outdevicelist:
        dpg.add_menu_item(tag = 'o'+i, label=i , callback= selectmidiout, parent = 'midi_out_menu')

def resetmididevice():
    try:
        # Leo el interface de nuevo, por si se ha encendido el sinte despues de seleccionar el midi.
        checkmidiprefs()
    except:
        # Si no lo detecta, reseteo la config midi.
        dpg.configure_item('prefsio_error', show=True)
        resetmidiconfig()
#endregion

#region################################################ CREATE INTERFACE #######################################################
dpg.create_context()
dpg.create_viewport(title='DSR-2000 Editor',x_pos = (150), width=1300, height=840, disable_close = True, resizable = False)
dpg.set_exit_callback(exitprogram)
#endregion

#region################################################## LOAD IMAGES ##########################################################
for i in range(1,9,1):
    width, height, channels, data = dpg.load_image('files/Images/W'+str(i)+'.png')
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=77, height=31, default_value=data, tag='wave'+str(i))

imagelist = ['button','lighton','lightoff','logo','blackpoint','handle','handlevert','fader4','fader8','fader16','fader64','greypoint2','fader8vert']
imagelist.extend(['greypoint3','buttonsmall','whitepoint','displayarrow','fader0', 'fader0vert','fader64vert','fader16vert','screen','mono','poly'])
imagelist.extend(['choruson','chorusoff','greypoint','OCTAVEL','OCTAVEM','OCTAVEH','joy','joyup','joydown','joyleft','joyright','SHADOW'])
for i in range(8):
    imagelist.extend(['displaysquare'+str(i)])
    imagelist.extend(['displaysquare'+str(i)+'B'])

for i in range(1,5,1):
    imagelist.append('LFOW'+str(i))
for i in range(1,9,1):
    imagelist.append('algorithm'+str(i))
for i in imagelist:
    width, height, channels, data = dpg.load_image('files/Images/'+i+'.png')
    with dpg.texture_registry(show=False):
        dpg.add_static_texture(width=width, height=height, default_value=data, tag=i)   
#endregion

######################################################### MAIN WINDOW ##########################################################
with dpg.window(tag='Primary Window', on_close = exitprogram):   
    #region MENU BAR    
    with dpg.menu_bar():
        with dpg.menu(label='File', tag = 'file'):
            dpg.add_menu_item(label = 'Load voice', tag = 'loadvoice', callback= loadvoice)
            dpg.add_menu_item(label = 'Load bank', tag = 'loadbank', callback= loadbank)
            dpg.add_menu_item(label = 'Save voice', tag = 'savevoice', callback= savevoice)
            dpg.add_menu_item(label = 'Save bank', tag = 'savebank', callback= savebank)
            dpg.add_menu_item(label = 'Quit', tag='quit',callback= exitprogram)

        with dpg.menu(label='Edit', tag = 'edit'):
            dpg.add_menu_item(label = 'Copy operator', tag = 'copyoperator', callback= copyoperator)
            dpg.add_menu_item(label = 'Paste operator', tag = 'pasteoperator', callback= pasteoperator)

        with dpg.menu(label = 'Data',tag = 'data'):
            dpg.add_menu_item(label='Request bank', tag='load', callback = requestbank)

        with dpg.menu(label='Midi',tag = 'midi'):
            dpg.add_menu_item(label='Reset Midi Configuration', tag = 'resetconfig', callback = resetmidiconfig)
            dpg.add_menu_item(label='Reset Midi Device', tag = 'resetdevice',callback = resetmididevice)
            with dpg.menu(label='Midi Input Device', tag = 'midi_in_menu'):
                for i in indevicelist:
                    dpg.add_menu_item(tag = 'i'+i, label=i , callback= selectmidiin)
            with dpg.menu(label='Midi Output Device', tag = 'midi_out_menu'):
                for i in outdevicelist:
                    dpg.add_menu_item(tag = 'o'+i, label=i , callback= selectmidiout)
    #endregion

    #region ITEM HANDLERS
    with dpg.handler_registry():
        dpg.add_mouse_release_handler(callback = mousereleaseCallback)
        dpg.add_mouse_click_handler(callback = mouseclickCallback)
        dpg.add_key_press_handler(callback = keypresscallback)
        dpg.add_key_release_handler(callback = keyreleasecallback)
    #endregion

    #region DRAW TOP SCREEN
    dpg.add_image('blackpoint',pos = (0,0),width = 1300, height = 165)
    dpg.add_image('logo',pos = (30,40),width = 961/3.3, height = 217/3.3)
    dpg.add_image('greypoint',pos = (scp-120,43),width = 292+96,height = 114)
    dpg.add_image('screen',pos = (scp,43),width = 202, height = 114)
    dpg.add_image('mono',tag = 'displaymonopolyimg',pos = (scp,43))
    dpg.add_image('chorusoff',tag = 'displaychorusimg', pos = (scp,43))
    dpg.add_image('OCTAVEL',tag = 'displayoctaveimg',pos = (scp,43))
    dpg.add_image('SHADOW',tag = 'shadowimg',pos = (scp,43))
    dpg.add_text('CHORUS',tag = 'chorustext',pos = (scp+scp2,40), color = (54,133,116))
    dpg.add_text('MONO/POLY',tag = 'monopolytext',pos = (scp+scp2,51), color = (54,133,116))
    dpg.add_text('OCTAVE',tag = 'octavetext',pos = (scp+scp2,62), color = (54,133,116))
    dpg.add_text('UPPER',tag = 'voicenumbertext',pos = (scp+scp2,91), color = (54,133,116))
    dpg.add_text('LOWER',tag = 'voicelowertext',pos = (scp+scp2,130), color = (90,90,90))
    dpg.add_text('VOICE DATA',tag = 'voicedatatext',pos = (scp+38,23), color = (255,255,255))
    dpg.add_text('ALGORITHM',tag = 'displayalgorithmtext',pos = (832,23), color = (255,255,255))
    dpg.add_image('screen',pos = (786,43),width = 150, height = 114)
    dpg.add_image('algorithm1',tag = 'algorithmimg',pos = (786,25))
    dpg.add_image('screen',tag = '1', pos = (970,43),width = 293, height = 114)
    dpg.add_text('PITCH ENVELOPE',tag = 'pitchenvelopetext',pos = (1078,23), color = (255,255,255))
    
    # voice parameters in the display
    for i in range(12):
        N = (scp-114)
        if i in (0,1,2,3,4,5,7,8):
            textcolor = (90,90,90)
        else:
            textcolor = (54,133,116)
        dpg.add_text(displaylist[i],tag = displaylist[i]+'_text',pos = (N,40+(i*9.08)), color = textcolor)

    # NUMERIC PAD    
    x1,y1,y2 = 1123,472,36
    numberlist = ['7','8','9','4','5','6','1','2','3','0','-','+']
    dpg.add_text('VOICE SELECTION',pos = (x1-2,y1-31))
    for i in range(12):
        if i in (0,1,2):
            x = x1 + (50*i)
            y = y1
        if i in (3,4,5):
            x = x1 + (50*(i-3))
            y = y1+y2
        if i in (6,7,8):
            x = x1 + (50*(i-6))
            y = y1+(y2*2)
        if i in (9,10,11):
            x = x1 + (50*(i-9))
            y = y1+(y2*3)
        dpg.add_image_button('buttonsmall',tag = 'numberbutton'+numberlist[i],pos = (x-17,y+2), callback = Numericpad)
        dpg.add_text(numberlist[i],pos = (x ,y+2))
    
    # JOY CURSORS
    dpg.add_image('joy',tag = 'joystick',pos = (joyx,joyy))
    dpg.add_text('VOICE DATA CONTROLLER',pos = (joyx-7,joyy-30))

    # DISPLAY ARROW
    dpg.add_image('displayarrow',tag = 'arrow', pos=(scp+3,100))
    
    # SQUARES BASIC EDITION
    y = 47
    x = scp+14
    for n in range(12):
        if n in (0,1,2,3,4,5,7,8):
            dpg.add_image('displaysquare0B',tag = 'displaysquarespos'+str(n),pos = (x,y+(9*n)))
        else:
            dpg.add_image('displaysquare0',tag = 'displaysquarespos'+str(n),pos = (x,y+(9*n)))

    #endregion

    #region ######################################### COMMON PARAMETERS 1 ######################################################
    # VOICE NUMBER
    dpg.add_text('00',tag = 'voicenumber',pos = (scp+143,78))

    # ALGORITHM
    dpg.add_text('ALGORITHM:', pos = (X0-16,Y11+184),tag = 'algorithmtext')
    dpg.add_slider_int(pos = (X0,Y11),tag = 'algorithm', vertical = True, callback = Algorithm, max_value = 7, width = 25,height = 181,format= f'', no_input = True)
    dpg.add_image('fader8vert',pos = (X0-18,Y11-1))
    dpg.add_image('handlevert',pos = (X0+1,Y11+119),width = 25, height = 62, tag = 'algorithmHandle')
    with dpg.tooltip('algorithm'):
        dpg.add_text('0',tag = 'algorithmtt')

    # FEEDBACK
    dpg.add_text('FEEDBACK:', pos = (X12-13,Y11+184),tag = 'feedbacktext')
    dpg.add_slider_int(pos = (X12,Y11),tag = 'feedback', vertical = True, callback = Feedback, max_value = 7, width = 25,height = 181,format= f'', no_input = True)
    dpg.add_image('fader8vert',pos = (X12-18,Y11-1))
    dpg.add_image('handlevert',pos = (X12+1,Y11+119),width = 25, height = 62, tag = 'FeedbackHandle')
    with dpg.tooltip('feedback'):
        dpg.add_text('0',tag = 'feedbacktt')

    ########## PITCH ENVELOPE
    dpg.add_text('PITCH ENVELOPE', pos = (X14+20,Y11-34))

    # Pitchenvlevel1
    dpg.add_text('LEVEL 1:', pos = (X13-4,Y11+184),tag = 'Pitchenvlevel1text')
    dpg.add_slider_int(pos = (X13,Y11),tag = 'Pitchenvlevel1', vertical = True, callback = Pitchenvlevel1, max_value = 254, min_value = 0, default_value = 127, width = 25,height = 181,format= f'', no_input = True)
    dpg.add_image('fader0vert',pos = (X13-18,Y11-1))
    dpg.add_image('handlevert',pos = (X13+1,Y11+59),width = 25, height = 62, tag = 'Pitchenvlevel1Handle')
    with dpg.tooltip('Pitchenvlevel1'):
        dpg.add_text('0',tag = 'Pitchenvlevel1tt')
    
    # RATE1
    dpg.add_text('RATE 1:', pos = (X14-3,Y11+184),tag = 'Pitchenvrate1text')
    dpg.add_slider_int(pos = (X14,Y11),tag = 'Pitchenvrate1', vertical = True, callback = Pitchenvrate1, max_value = 127, width = 25,height = 181,format= f'', no_input = True,)
    dpg.add_image('fader64vert',pos = (X14-18,Y11-1))
    dpg.add_image('handlevert',pos = (X14+1,Y11+119),width = 25, height = 62, tag = 'Pitchenvrate1Handle')
    with dpg.tooltip('Pitchenvrate1'):
        dpg.add_text('0',tag = 'Pitchenvrate1tt')

    # Pitchenvlevel2
    dpg.add_text('LEVEL 2:', pos = (X15-5,Y11+184),tag = 'Pitchenvlevel2text')
    dpg.add_slider_int(pos = (X15,Y11),tag = 'Pitchenvlevel2', vertical = True, callback = Pitchenvlevel2, max_value = 254, default_value = 128, width = 25,height = 181,format= f'', no_input = True)
    dpg.add_image('fader0vert',pos = (X15-18,Y11-1))
    dpg.add_image('handlevert',pos = (X15+1,Y11+59),width = 25, height = 62, tag = 'Pitchenvlevel2Handle')
    with dpg.tooltip('Pitchenvlevel2'):
        dpg.add_text('0',tag = 'Pitchenvlevel2tt')

    # RATE2
    dpg.add_text('RATE 2:', pos = (X16-3,Y11+184),tag = 'Pitchenvrate2text')
    dpg.add_slider_int(pos = (X16,Y11),tag = 'Pitchenvrate2', vertical = True, callback = Pitchenvrate2, max_value = 127, width = 25,height = 181,format= f'', no_input = True)
    dpg.add_image('fader64vert',pos = (X16-18,Y11-1))
    dpg.add_image('handlevert',pos = (X16+1,Y11+119),width = 25, height = 62, tag = 'Pitchenvrate2Handle')
    with dpg.tooltip('Pitchenvrate2'):
        dpg.add_text('0',tag = 'Pitchenvrate2tt')

    # Pitchenvlevel3
    dpg.add_text('LEVEL 3:', pos = (X17-5,Y11+184),tag = 'Pitchenvlevel3text')
    dpg.add_slider_int(pos = (X17,Y11),tag = 'Pitchenvlevel3', vertical = True, callback = Pitchenvlevel3, max_value = 254, default_value = 128, width = 25,height = 181,format= f'', no_input = True)
    dpg.add_image('fader0vert',pos = (X17-18,Y11-1))
    dpg.add_image('handlevert',pos = (X17+1,Y11+59),width = 25, height = 62, tag = 'Pitchenvlevel3Handle')
    with dpg.tooltip('Pitchenvlevel3'):
        dpg.add_text('0',tag = 'Pitchenvlevel3tt')

    #endregion

    #region ####################################### COMMON PARAMETERS 2 LFO ####################################################
    dpg.add_text('LOW FREQUENCY OSCILLATOR', pos = (X10-1,Y11-34))
    # LFO WAVEFORM
    x1 = 32
    dpg.add_text('LFO WAVEFORM',tag = 'lfowavetext',pos = (x1+54,Y7-32))
    for n in range(1,5,1):
        if n in (1,2):
            x,y = (x1-74)+(100*n),Y7+7
        else:
            x,y = (x1-74)+(100*(n-2)),Y8+3
        
        dpg.add_image_button('LFOW'+str(n),tag = 'lfowave'+str(n),pos = (x-12,y-3), callback = Lfowave, width = 77, height = 31)
        dpg.add_image('lightoff',tag = 'lightofflfowave'+str(n),pos = (x-12,y-17), width = 10, height = 10)
        dpg.add_image('lighton',tag = 'lightonlfowave'+str(n),pos = (x-12,y-17), width = 10, height = 10,show = False)    

    # LFO FREQ.
    dpg.add_text('   LFO\nFREQ.:', pos = (X3-35,Y6-3),tag = 'lfofreqtext')
    dpg.add_slider_int(pos = (X3,Y6),tag = 'lfofreq', callback = Lfofreq, max_value = 255, width = 181,height = 15,format= f'', no_input = True)
    dpg.add_image('fader8',pos = (X3-1,Y6-18),width = 183, height = 56)
    dpg.add_image('handle',pos = (X3,Y6+1),width = 62, height = 25, tag = 'lfofreqHandle')
    with dpg.tooltip('lfofreq'):
        dpg.add_text('0',tag = 'lfofreqtt')

    # LFO DELAY
    dpg.add_text('     LFO\nDELAY:', pos = (X10-37,Y6-3),tag = 'lfodelaytext')
    dpg.add_slider_int(pos = (X10,Y6),tag = 'lfodelay', callback = Lfodelay, max_value = 127, width = 181,height = 15,format= f'', no_input = True)
    dpg.add_image('fader8',pos = (X10-1,Y6-18),width = 183, height = 56)
    dpg.add_image('handle',pos = (X10,Y6+1),width = 62, height = 25, tag = 'lfodelayHandle')
    with dpg.tooltip('lfodelay'):
        dpg.add_text('0',tag = 'lfodelaytt')

    # LFO RAMP
    dpg.add_text('    LFO\nRAMP:', pos = (X11-34,Y6-3),tag = 'lforamptext')
    dpg.add_slider_int(pos = (X11,Y6),tag = 'lforamp', callback = Lforamp, max_value = 127, width = 181,height = 15,format= f'', no_input = True)
    dpg.add_image('fader8',pos = (X11-1,Y6-18),width = 183, height = 56)
    dpg.add_image('handle',pos = (X11,Y6+1),width = 62, height = 25, tag = 'lforampHandle')
    with dpg.tooltip('lforamp'):
        dpg.add_text('0',tag = 'lforamptt')

    # LFO TO PITCH
    dpg.add_text('LFO TO\n  PITCH:', pos = (X10-40,Y7-3),tag = 'lfotopitchtext')
    dpg.add_slider_int(pos = (X10,Y7),tag = 'lfotopitch', callback = Lfotopitch, max_value = 127, width = 181,height = 15,format= f'', no_input = True)
    dpg.add_image('fader8',pos = (X10-1,Y7-18),width = 183, height = 56)
    dpg.add_image('handle',pos = (X10,Y7+1),width = 62, height = 25, tag = 'lfotopitchHandle')
    with dpg.tooltip('lfotopitch'):
        dpg.add_text('0',tag = 'lfotopitchtt')

    # LFO PITCH SENS
    dpg.add_text('LFO PITCH\n         SENS:', pos = (X11-54,Y7-3),tag = 'lfopitchsenstext')
    dpg.add_slider_int(pos = (X11,Y7),tag = 'lfopitchsens', callback = Lfopitchsens, max_value = 7, width = 181,height = 15,format= f'', no_input = True)
    dpg.add_image('fader8',pos = (X11-1,Y7-18),width = 183, height = 56)
    dpg.add_image('handle',pos = (X11,Y7+1),width = 62, height = 25, tag = 'lfopitchsensHandle')
    with dpg.tooltip('lfopitchsens'):
        dpg.add_text('0',tag = 'lfopitchsenstt')

    # LFO TO AMP
    dpg.add_text('LFO TO\n     AMP.:', pos = (X10-41,Y8-3),tag = 'lfotoamptext')
    dpg.add_slider_int(pos = (X10,Y8),tag = 'lfotoamp', callback = Lfotoamp, max_value = 127, width = 181,height = 15,format= f'', no_input = True)
    dpg.add_image('fader8',pos = (X10-1,Y8-18),width = 183, height = 56)
    dpg.add_image('handle',pos = (X10,Y8+1),width = 62, height = 25, tag = 'lfotoampHandle')
    with dpg.tooltip('lfotoamp'):
        dpg.add_text('0',tag = 'lfotoamptt')

    # LFO amp SENS
    dpg.add_text('LFO AMP\n       SENS:', pos = (X11-50,Y8-3),tag = 'lfoampsenstext')
    dpg.add_slider_int(pos = (X11,Y8),tag = 'lfoampsens', callback = Lfoampsens, max_value = 3, width = 181,height = 15,format= f'', no_input = True)
    dpg.add_image('fader4',pos = (X11-1,Y8-18),width = 183, height = 56)
    dpg.add_image('handle',pos = (X11,Y8+1),width = 62, height = 25, tag = 'lfoampsensHandle')
    with dpg.tooltip('lfoampsens'):
        dpg.add_text('0',tag = 'lfoampsenstt')
    #endregion

    ########################################################## TABS #############################################################
    with dpg.window(label = 'tabs window',tag = 'tabs', no_title_bar = True,no_resize = True, no_move = True, pos = (0,415), height = 1000, width = 1044 ,no_background=True,no_scrollbar = True):
        dpg.add_image('greypoint',pos = (1039,31),width = 2,height = 393,tint_color = (100,100,100))
        dpg.add_image('greypoint3',pos = (0,30),width = 1039,height = 393,tint_color = (100,100,100))
        with dpg.tab_bar(show = True):
            ################################################## OPERATORS 1-4 #######################################################
            for o in range(1,5,1):
                with dpg.tab(label='  OPERATOR '+str(o)+'  ',tag = 'op'+str(o)+'_tab'):
                    ################ BUTTONS
                    # WAVE SELECT
                    dpg.add_text('OPERATOR WAVEFORM:', pos = (150,40),tag = 'op'+str(o)+'waveselect')
                    y1,y2 = 80,137
                    for i in range(1,9,1):
                        y = y1
                        x = (i*95) - 65
                        if i >4:
                            y = y2
                            x = ((i-4)*95) - 65
                        dpg.add_image_button('wave'+str(i),tag = 'op'+str(o)+'_waveform'+str(i),pos = (x,y), callback = SelectWaveform, width = 77, height = 31)
                        dpg.add_image('lightoff',tag = 'op'+str(o)+'lightoffwave'+str(i),pos = (x,y-14), width = 10, height = 10)
                        dpg.add_image('lighton',tag = 'op'+str(o)+'lightonwave'+str(i),pos = (x,y-14), width = 10, height = 10,show = False)

                    x = 425
                    # FIXED FREQUENCY
                    dpg.add_image_button('button',tag = 'op'+str(o)+'fixedfreq',pos = (x,y1), callback = FixedFrequency, width = 77, height = 31)
                    dpg.add_text('FIXED\nFREQUENCY',tag = 'op'+str(o)+'fixedfreqtext',pos = (x+3,y1-2))
                    dpg.add_image('lightoff',tag = 'op'+str(o)+'lightofffixedfreq',pos = (x,y1-14), width = 10, height = 10)
                    dpg.add_image('lighton',tag = 'op'+str(o)+'lightonfixedfreq',pos = (x,y1-14), width = 10, height = 10,show = False)

                    # AMP MOD ENABLE
                    x = 520
                    dpg.add_image_button('button',tag = 'op'+str(o)+'ampmodenable',pos = (x,y1), callback = AmpModEnable, width = 77, height = 31)
                    dpg.add_text('LFO AMP\nMODULATION',tag = 'op'+str(o)+'ampmodenabletext',pos = (x+3,y1-2))
                    dpg.add_image('lightoff',tag = 'op'+str(o)+'lightoffampmodenable',pos = (x,y1-14), width = 10, height = 10)
                    dpg.add_image('lighton',tag = 'op'+str(o)+'lightonampmodenable',pos = (x,y1-14), width = 10, height = 10,show = False)

                    ################ SLIDERS
                    # VOLUME
                    dpg.add_text('VOLUME:', pos = (X18-8,Y1+184),tag = 'op'+str(o)+'Volumetext')
                    dpg.add_slider_int(pos = (X18,Y1),tag = 'op'+str(o)+'Volume', vertical = True, callback = Volume, max_value = 63, width = 25,height = 181,format= f'', no_input = True)
                    dpg.add_image('fader64vert',pos = (X18-18,Y1-1))
                    dpg.add_image('handlevert',pos = (X18+1,Y1+119),width = 25, height = 62, tag = 'op'+str(o)+'VolumeHandle')
                    with dpg.tooltip('op'+str(o)+'Volume'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Volumett')

                    # FINE TUNE
                    dpg.add_text('FINE\nTUNE:', pos = (X1-32,Y1-3),tag = 'op'+str(o)+'Finetunetext')
                    dpg.add_slider_int(pos = (X1,Y1),tag = 'op'+str(o)+'Finetune', callback = Finetune, max_value = 15, width = 181,height = 15,format= f'', no_input = True)
                    dpg.add_image('fader16',pos = (X1-1,Y1-18),width = 183, height = 56)
                    dpg.add_image('handle',pos = (X1,Y1+1),width = 62, height = 25, tag = 'op'+str(o)+'FinetuneHandle')
                    with dpg.tooltip('op'+str(o)+'Finetune'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Finetunett')

                    # COARSE TUNE
                    dpg.add_text('COARSE\n     TUNE:', pos = (X1-42,Y2-3),tag = 'op'+str(o)+'Coarsetunetext')
                    dpg.add_slider_int(pos = (X1,Y2),tag = 'op'+str(o)+'Coarsetune', callback = Coarsetune, max_value = 3, width = 181,height = 15,format= f'', no_input = True)
                    dpg.add_image('fader4',pos = (X1-1,Y2-18),width = 183, height = 56)
                    dpg.add_image('handle',pos = (X1,Y2+1),width = 62, height = 25, tag = 'op'+str(o)+'CoarsetuneHandle')
                    with dpg.tooltip('op'+str(o)+'Coarsetune'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Coarsetunett')

                    # FREQUENCY
                    dpg.add_text('FREQ.:', pos = (X1-34,Y3+2),tag = 'op'+str(o)+'Freqtext')
                    dpg.add_slider_int(pos = (X1,Y3),tag = 'op'+str(o)+'Freq', callback = Freq, max_value = 15, width = 181,height = 15,format= f'', no_input = True)
                    dpg.add_image('fader16',pos = (X1-1,Y3-18),width = 183, height = 56)
                    dpg.add_image('handle',pos = (X1,Y3+1),width = 62, height = 25, tag = 'op'+str(o)+'FreqHandle')
                    with dpg.tooltip('op'+str(o)+'Freq'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Freqtt')

                    # FIXED RANGE OCTAVE
                    dpg.add_text('FIX.RNG.\nOCTAVE:', pos = (X1-45,Y4-3),tag = 'op'+str(o)+'Fxrgocttext')
                    dpg.add_slider_int(pos = (X1,Y4),tag = 'op'+str(o)+'Fxrg', callback = Fixedrangeoct, max_value = 7, width = 181,height = 15,format= f'', no_input = True)
                    dpg.add_image('fader8',pos = (X1-1,Y4-18),width = 183, height = 56)
                    dpg.add_image('handle',pos = (X1,Y4+1),width = 62, height = 25, tag = 'op'+str(o)+'FxrgoctHandle')
                    with dpg.tooltip('op'+str(o)+'Fxrg'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Fxrgtt')

                    ############## KEY SCALING

                    dpg.add_text('KEY SCALING', pos = (X2+48,163))

                    # TOUCH SENS (KEY VELOCITY SENSITIVITY)
                    dpg.add_text('TOUCH\n  SENS.:', pos = (X2-38,Y1-3),tag = 'op'+str(o)+'Touchsenstext')
                    dpg.add_slider_int(pos = (X2,Y1),tag = 'op'+str(o)+'Touchsens', callback = Touchsens, max_value = 7, width = 181,height = 15,format= f'', no_input = True)
                    dpg.add_image('fader8',pos = (X2-1,Y1-18),width = 183, height = 56)
                    dpg.add_image('handle',pos = (X2,Y1+1),width = 62, height = 25, tag = 'op'+str(o)+'TouchsensHandle')
                    with dpg.tooltip('op'+str(o)+'Touchsens'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Touchsenstt')

                    # LOW LEVEL
                    dpg.add_text('   LOW KEY\n        LEVEL:', pos = (X2-55,Y2-3),tag = 'op'+str(o)+'Lowleveltext')
                    dpg.add_slider_int(pos = (X2,Y2),tag = 'op'+str(o)+'Lowlevel', callback = Lowlevel, max_value = 15, width = 181,height = 15,format= f'', no_input = True)
                    dpg.add_image('fader16',pos = (X2-1,Y2-18),width = 183, height = 56)
                    dpg.add_image('handle',pos = (X2,Y2+1),width = 62, height = 25, tag = 'op'+str(o)+'LowlevelHandle')
                    with dpg.tooltip('op'+str(o)+'Lowlevel'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Lowleveltt')

                    # HIGH LEVEL
                    dpg.add_text('  HIGH KEY\n        LEVEL:', pos = (X2-55,Y3-3),tag = 'op'+str(o)+'Highleveltext')
                    dpg.add_slider_int(pos = (X2,Y3),tag = 'op'+str(o)+'Highlevel', callback = Highlevel, max_value = 15, width = 181,height = 15,format= f'', no_input = True)
                    dpg.add_image('fader16',pos = (X2-1,Y3-18),width = 183, height = 56)
                    dpg.add_image('handle',pos = (X2,Y3+1),width = 62, height = 25, tag = 'op'+str(o)+'HighlevelHandle')
                    with dpg.tooltip('op'+str(o)+'Highlevel'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Highleveltt')

                    # RATE
                    dpg.add_text('RATE:', pos = (X2-32,Y4+2),tag = 'op'+str(o)+'KSRatetext')
                    dpg.add_slider_int(pos = (X2,Y4),tag = 'op'+str(o)+'KSRate', callback = KSRate, max_value = 3, width = 181,height = 15,format= f'', no_input = True)
                    dpg.add_image('fader4',pos = (X2-1,Y4-18),width = 183, height = 56)
                    dpg.add_image('handle',pos = (X2,Y4+1),width = 62, height = 25, tag = 'op'+str(o)+'KSRateHandle')
                    with dpg.tooltip('op'+str(o)+'KSRate'):
                        dpg.add_text('0',tag = 'op'+str(o)+'KSRatett')

                    ############## ENVELOPE
                    dpg.add_text('ATTACK', pos = (X5-5,Y5+184),tag = 'op'+str(o)+'Envattacktext')
                    dpg.add_slider_int(pos = (X5,Y5),tag = 'op'+str(o)+'Envattack', vertical = True, callback = EnvAttack, max_value = 31, height = 181,width = 25,format= f'', no_input = True,)
                    dpg.add_image('fader64vert',pos = (X5-18,Y5-1))
                    dpg.add_image('handlevert',pos = (X5+1,Y5+119),width = 25, height = 62, tag = 'op'+str(o)+'EnvattackHandle')
                    with dpg.tooltip('op'+str(o)+'Envattack'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Envattacktt')

                    dpg.add_text('DECAY 1', pos = (X6-5,Y5+184),tag = 'op'+str(o)+'Envdecay1text')
                    dpg.add_slider_int(pos = (X6,Y5),tag = 'op'+str(o)+'Envdecay1', vertical = True, callback = Envdecay1, max_value = 31, height = 181,width = 25,format= f'', no_input = True,)
                    dpg.add_image('fader64vert',pos = (X6-18,Y5-1))
                    dpg.add_image('handlevert',pos = (X6+1,Y5+119),width = 25, height = 62, tag = 'op'+str(o)+'Envdecay1Handle')
                    with dpg.tooltip('op'+str(o)+'Envdecay1'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Envdecay1tt')

                    dpg.add_text('SUSTAIN', pos = (X7-7,Y5+184),tag = 'op'+str(o)+'Envsustaintext')
                    dpg.add_slider_int(pos = (X7,Y5),tag = 'op'+str(o)+'Envsustain', vertical = True, callback = Envsustain, max_value = 15, height = 181,width = 25,format= f'', no_input = True,)
                    dpg.add_image('fader16vert',pos = (X7-18,Y5-1))
                    dpg.add_image('handlevert',pos = (X7+1,Y5+119),width = 25, height = 62, tag = 'op'+str(o)+'EnvsustainHandle')
                    with dpg.tooltip('op'+str(o)+'Envsustain'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Envsustaintt')

                    dpg.add_text('DECAY 2', pos = (X8-5,Y5+184),tag = 'op'+str(o)+'Envdecay2text')
                    dpg.add_slider_int(pos = (X8,Y5),tag = 'op'+str(o)+'Envdecay2', vertical = True, callback = Envdecay2, max_value = 31, height = 181,width = 25,format= f'', no_input = True,)
                    dpg.add_image('fader64vert',pos = (X8-18,Y5-1))
                    dpg.add_image('handlevert',pos = (X8+1,Y5+119),width = 25, height = 62, tag = 'op'+str(o)+'Envdecay2Handle')
                    with dpg.tooltip('op'+str(o)+'Envdecay2'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Envdecay2tt')

                    dpg.add_text('RELEASE', pos = (X9-7,Y5+184),tag = 'op'+str(o)+'Envreleasetext')
                    dpg.add_slider_int(pos = (X9,Y5),tag = 'op'+str(o)+'Envrelease', vertical = True, callback = Envrelease, max_value = 15, height = 181,width = 25,format= f'', no_input = True,)
                    dpg.add_image('fader16vert',pos = (X9-18,Y5-1))
                    dpg.add_image('handlevert',pos = (X9+1,Y5+119),width = 25, height = 62, tag = 'op'+str(o)+'EnvreleaseHandle')
                    with dpg.tooltip('op'+str(o)+'Envrelease'):
                        dpg.add_text('0',tag = 'op'+str(o)+'Envreleasett')

                    # ENVELOPE SCREEN
                    dpg.add_text('AMPLITUDE ENVELOPE:', pos = (X5+80,40),tag = 'op'+str(o)+'envelopetext')
                    dpg.add_image('screen',pos = (X5-22,72),width = 345, height = 108, border_color=(60,60,60))
                    with dpg.drawlist(width=1600, height=342):
                        linecolor = (56,56,56)
                        # attack
                        dpg.draw_line((X5-17, 140),(X5-17,44),tag = 'op'+str(o)+'envattackline', color=linecolor, thickness=2)
                        # decay1 / sustain
                        dpg.draw_line((X5-17,44),(X5-17,140),tag = 'op'+str(o)+'envdecay1line', color=linecolor, thickness=2)
                        # decay2
                        dpg.draw_line((X5-17,140),(X5-17,140),tag = 'op'+str(o)+'envdecay2line', color=linecolor, thickness=2)
                        # release
                        for n in range(44,140,6):
                            dpg.draw_line((X5-17,n),(X5-17,n+3),tag = 'op'+str(o)+'envkeyreleaseline'+str(n), color=(70,70,70))#, thickness=2)
                        
                        dpg.draw_line((X5-17,140),(X5-17,140),tag = 'op'+str(o)+'envreleaseline', color=linecolor, thickness=2)

                        # circles
                        circlelist = [(X5-17, 140),(X5-17, 140),(X5-17, 140),(X5-17, 44),(X5-17, 44)]
                        for n in range(5):
                            dpg.draw_circle(center = circlelist[n],radius = 3, tag = 'op'+str(o)+'circle'+str(n),color=(60,60,60),fill = (60,60,60))

    # PITCH ENVELOPE LINES
    with dpg.drawlist(width=1600, height=342):
        linecolor = (56,56,56)
        # lv1 - lv2
        dpg.draw_line((975, 68),(1108,68),tag = 'pitchenvline1', color=linecolor, thickness=2)
        # lv2 - lv3
        dpg.draw_line((1108,68),(1241,68),tag = 'pitchenvline2', color=linecolor, thickness=2)

        # circles
        pitchcirclelist = [(975, 68),(1108,68),(1241,68)]
        for n in range(3):
            dpg.draw_circle(center = pitchcirclelist[n],radius = 3, tag = 'pitchcircle'+str(n),color=(60,60,60),fill = (60,60,60))
#region################################################## DIALOG WINDOWS #######################################################
with dpg.window(label='Request bank', modal=True, show=False, tag='request_bank', no_title_bar=False, pos =[330,300],width=590,height = 350, no_resize = True, no_close = True):
    dpg.add_text('''Please, perform a voice data dump from the DSR-2000 as follow:\n\n
1- Press and hold the "MIDI MODE" yellow button on the DSR-2000.\n
2- Press the "11 (salsa)" grey key from the RHYTHM COMPOSER section.\n
3- Press the first white key on the Keyboard (C1).\n
4- Release the yellow "MIDI MODE" key and wait 5 seconds.\n\n
    This window will be closed automatically when the bulk data is received.''')
    dpg.add_text('')
    dpg.add_button(label = ' Cancel ', width = 70, pos =[238,295], callback = cancelrequest )

with dpg.window(label = 'Select midi devices', modal=True, show=False, tag='selectmidi', no_title_bar=False, pos =[390,300],width=490,height = 250, no_resize = True, no_close = True):
    dpg.add_text('Midi Input Device')
    dpg.add_combo(items=indevicelist, tag = 'firtsstartin', callback = forcemidiselect)
    dpg.add_text('Midi Output Device')
    dpg.add_combo(items=outdevicelist, tag = 'firtsstartout', callback = forcemidiselect)
    dpg.add_text(' ')
    dpg.add_button(label = 'ok', tag = 'selectmidiok', width = 60, callback = forcebulk)
#endregion

#region#####################################################  ERRORS  n#########################################################
with dpg.window(label='Error', modal=True, show=False, tag='data_error', no_title_bar=False, pos =[570,350],width=(200),no_close = True, no_resize = True):
    dpg.add_text('Invalid data.',)
    dpg.add_text('')
    dpg.add_button(label = 'ok', width = 60, callback = lambda: dpg.configure_item('data_error', show=False) )

with dpg.window(label='Error', modal=True, show=False, tag='novoice_error', no_title_bar=False, pos =[440,350],width=(400),no_close = True, no_resize = True,):
    dpg.add_text('User bank not loaded.\n\nPlease, use the menu:\nData > Request bank.')
    dpg.add_text('')
    dpg.add_button(label = 'ok', width = 60, callback = lambda: dpg.configure_item('novoice_error', show=False) )

with dpg.window(label='Error', modal=True, show=False, tag='midi_error', no_title_bar=False, pos =[570,350],width=(200),no_close = True, no_resize = True):
    dpg.add_text('Midi error.')
    dpg.add_text('')
    dpg.add_button(label = 'ok', width = 60, callback = clearmidierror )
#endregion

#region################################################# READ MIDI PREFS #######################################################
if os.path.exists(prefdir) is False:
    F = open (prefdir,'w+')
    F.write('Not connected\nNot connected')
    F.close()

def readmidiprefs():
    global inport, outport, checkinport, checkoutport
    try:
        outport.close()
    except AttributeError:
        pass
    time.sleep(0.1)
    try:
        inport.close()
    except AttributeError:
        pass
    time.sleep(0.1)
    F = open(prefdir, 'r')
    data = F.readlines()
    # Read midi input device, if exists, connect it.
    if data[0] !='Not connected':
        for i in indevicelist:
            if i == data[0][:-1]:
                dpg.set_item_label('i'+i, '*** ' + i + ' ***')
                inport = midiin.open_port(indevicelist.index(i))
                inport.ignore_types(sysex=False)
                break
    # Read midi output device, if exists, connect it.
    if data[1] !='Not connected':
        for i in outdevicelist:
            if i == data[1][:-1]:
                dpg.set_item_label('o'+i, '*** ' + i + ' ***')
                outport =  midiout.open_port(outdevicelist.index(i))
                break
    F.close()
    checkinport, checkoutport = str(inport), str(outport)
    time.sleep(0.1)

    if inport == '' or outport == '':
        dpg.configure_item('selectmidi',show = True)

def checkmidiprefs():
    if checkinport != str(inport):
        readmidiprefs()
    elif checkoutport != str(outport):
        readmidiprefs()

readmidiprefs()
#endregion

#region##################################################### THEME #############################################################
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        # # Menu bar
        dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (50, 50, 50), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (0, 0, 0), category=dpg.mvThemeCat_Core)
        # all widgets background
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (35, 35, 35), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (60, 60, 60), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (60, 60, 60), category=dpg.mvThemeCat_Core)
        # all borders
        dpg.add_theme_color(dpg.mvThemeCol_Border, (30, 30, 30), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0), category=dpg.mvThemeCat_Core)
        # Text
        dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (00, 100, 100), category=dpg.mvThemeCat_Core)
        # Combo box & selected menus
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (64, 64, 64), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (64, 64, 64), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Header, (64, 64, 64), category=dpg.mvThemeCat_Core)
        # Tabs
        dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (120, 120, 120), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_TabActive, (100, 100, 100), category=dpg.mvThemeCat_Core)
        # buttons and Combo box arrow
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (64, 64, 64), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (74, 74, 74), category=dpg.mvThemeCat_Core)
        # Slider Grab
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (50, 50, 50), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (50, 50, 50), category=dpg.mvThemeCat_Core)
        # Check mark
        dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (255, 0, 0), category=dpg.mvThemeCat_Core)
        # Window
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (40, 40, 40), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (40, 40, 40), category=dpg.mvThemeCat_Core)
        
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (40, 40, 40), category=dpg.mvThemeCat_Core)

        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 1, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 1, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 1, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 60, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 2,5, category=dpg.mvThemeCat_Core)
dpg.bind_theme(global_theme)

# DIALOG WINDOWS THEME
dialoglist = ['data_error','novoice_error','midi_error','selectmidi','request_bank']
with dpg.theme() as selectmidi_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 5,5, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 2, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Border, (54,133,116), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (54,133,116), category=dpg.mvThemeCat_Core)
for i in dialoglist:
    dpg.bind_item_theme(i,selectmidi_theme)

# Voice number input
with dpg.theme() as voicenumber_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0,0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (118,114,101,0), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Text, (56,56,56), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (56,56,56), category=dpg.mvThemeCat_Core)
dpg.bind_item_theme('voicenumber',voicenumber_theme)    

# GREY BUTTONS
with dpg.theme() as buttons_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0,0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_TabBarBorderSize, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Button, (100, 100, 100), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (100, 100, 100), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (75,75,75), category=dpg.mvThemeCat_Core)

for i in range(1,9,1):
    for o in range(1,5,1):
        dpg.bind_item_theme('op'+str(o)+'_waveform'+str(i),buttons_theme)    

for i in range(12):
    dpg.bind_item_theme('numberbutton'+numberlist[i],buttons_theme)    

# PURPLE BUTTONS
with dpg.theme() as buttons2_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0,0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_TabBarBorderSize, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Button, (80,68,93), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,  (80,68,93), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (60,48,73), category=dpg.mvThemeCat_Core)

for o in range(1,5,1):
    dpg.bind_item_theme('lfowave'+str(o),buttons2_theme)    
# ORANGE BUTTONS
with dpg.theme() as buttons3_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0,0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_TabBarBorderSize, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Button, (200,104,68), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,  (200,104,68), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (170,80,48), category=dpg.mvThemeCat_Core)

for o in range(1,5,1):
    dpg.bind_item_theme('op'+str(o)+'ampmodenable',buttons3_theme)    

# YELLOW BUTTONS
with dpg.theme() as buttons4_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0,0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_TabBarBorderSize, 0, category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Button, (175,159,84), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,  (175,159,84), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (155,129,64), category=dpg.mvThemeCat_Core)

for o in range(1,5,1):
    dpg.bind_item_theme('op'+str(o)+'fixedfreq',buttons4_theme) 

# Tab buttons
with dpg.theme() as tab_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 2,5, category=dpg.mvThemeCat_Core)
dpg.bind_item_theme('tabs',tab_theme)     

# Menu bar titles
with dpg.theme() as menutitle_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (0,0,0), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (100, 0, 0), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (0, 0, 0), category=dpg.mvThemeCat_Core)

menutitlelist = ['file','data','midi']
for i in menutitlelist:
    dpg.bind_item_theme(i,menutitle_theme)

# Menu bar content
with dpg.theme() as menu_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (60,60,60), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (0, 0, 0), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (0, 0, 0), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Text, (54,133,116), category=dpg.mvThemeCat_Core)

menulist = ['quit','loadvoice','savevoice','loadbank','savebank','load','resetconfig','resetdevice','midi_in_menu','midi_out_menu','copyoperator','pasteoperator']
for i in menulist:
    dpg.bind_item_theme(i,menu_theme)
#endregion

#region##################################################### FONTS #############################################################
with dpg.font_registry():
    default_font = dpg.add_font('Files/Fonts/Freesans.ttf', 13)
    menu_font = dpg.add_font('Files/Fonts/Freesans.ttf', 15)
    errors_font = dpg.add_font('Files/Fonts/Freesans.ttf', 18)
    small2_font = dpg.add_font('Files/Fonts/Freesans.ttf', 10)
    small_font = dpg.add_font('Files/Fonts/mono.ttf',10)
    voicefont = dpg.add_font('files/Fonts/FONT.ttf',48)

dpg.bind_font(default_font)

# VOICE NUMBER FONT
dpg.bind_item_font('voicenumber',voicefont)

# MENU FONT
menulist = ['file','data','edit','midi']
for i in menulist:
    dpg.bind_item_font(i,menu_font)

# DISPLAY ANNOTATIONS FONT
list1 = ['chorustext','monopolytext','voicenumbertext','voicelowertext','octavetext']
list2 = displaylist
list3 = list1+list2
for i in list3:
    if i in list2:
        dpg.bind_item_font(i+'_text',small_font)
    else:
        dpg.bind_item_font(i,small_font)

# SLIDERS FONT
small2ist = ['Freqtext','Volumetext','Lowleveltext','Highleveltext','KSRatetext','fixedfreqtext','ampmodenabletext','Touchsenstext','Fxrgocttext']
small2ist.extend(['Envattacktext','Envdecay1text','Envsustaintext','Envdecay2text','Envreleasetext','Finetunetext','Coarsetunetext'])
for i in small2ist:
    for o in range(1,5,1):
        dpg.bind_item_font('op'+str(o)+i,small2_font)

small2ist2 = ['feedbacktext','algorithmtext','lfofreqtext','lfodelaytext','lforamptext','lfotopitchtext','Pitchenvlevel1text']
small2ist2.extend(['lfopitchsenstext','lfotoamptext','lfoampsenstext','voicedatatext','displayalgorithmtext','pitchenvelopetext'])
small2ist2.extend(['Pitchenvrate1text','Pitchenvlevel2text','Pitchenvrate2text','Pitchenvlevel3text'])
for i in small2ist2:
    dpg.bind_item_font(i,small2_font)

for i in dialoglist:
    dpg.bind_item_font(i,errors_font)
#endregion

#region################################################# Start interface #######################################################
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window('Primary Window', True)
while dpg.is_dearpygui_running():
    dpg.render_dearpygui_frame()
dpg.destroy_context()
#endregion