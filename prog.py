# # Scanner
# import Adafruit_GPIO.FT232H as FT232H

# # Temporarily disable FTDI serial drivers.
# FT232H.use_FT232H()

# # Find the first FT232H device.
# ft232h = FT232H.FT232H()

# print 'Scanning all I2C bus addresses...'
# # Enumerate all I2C addresses.
# for address in range(127):
#     # Skip I2C addresses which are reserved.
#     if address <= 7 or address >= 120:
#         continue
#     # Create I2C object.
#     i2c = FT232H.I2CDevice(ft232h, address)
#     # Check if a device responds to this address.
#     if i2c.ping():
#         print 'Found I2C device at address 0x{0:02X}'.format(address)
# print 'Done!'

import Adafruit_GPIO.FT232H as FT232H
import sys
import os
import crc
import time
import argparse


parser = argparse.ArgumentParser(description='RTD2660 Flash Reader.')
parser.add_argument('--flash-filename', dest='flashfile', help='Flash this file to the controller')
parser.add_argument('--dump-filename', dest='readfile', help='Read into this file from the controller')

args = parser.parse_args()
print(args)

DUMP_ACTION = False
FLASH_ACTION = False

if(not args.flashfile == None and not args.readfile == None):
    print "Choose to read OR write the controller. Not both."
    exit()
elif(not args.readfile == None):
    # reading controller
    print "reading controller"
    DUMP_ACTION = True
elif(not args.flashfile == None):
    # flashing the controller
    print "flashing the controller"
    FLASH_ACTION = True
else:
    # they chose nothing
    parser.print_help()
    exit()


print(args)



E_CC_NOOP = 0
E_CC_WRITE = 1
E_CC_READ = 2
E_CC_WRITE_AFTER_WREN = 3
E_CC_WRITE_AFTER_EWSR = 4
E_CC_ERASE = 5


# Temporarily disable FTDI serial drivers.
FT232H.use_FT232H()
 
# Find the first FT232H device.
ft232h = FT232H.FT232H()
 
# Create an I2C device at address 0x70.
i2c = FT232H.I2CDevice(ft232h, 0x4A)

class FlashDesc:
    def __init__(self, device_name,jedec_id,size_kb,page_size,block_size_kb):
        self.device_name = device_name;
        self.jedec_id = jedec_id;
        self.size_kb = size_kb;
        self.page_size = page_size;
        self.block_size_kb = block_size_kb;

FlashDevices = [
    #          name,         Jedec ID,    sizeK, page size, block sizeK
    FlashDesc("AT25DF041A" , 0x1F4401,      512,       256, 64),
    FlashDesc("AT25DF161"  , 0x1F4602, 2 * 1024,       256, 64),
    FlashDesc("AT26DF081A" , 0x1F4501, 1 * 1024,       256, 64),
    FlashDesc("AT26DF0161" , 0x1F4600, 2 * 1024,       256, 64),
    FlashDesc("AT26DF161A" , 0x1F4601, 2 * 1024,       256, 64),
    FlashDesc("AT25DF321" ,  0x1F4701, 4 * 1024,       256, 64),
    FlashDesc("AT25DF512B" , 0x1F6501,       64,       256, 32),
    FlashDesc("AT25DF512B" , 0x1F6500,       64,       256, 32),
    FlashDesc("AT25DF021"  , 0x1F3200,      256,       256, 64),
    FlashDesc("AT26DF641" ,  0x1F4800, 8 * 1024,       256, 64),
    # Manufacturer: ST 
    FlashDesc("M25P05"     , 0x202010,       64,       256, 32),
    FlashDesc("M25P10"     , 0x202011,      128,       256, 32),
    FlashDesc("M25P20"     , 0x202012,      256,       256, 64),
    FlashDesc("M25P40"     , 0x202013,      512,       256, 64),
    FlashDesc("M25P80"     , 0x202014, 1 * 1024,       256, 64),
    FlashDesc("M25P16"     , 0x202015, 2 * 1024,       256, 64),
    FlashDesc("M25P32"     , 0x202016, 4 * 1024,       256, 64),
    FlashDesc("M25P64"     , 0x202017, 8 * 1024,       256, 64),
    # Manufacturer: Windbond 
    FlashDesc("W25X10"     , 0xEF3011,      128,       256, 64),
    FlashDesc("W25X20"     , 0xEF3012,      256,       256, 64),
    FlashDesc("W25X40"     , 0xEF3013,      512,       256, 64),
    FlashDesc("W25X80"     , 0xEF3014, 1 * 1024,       256, 64),
    # Manufacturer: Macronix 
    FlashDesc("MX25L512"   , 0xC22010,       64,       256, 64),
    FlashDesc("MX25L3205"  , 0xC22016, 4 * 1024,       256, 64),
    FlashDesc("MX25L6405"  , 0xC22017, 8 * 1024,       256, 64),
    FlashDesc("MX25L8005"  , 0xC22014,     1024,       256, 64),
    # Microchip
    FlashDesc("SST25VF512" , 0xBF4800,       64,       256, 32),
    FlashDesc("SST25VF032" , 0xBF4A00, 4 * 1024,       256, 32),
    FlashDesc(None , 0, 0, 0, 0)
]

# returns uint32_t
    # cmd_type, # ECommondCommandType
    # cmd_code, # uint8_t
    # read_length, # uint8_t
    # write_length, # uint8_t
    # write_value, # uint32_t
def SPICommonCommand( cmd_type, cmd_code, read_length, write_length, write_value):
    read_length &= 3
    write_length &= 3
    write_value &= 0xFFFFFF
    # uint8_t
    reg_value = (cmd_type << 5) | (write_length << 3) | (read_length << 1)

    i2c.write8(0x60, reg_value)
    i2c.write8(0x61, cmd_code)

    if write_length == 3:
        i2c.write8(0x64, write_value >> 16)
        i2c.write8(0x65, write_value >> 8)
        i2c.write8(0x66, write_value)
    elif write_length == 2:
        i2c.write8(0x64, write_value >> 8)
        i2c.write8(0x65, write_value)
    elif write_length == 3:
        i2c.write8(0x64, write_value)

    i2c.write8(0x60, reg_value | 1) # Execute the command
    # uint8_t b;
    b = i2c.readU8(0x60)
    while (b & 1):
        b = i2c.readU8(0x60)

    if read_length == 0:
        return 0
    elif read_length == 1:
        return i2c.readU8(0x67)
    elif read_length == 2:
        return (i2c.readU8(0x67) << 8) | i2c.readU8(0x68)
    elif read_length == 3:
        return (i2c.readU8(0x67) << 16) | (i2c.readU8(0x68) << 8) | i2c.readU8(0x69)

    return 0;

# uint32_t address,
# uint8_t *data, 
# int32_t len
def SPIRead( address, data, len):
    i2c.write8(0x60, 0x46)
    i2c.write8(0x61, 0x3)
    i2c.write8(0x64, address>>16)
    i2c.write8(0x65, address>>8)
    i2c.write8(0x66, address)
    i2c.write8(0x60, 0x47) # Execute the command
    # uint8_t b;
    b = i2c.readU8(0x60)

    while(b & 1):
        b = i2c.readU8(0x60)
        # TODO: add timeout and reset the controller

    while (len > 0):
        read_len = len # int32_t
        if (read_len > 64):
            read_len = 64

        # Original
        # ReadBytesFromAddr(0x70, data, read_len)

        # Adafruit library
        # keeps failing with an ACK error
        # bytedata = i2c.readList(0x70, read_len) # returns bytearray
        
        # fell back to reading ONE BYTE AT A TIME! (this took around 8-10 mins)
        bytedata = bytearray()
        itr = read_len
        while(itr > 0):
            bytedata += bytearray([i2c.readU8(0x70)])
            itr -= 1
        
        # data += read_len

        data += bytedata
        len -= read_len

# void PrintManufacturer(uint32_t id) {
def PrintManufacturer(id):
    if id == 0x20:
        print "ST"
    elif id == 0xef:
        print "Winbond"
    elif id == 0x1f:
        print "Atmel"
    elif id == 0xc2:
        print "Macronix"
    elif id == 0xbf:
        print "Microchip"
    else:
        print "Unknown"


# static const FlashDesc* FindChip(uint32_t jedec_id) {
def FindChip(jedec_id):
    for chip in FlashDevices:
        if (chip.jedec_id == jedec_id):
            return chip
    return None


# uint8_t SPIComputeCRC(uint32_t start, uint32_t end) {
def SPIComputeCRC(start, end):
    i2c.write8(0x64, start >> 16)
    i2c.write8(0x65, start >> 8)
    i2c.write8(0x66, start)

    i2c.write8(0x72, end >> 16)
    i2c.write8(0x73, end >> 8)
    i2c.write8(0x74, end)

    i2c.write8(0x6f, 0x84)
    
    # uint8_t b;
    b = i2c.readU8(0x6f)
    while (not (b & 0x2)):
        b = i2c.readU8(0x6f)
    # TODO: add timeout and reset the controller

    return i2c.readU8(0x75)


# uint8_t GetManufacturerId(uint32_t jedec_id)
def GetManufacturerId(jedec_id):
    return jedec_id >> 16


# void SetupChipCommands(uint32_t jedec_id)
def SetupChipCommands(jedec_id):
    # uint8_t manufacturer_id = GetManufacturerId(jedec_id);
    manufacturer_id = GetManufacturerId(jedec_id)
    if manufacturer_id == 0xEF:
        # These are the codes for Winbond
        i2c.write8(0x62, 0x6)  # Flash Write enable op code
        i2c.write8(0x63, 0x50) # Flash Write register op code
        i2c.write8(0x6a, 0x3)  # Flash Read op code.
        i2c.write8(0x6b, 0xb)  # Flash Fast read op code.
        i2c.write8(0x6d, 0x2)  # Flash program op code.
        i2c.write8(0x6e, 0x5)  # Flash read status op code.
    else:
        printf("Can not handle manufacturer code %02x\n", manufacturer_id)



# bool SaveFlash(const char *output_file_name, uint32_t chip_size) {

def SaveFlash(output_file_name, chip_size):

    # FILE *dump = fopen(output_file_name, "wb");
    dump = open(output_file_name, "wb")
    # uint32_t addr = 0;
    addr = 0
    crc.InitCRC();
    while (addr < chip_size):
        # uint8_t buffer[1024];
        # buffer = 1024 * [None]
        buffer = bytearray()
        # printf("Reading addr %x\r", addr);
        print 'Reading addr {0} [{0:02X}]\r'.format(addr)
        # SPIRead(addr, buffer, sizeof(buffer));
        SPIRead(addr, buffer, 1024);
        # buffer = i2c.readList(addr, 32) # returns bytearray

        print "Got data ({0} bytes):\r\n".format(len(buffer))
        # print buffer
        # print "\r\n"

        # fwrite(buffer, 1, sizeof(buffer), dump);
        dump.write(buffer);

        # addr += sizeof(buffer);
        addr += len(buffer)


        # ProcessCRC(buffer, sizeof(buffer));

        # temporarily disabling CRC
        crc.ProcessCRC(buffer, len(buffer))
        # 


        print "New address: {0}\r\n".format(addr)
    

    print "done.\n"
    # fclose(dump);
    dump.close()
    # uint8_t data_crc = GetCRC();
    data_crc = crc.GetCRC()
    # uint8_t chip_crc = SPIComputeCRC(0, chip_size - 1);

    # Temporarily disabling CRC
    chip_crc = SPIComputeCRC(0, chip_size - 1)
    # chip_crc = 0
    # 

    print "Received data CRC {0:02X}\n".format(data_crc);
    print "Chip CRC {0:02X}\n".format(chip_crc);
    return data_crc == chip_crc;


# uint64_t GetFileSize(FILE* file) {
def GetFileSize(file):
    return os.stat.st_size(file)


# # static uint8_t* ReadFile(const char *file_name, uint32_t* size) {
# ReadFile(file_name, size)
#     # FILE *file = fopen(file_name, "rb");
#     file = open(file_name, "rb")
#     # uint8_t* result = NULL;
#     result = NULL;
#     if (NULL == file):
#         # printf("Can't open input file %s\n", file_name);
#         print "Can't open input file {0}\n".format(file_name);
#         return result;

#     # uint64_t file_size64 = GetFileSize(file);
#     file_size64 = GetFileSize(file);
#     if (file_size64 > 8*1024*1024):
#         # printf("This file looks to big %lld\n", file_size64);
#         print "This file looks to big {0}\n".format(file_size64);
#         # fclose(file);
#         file.close();
#         return result;
        
#     # uint32_t file_size = (uint32_t)file_size64;
#     file_size = file_size64;
#     # result = new uint8_t[file_size];
#     result = [0] * file_size;
#     if (NULL == result):
#         # printf("Not enough RAM.\n");
#         print "Not enough RAM.\n";
#         # fclose(file);
#         file.close();
#         return result;

#     # fread(result, 1, file_size, file);
#     file.read() fread(result, 1, file_size, file);
#     # fclose(file);
#     file.close();
#     if (memcmp("GMI GFF V1.0", result, 12) == 0) {
#       printf("Detected GFF image.\n");
#       // Handle GFF file
#       if (file_size < 256) {
#         printf("This file looks to small %d\n", file_size);
#         delete [] result;
#         return NULL;
#       }
#       uint32_t gff_size = ComputeGffDecodedSize(result + 256,
#         file_size - 256);
#       if (gff_size == 0) {
#         printf("GFF Decoding failed for this file\n");
#         delete [] result;
#         return NULL;
#       }
#       uint8_t* gff_data = new uint8_t[gff_size];
#       if (NULL == gff_data) {
#         printf("Not enough RAM.\n");
#         delete [] result;
#         return NULL;
#       }
#       DecodeGff(result + 256, file_size - 256, gff_data);
#       // Replace the encoded buffer with the decoded data.
#       delete [] result;
#       result = gff_data;
#       file_size = gff_size;
#     }
#     if (NULL != size) {
#       *size = file_size;
#     }
#     return result;


# static bool ShouldProgramPage(uint8_t* buffer, uint32_t size) {
def ShouldProgramPage(buffer, size):
    # for (uint32_t idx = 0; idx < size; ++idx) {
    idx = 0
    while idx < size:
        if (buffer[idx] != 0xff):
            return True;
        ++idx
    return False;


# bool ProgramFlash(const char *input_file_name, uint32_t chip_size) {
#   uint32_t prog_size;
#   uint8_t* prog = ReadFile(input_file_name, &prog_size);
#   if (NULL == prog) {
#     return False;
#   }
#   printf("Erasing...");fflush(stdout);
#   SPICommonCommand(E_CC_WRITE_AFTER_EWSR, 1, 0, 1, 0); // Unprotect the Status Register
#   SPICommonCommand(E_CC_WRITE_AFTER_WREN, 1, 0, 1, 0); // Unprotect the flash
#   SPICommonCommand(E_CC_ERASE, 0xc7, 0, 0, 0);         // Chip Erase
#   printf("done\n");

#   //RTD266x can program only 256 bytes at a time.
#   uint8_t buffer[256];
#   uint8_t b;
#   uint32_t addr = 0;
#   uint8_t* data_ptr = prog;
#   uint32_t data_len = prog_size;
#   InitCRC();
#   do
#   {
#     // Wait for programming cycle to finish
#     do {
#       b = ReadReg(0x6f);
#     } while (b & 0x40);

#     printf("Writing addr %x\r", addr);
#     // Fill with 0xff in case we read a partial buffer.
#     memset(buffer, 0xff, sizeof(buffer));
#     uint32_t len = sizeof(buffer);
#     if (len > data_len) {
#       len = data_len;
#     }
#     memcpy(buffer, data_ptr, len);
#     data_ptr += len;
#     data_len -= len;

#     if (ShouldProgramPage(buffer, sizeof(buffer))) {
#       // Set program size-1
#       WriteReg(0x71, 255);

#       // Set the programming address
#       WriteReg(0x64, addr >> 16);
#       WriteReg(0x65, addr >> 8);
#       WriteReg(0x66, addr);

#       // Write the content to register 0x70
#       // Out USB gizmo supports max 63 bytes at a time.
#       WriteBytesToAddr(0x70, buffer, 63);
#       WriteBytesToAddr(0x70, buffer + 63, 63);
#       WriteBytesToAddr(0x70, buffer + 126, 63);
#       WriteBytesToAddr(0x70, buffer + 189, 63);
#       WriteBytesToAddr(0x70, buffer + 252, 4);

#       WriteReg(0x6f, 0xa0); // Start Programing
#     }
#     ProcessCRC(buffer, sizeof(buffer));
#     addr += 256;
#   } while (addr < chip_size and data_len != 0);
#   delete [] prog;

#   // Wait for programming cycle to finish
#   do {
#     b = ReadReg(0x6f);
#   } while (b & 0x40);

#   SPICommonCommand(E_CC_WRITE_AFTER_EWSR, 1, 0, 1, 0x1c); // Unprotect the Status Register
#   SPICommonCommand(E_CC_WRITE_AFTER_WREN, 1, 0, 1, 0x1c); // Protect the flash

#   uint8_t data_crc = GetCRC();
#   uint8_t chip_crc = SPIComputeCRC(0, addr - 1);
#   printf("Received data CRC %02x\n", data_crc);
#   printf("Chip CRC %02x\n", chip_crc);
#   return data_crc == chip_crc;
# }





# Main


# # int main(int argc, char* argv[])
# def main():
#   uint8_t b;
#   if (!InitI2C()) {
#     printf("Can't connect to the USB device. Check the cable.\n");
#     return -1;
#   }
#   printf("Ready\n");
#   SetI2CAddr(0x4a);

#   const FlashDesc* chip;
#   bool cnt;
#   do {
#     cnt = False;
#     if (!WriteReg(0x6f, 0x80)) {  // Enter ISP mode
#       printf("Write to 6F failed.\n");
#       //return -2;
#       cnt = True;
#       continue;
#     }
#     b = ReadReg(0x6f);
#     if (!(b & 0x80)) {
#       printf("Can't enable ISP mode\n");
#       //return -3;
#       cnt = True;
#       continue;
#     }
#     uint32_t jedec_id = SPICommonCommand(E_CC_READ, 0x9f, 3, 0, 0);
#     printf("JEDEC ID: 0x%02x\n", jedec_id);
#     chip = FindChip(jedec_id);
#     if (NULL == chip) {
#       printf("Unknown chip ID\n");
#       cnt = True;
#       continue;
#     }
#   } while(cnt);
#   printf("Manufacturer ");
#   PrintManufacturer(GetManufacturerId(chip->jedec_id));
#   printf("\n");
#   printf("Chip: %s\n", chip->device_name);
#   printf("Size: %dKB\n", chip->size_kb);

#   // Setup flash command codes
#   SetupChipCommands(chip->jedec_id);

#   b = SPICommonCommand(E_CC_READ, 0x5, 1, 0, 0);
#   printf("Flash status register: 0x%02x\n", b);
  
# #if 0
#   SaveFlash("flash-test.bin", chip->size_kb * 1024);
# #else
#   # ProgramFlash("1024x600.bin", chip->size_kb * 1024);
# #endif
#   CloseI2C();
#     return 0;
# }

# {
#     "W25X40", # chip name (device_name)
#     0xEF3013, # jedec id (jedec_id)
#     512,      # flash size K (size_kb)
#     256,      # page size (page_size)
#     64        # block size K (block_size_kb)
# }

# Enter ISP Mode
i2c.write8(0x6f, 0x80)
    # uint32_t jedec_id = SPICommonCommand(E_CC_READ, 0x9f, 3, 0, 0);
jedec_id = SPICommonCommand(E_CC_READ, 0x9f, 3, 0, 0);
    # printf("JEDEC ID: 0x%02x\n", jedec_id);
print "JEDEC ID: 0x{:02X}\n".format(jedec_id);
chip = FindChip(jedec_id);


if jedec_id == 15675411:
    print "flash matches!"
else:
    print "what is this flash chip?"
    exit(0)


print "Manufacturer "
PrintManufacturer(GetManufacturerId(chip.jedec_id));
print "\n"
print "Chip: {}\n".format(chip.device_name)
print "Size: {}KB\n".format(chip.size_kb)

#   // Setup flash command codes
SetupChipCommands(jedec_id)


b = SPICommonCommand(E_CC_READ, 0x5, 1, 0, 0)
print "Flash status register: 0x{:02X}\n".format(b)

ticks = time.time()

if(DUMP_ACTION):
    print "Saving controller flash to \"{0}\"".format(os.path.abspath(args.readfile))
    SaveFlash(args.readfile, chip.size_kb * 1024)
elif(FLASH_ACTION):
    print "Flashing \"{0}\" to controller".format(os.path.abspath(args.flashfile))

duration = time.time() - ticks

remainder = duration % (60 * 60)
hour_secs = duration - remainder
hours = hour_secs/(60 * 60)

duration -= hour_secs

remainder = duration % (60)
min_secs = duration - remainder
mins = min_secs/(60)

duration -= min_secs

secs = duration

print "run time: {0}:{1}:{2}".format(hours, mins, secs)
#  /cygdrive/z/Workspaces/RTD2660H\ LCD\ TFT\ Controller\ I2C

exit()