
import binascii
import string
import time
import serial
import crcmod
import math

from tkinter import *
from tkinter import messagebox


SER_PORT = 'COM95'

CMD_CONFIRM_OK  = b'\x01'
CMD_CONFIRM_ERR = b'\x02'
CMD_EXE_OK      = b'\x03'
CMD_EXE_FAIL    = b'\x04'

B_C_CMD                 = '33'
SET_BR_CMD              = '34'
SET_FLASH_CLK_CMD       = '35'
RD_BL_VER_CMD           = '36'
RD_CHIP_ID_CMD          = '37'
RD_FLASH_ID_CMD         = '38'
SET_APP_LOC_CMD         = '39'
SETUP_FLASH_CMD         = '3a'
SET_ST_ADDR_CMD         = '3b'
SET_APP_SIZE_CMD        = '3c'
RD_APP_SIZE_CMD         = '3d'
SET_APP_CRC_CMD         = '3e'
RD_APP_CRC_CMD          = '3f'
SET_APP_IN_FLASH_ADDR   = '40'
RD_APP_IN_FLASH_ADDR    = '41'
SE_FLASH_CMD            = '42'
BE_FLASH_CMD            = '43'
CE_FLASH_CMD            = '44'
PROGRAM_CMD             = '45'
RD_CMD                  = '46'
VERIFY_CMD              = '47'
PROTECT_CMD             = '48'
RUN_APP_CMD             = '49'
REBOOT_CMD              = '4a'
WR_RANDOM_DATA_CMD      = '4b'
SET_APP_IN_RAM_ADDR_CMD = '4c'
SET_APP_RESET_ADDR_CMD  = '4d'

set_baudrate_cmd = bytes.fromhex('71' + SET_BR_CMD + '0400002c080000aa59') #115200
set_app_loc_cmd = bytes.fromhex('713904000001000000a7a8')  # IN_FLASH by default
# set_app_loc_cmd = bytes.fromhex('71390400000000000013de')  # IN_IRAM
st_start_addr_cmd = bytes.fromhex('71' + SET_ST_ADDR_CMD + '04000000100000d612')
se_flash_cmd = bytes.fromhex('71' + SE_FLASH_CMD + '0400000f0000005e6c')
verify_image_cmd = bytes.fromhex('71' + VERIFY_CMD + '000000b13f')
set_reboot_cmd = bytes.fromhex('71' + REBOOT_CMD + '0000003706')

set_random_cmd = bytes.fromhex('71' + WR_RANDOM_DATA_CMD + '040000c9520000c491')
set_flashclk_cmd = bytes.fromhex('71' + SET_FLASH_CLK_CMD + '04000000127a003505')
setup_flash_cmd = bytes.fromhex('71' + SETUP_FLASH_CMD + '0800000506205260b9ab010783')
set_app_in_ram_addr_cmd = bytes.fromhex('71' + SET_APP_IN_RAM_ADDR_CMD + '040000000000109034')
set_app_reset_addr_cmd = bytes.fromhex('71' + SET_APP_RESET_ADDR_CMD + '040000d4000010b111')


# from colorama import Fore
import _thread   # 导入线程包
if 0:
    CRC_DEG = 'OPEN'
else:
    CRC_DEG = 'CLOSE'

# read one byte from serial port
def serial_read_one_byte():
    oneByte = ser.readline(1)
    while oneByte == b'':
        oneByte = ser.readline(1)
    return oneByte

def cmd_crc16_check(input_str):

    read = input_str[4:-4]
    crc_pad = input_str[-2:] + input_str[-4:-2]
    crc_pad_byte = bytes.fromhex(crc_pad)
    if CRC_DEG == 'OPEN':
        print('input: '+input_str)
        print('crc_rst: '+crc_pad)
        print('CR_input: '+read)

    crc16 = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)
    data = read.replace(" ", "")
    readcrcout = hex(crc16(binascii.unhexlify(data))).upper()
    str_list = list(readcrcout)
    if len(str_list) == 5:
        str_list.insert(2, '0')  # 位数不足补0
    crc_data = "".join(str_list)
    crc_data_byte = bytes.fromhex(crc_data[2:])
    if CRC_DEG == 'OPEN':
        print(crc_data)
    if crc_pad_byte == crc_data_byte:
        return 0
    else:
        return 1


def crc16_calculate(input_byte):
    crc_payload = str(binascii.b2a_hex(input_byte))[2:-1]
    # print('crc_payload: '+crc_payload)
    crc16 = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)
    data = crc_payload.replace(" ", "")
    readcrcout = hex(crc16(binascii.unhexlify(data))).upper()
    str_list = list(readcrcout)
    if len(str_list) == 5:
        str_list.insert(2, '0')  # 位数不足补0
    else:
        if len(str_list) == 4:
            str_list.insert(2, '00')  # 位数不足补0
    crc_data = "".join(str_list)
    crc16_result_hex = bytes.fromhex(crc_data[-2:])+bytes.fromhex(crc_data[-4:-2])
    # print('crc caculate result: '+crc_data)
    # print(crc16_result_hex)
    return crc16_result_hex

def crc16_calculate_str(input_str):
    # print('crc_payload: '+input_str)
    crc16 = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)
    data = input_str.replace(" ", "")
    readcrcout = hex(crc16(binascii.unhexlify(data))).upper()
    str_list = list(readcrcout)
    if len(str_list) == 5:
        str_list.insert(2, '0')  # 位数不足补0
    else:
        if len(str_list) == 4:
            str_list.insert(2, '00')  # 位数不足补0
    crc_data = "".join(str_list)
    crc16_result_str = crc_data[-2:] + crc_data[-4:-2]
    return crc16_result_str

def rd_bl_version():
    get_bl_ver_cmd = bytes.fromhex('7136000000700b')
    ser.write(get_bl_ver_cmd)
    time.sleep(0.1)
    rec = ser.readline()
    rec_cfm = rec[0]
    # print(str_bl_ver)
    # print(type(str_bl_ver))
    if rec_cfm == 1:
        rec_payload = str(binascii.b2a_hex(rec))[2:-1]
        if cmd_crc16_check(rec_payload) == 0:
            bl_ver = rec_payload[-6:-4]+rec_payload[-8:-6]+rec_payload[-10:-8]+rec_payload[-12:-10]
            print('bootloader ver: '+bl_ver)
            return bl_ver
    else:
        print('get bootloader version failed')

def serial_read_one_frame():
    head = serial_read_one_byte()
    if head == b'\x71':
        cmd_fied = serial_read_one_byte()
        len_field = ser.readline(3)
        payload_filed = ser.readline(len_field[0])
        crc_field = ser.readline(len_field[2])
        frame = b'\x71' + cmd_fied + len_field+payload_filed+crc_field
        return frame
        # print(frame)

def rd_chip_id():
    rd_chip_id_cmd = bytes.fromhex('7137000000c47d')
    ser.write(rd_chip_id_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        rec = serial_read_one_frame()
        print(rec)
    # rd_chip_id_cmd = bytes.fromhex('7137000000c47d')
    # ser.write(rd_chip_id_cmd)
    # time.sleep(0.01)
    # rec = ser.readline()
    # rec_cfm = rec[0]
    # if rec_cfm == 1:
    #     rec_payload = str(binascii.b2a_hex(rec))[2:-1]
    #     if cmd_crc16_check(rec_payload) == 0:
    #         chip_id = rec_payload[-6:-4]+rec_payload[-8:-6]+rec_payload[-10:-8]+rec_payload[-12:-10]
    #         print('chip_id: 0x'+chip_id)
    #         return bytes.fromhex(chip_id)
    #     else:
    #         print('rd_chip_id crc check failed')

def rd_flash_id():
    rd_flash_id_cmd = bytes.fromhex('71380000002aa9')
    ser.write(rd_flash_id_cmd)
    time.sleep(0.01)
    rec = ser.readline()
    rec_cfm = rec[0]
    if rec_cfm == 1:
        rec_payload = str(binascii.b2a_hex(rec))[2:-1]
        if cmd_crc16_check(rec_payload) == 0:
            flash_id = rec_payload[-6:-4]+rec_payload[-8:-6]+rec_payload[-10:-8]+rec_payload[-12:-10]
            print('flash_id: 0x'+flash_id)
            return bytes.fromhex(flash_id)
        else:
            print('rd_flash_id crc check failed')


def Build_connection():
    print('Building connection........ \r\n'
          '-> Reset your Board')
    while True:
        ser.write(b'\x33')  # build connect with target
        time.sleep(0.005)
        recv = ser.readline()
        if recv == CMD_CONFIRM_OK:
            print('build connect success')
            break
        elif recv != b'':
            print(str(recv))


def program_one_frame(row_data):

    payload_len = len(row_data)
    if payload_len > 256:
        print('program payload len error')
    else:
        if payload_len == 256:
            frame = b'\x45\x00\x01\x00' + row_data
            crc16_pad = crc16_calculate(frame)
        else:
            frame = b'\x45'+bytes([payload_len])+b'\x00\x00'+row_data
            crc16_pad = crc16_calculate(frame)
        frame = b'\x71' + frame+ crc16_pad
    # print(frame)
    ser.write(frame)

    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        rec = serial_read_one_byte()
        if rec == CMD_EXE_OK:
            return CMD_EXE_OK
        else:
            print('setup_flash: CMD_EXE_FAIL')
            exit()
    else:
        print('setup_flash: CMD_CONFIRM_ERR')
        exit()



def image_programming(image,image_size):

    pk_nb = image_size/256
    print(pk_nb)
    i = 0
    while image_size > 0:
        current_data = image[256*i:256*(i+1)]
        if CMD_EXE_OK == program_one_frame(current_data):
            # print("download one frame")
            time.sleep(0.001)
        i += 1
        image_size -= 256
        print('Programming -> ' + str(math.ceil(100*i/pk_nb)) + '%')




def set_app_loc():
    ser.write(set_app_loc_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        return CMD_CONFIRM_OK
    else:
        print('set app loc rec_cfm failed:'+str(rec))

# /* sset the start address of read, program, erase and verify cmds*/
def set_start_addr():
    ser.write(st_start_addr_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        return CMD_CONFIRM_OK
    else:
        print('set_start_addr: CMD_CONFIRM_ERR')

def sector_erase_flash():
    ser.write(se_flash_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        rec = serial_read_one_byte()
        if rec == CMD_EXE_OK:
            return CMD_EXE_OK
        else:
            print('sector_erase_flash: '+str(rec))
            exit()
    else:
        print('sector_erase_flash: CMD_CONFIRM_ERR')
        exit()

def write_random_data():
    # print(write_random_data)
    ser.write(set_random_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        rec = serial_read_one_byte()
        if rec == CMD_EXE_OK:
            return CMD_EXE_OK
        else:
            print('write_random_data: CMD_EXE_FAIL')
            exit()
    else:
        print('write_random_data: CMD_CONFIRM_ERR')
        exit()

def set_flash_clk():
    # print(set_flash_clk)
    ser.write(set_flashclk_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        rec = serial_read_one_byte()
        if rec == CMD_EXE_OK:
            return CMD_EXE_OK
        else:
            print('set_flash_clk: CMD_EXE_FAIL')
            exit()
    else:
        print('set_flash_clk: CMD_CONFIRM_ERR')
        exit()

def setup_flash():
    # print(setup_flash)
    ser.write(setup_flash_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        rec = serial_read_one_byte()
        if rec == CMD_EXE_OK:
            return CMD_EXE_OK
        else:
            print('setup_flash: CMD_EXE_FAIL')
            exit()
    else:
        print('setup_flash: CMD_CONFIRM_ERR')
        exit()


def set_app_in_ram_addr():
    # print(set_app_in_ram_addr)
    ser.write(set_app_in_ram_addr_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        rec = serial_read_one_byte()
        if rec == CMD_EXE_OK:
            return CMD_EXE_OK
        else:
            print('set_app_reset_addr: CMD_EXE_FAIL')
            exit()
    else:
        print('set_app_in_ram_addr: CMD_CONFIRM_ERR')
        exit()

def set_app_reset_addr():
    ser.write(set_app_reset_addr_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        rec = serial_read_one_byte()
        if rec == CMD_EXE_OK:
            return CMD_EXE_OK
        else:
            print('set_app_reset_addr: CMD_EXE_FAIL')
            exit()
    else:
        print('set_app_reset_addr: CMD_CONFIRM_ERR')
        exit()

def set_app_size():
    str_list = list(hex(image_size))
    # print(str_list)
    while (len(str_list) < 10):
        str_list.insert(2, '0')  # 位数不足补0
    app_size_str = "".join(str_list)
    app_size_str = app_size_str[-2:]+app_size_str[-4:-2]+app_size_str[-6:-4]+app_size_str[2:4]# 倒序
    # print('app_size_str: ' + app_size_str)
    cmd_payload_str = SET_APP_SIZE_CMD+'040000'+app_size_str
    crc_str = crc16_calculate_str(cmd_payload_str)
    set_app_size_cmd = bytes.fromhex('71'+cmd_payload_str+crc_str)
    ser.write(set_app_size_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        rec = serial_read_one_byte()
        if rec == CMD_EXE_OK:
            return CMD_EXE_OK
        else:
            print('set_app_size: CMD_EXE_FAIL')
            exit()
    else:
        print('set_app_size: CMD_CONFIRM_ERR')
        exit()



def set_app_crc():
    # print(set_app_crc)
    image_str = str(binascii.b2a_hex(image))[2:-1]  # convert to string
    # print('image_str: ' + image_str)
    app_crc = crc16_calculate_str(image_str)  # calculate image app crc value
    # print('app_crc: ' + app_crc)
    set_app_crc_cmd = '3e040000' + app_crc + '0000'  # struct command
    fram_crc = crc16_calculate_str(set_app_crc_cmd)
    # print('fram_crc: ' + fram_crc)
    set_app_crc_cmd = '71' + set_app_crc_cmd + fram_crc
    # print(set_app_crc_cmd)
    set_app_crc_cmd = bytes.fromhex(set_app_crc_cmd)
    ser.write(set_app_crc_cmd)#writ one frame
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        rec = serial_read_one_byte()
        if rec == CMD_EXE_OK:
            return CMD_EXE_OK
        else:
            print('set_app_crc: CMD_EXE_FAIL')
            exit()
    else:
        print('set_app_crc: CMD_CONFIRM_ERR')
        exit()

def program_boot_inf():
    set_app_loc()
    set_start_addr()
    sector_erase_flash()
    write_random_data()
    set_flash_clk()
    setup_flash()
    set_app_in_ram_addr()
    set_app_reset_addr()
    set_app_size()
    set_app_crc()

def verify_image():
    ser.write(verify_image_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        time.sleep(1)
        rec = serial_read_one_byte()
        if rec == CMD_EXE_OK:
            return CMD_EXE_OK
        else:
            print(rec)
            print('verify_image: CMD_EXE_FAIL')
            # exit()
    else:
        print(rec)
        print('verify_image: CMD_CONFIRM_ERR')
        exit()

def set_reboot():
    ser.write(set_reboot_cmd)
    rec = serial_read_one_byte()
    if rec == CMD_CONFIRM_OK:
        return CMD_CONFIRM_OK
    else:
        print('set_reboot: CMD_CONFIRM_ERR')
        exit()

def baudrate_update(): #update baudrate to 115200
    ser.write(set_baudrate_cmd)
    # time.sleep(0.01)
    # rec = ser.readline()
    rec = serial_read_one_byte()
    # print(rec)
    if rec == CMD_CONFIRM_OK:
        ser.close()
        ser.port = SER_PORT#'COM94'
        ser.baudrate = 115200
        ser.timeout = 0.05
        ser.open()
        return CMD_CONFIRM_OK
    else:
        print('baudrate_update: CMD_CONFIRM_ERR')
        exit()



#=====================================================================
#
# main function: 函数入口
# print('input serial port:')
# SER_PORT = input()
if __name__ == '__main__':
    root = Tk(className=' QN902x ISP Tool v0.0.1.  ')
    root.geometry("450x180")

    root.mainloop()

    SER_PORT = 'com7'
    ser = serial.Serial()
    ser.port = SER_PORT
    ser.baudrate = 9600
    ser.timeout = 0.05
    ser.open()


    print('Input Your Firmware:')
    # firmware = input()
    # firmware = 'C:\nxp\QN902x_SDK_1.4.0\BinFiles\BinFiles_B2_v40\qpps.bin'
    # file = open(firmware, "rb")
    # file = open("firmware.bin", "rb")
    file = open("qpps.bin", "rb")
    image = file.read()
    image_size = len(image)
    file.close()

    Build_connection()          # Try to connect with target
    # baudrate_update()

    # bl_ver = rd_bl_version()    # Get bootloader version
    # chip_id = rd_chip_id()      # read chip id
    # flash_id = rd_flash_id()    # read flash id

    program_boot_inf()
    image_programming(image, image_size)         # program image
    time.sleep(0.1)
    verify_image()              # verify image

    # 71 4a 00 00  00 37 06
    set_reboot()

    print('*********************************************************')
    print('download firmware success!!!')
    print('*********************************************************')
    # file_size = sizeof(file)
    # print(file_size)

    ser.close()





