import os
import gc
import board
import busio
import time
import storage
import displayio
import terminalio
import ulab.numpy as np
import adafruit_mlx90640
from adafruit_bitmapsaver import save_pixels
from adafruit_st7735r import ST7735R
from adafruit_display_text.label import Label
from simpleio import map_range
from digitalio import DigitalInOut, Direction, Pull

# GP0 to GND to remount storage (to save screenshots)
mountstor = DigitalInOut(board.GP0)
mountstor.direction = Direction.INPUT
mountstor.pull = Pull.UP

try:
    if mountstor.value == False:
        print("storage active\n ------------")
        storage.remount("/", readonly=mountstor.value)       
    else:
        print("no storage\n ---------------")
except:
    pass

# button to take screenshot
button = DigitalInOut(board.GP22)
button.direction = Direction.INPUT
button.pull = Pull.UP
print(button.value)  # False == button pressed

# def SPI pins for display
mosi_pin = board.GP11
clk_pin = board.GP10
reset_pin = board.GP17
cs_pin = board.GP18
dc_pin = board.GP16

# init disp
displayio.release_displays()
spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin)
display_bus = displayio.FourWire(
    spi, command=dc_pin, chip_select=cs_pin, reset=reset_pin
)
display = ST7735R(display_bus, width=128, height=160, bgr=True)

number_of_colors = 64  # Number of color in the gradian
last_color = number_of_colors - 1  # Last color in palette
palette = displayio.Palette(number_of_colors)  # Palette with all our colors

## custom color gradian for heatmap
color_A = [
    [33, 22, 44],
    [0, 100, 100],
    [210, 210, 210],
    [35, 245, 224],
    [250, 5, 205]
]
color_B = [
    [5, 40, 50],
    [5, 230, 75],
    [235, 155, 5],
    [230, 5, 75]
]

color = color_B #  color_A
NUM_COLORS = len(color)

def MakeHeatMapColor():
    for c in range(number_of_colors):
        value = c * (NUM_COLORS - 1) / last_color
        idx1 = int(value)  # Our desired color will be after this index.
        if idx1 == value:  # This is the corner case
            red = color[idx1][0]
            green = color[idx1][1]
            blue = color[idx1][2]
        else:
            idx2 = idx1 + 1  # ... and before this index (inclusive).
            fractBetween = value - idx1  # Distance between the two indexes (0-1).
            red = int(
                round((color[idx2][0] - color[idx1][0]) * fractBetween + color[idx1][0])
            )
            green = int(
                round((color[idx2][1] - color[idx1][1]) * fractBetween + color[idx1][1])
            )
            blue = int(
                round((color[idx2][2] - color[idx1][2]) * fractBetween + color[idx1][2])
            )
        palette[c] = (0x010000 * red) + (0x000100 * green) + (0x000001 * blue)

MakeHeatMapColor()

# Bitmap for color coded thermal value
image_bitmap = displayio.Bitmap(24, 32, number_of_colors)

# Create a TileGrid using the Bitmap and Palette
image_tile = displayio.TileGrid(image_bitmap, pixel_shader=palette)
image_tile.x = 3
image_tile.y = 4

# Create a group to scale 24*32 sensor data to 96*128 to display
image_group = displayio.Group(scale=4)
image_group.append(image_tile)

# Create a temp. scale with color range matching the selected heatmap
scale_bitmap = displayio.Bitmap(1, number_of_colors, number_of_colors)
scale_group = displayio.Group(scale=2)
scale_tile = displayio.TileGrid(scale_bitmap, pixel_shader=palette, x=58, y=8)
scale_group.append(scale_tile)

for i in range(number_of_colors):
    scale_bitmap[0, i] = i  # Fill the scale with the palette gradian

# Add min. and max. temp values in matching colors 
min_label = Label(terminalio.FONT, scale=1, color=palette[0], x=92, y=8)
max_label = Label(terminalio.FONT, scale=1, color=palette[last_color], x=92, y=152)

# Create the main group and add all sub-groups to display
group = displayio.Group()

group.append(image_group)
group.append(scale_group)
group.append(min_label)
group.append(max_label)

display.show(group)

# Sensor setup
# i2c = busio.I2C(board.GP21, board.GP20, frequency=800000)
i2c = busio.I2C(board.GP21, board.GP20, frequency=1000000)

mlx = adafruit_mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C")
print([hex(i) for i in mlx.serial_number])

# mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_0_5_HZ
# mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_1_HZ
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_16_HZ
# mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2/4/8/16/32_HZ

last_time1 = time.monotonic()

frame = [0] * 768

filename = [
   '01.bmp', '02.bmp', '03.bmp', '04.bmp', '05.bmp',
   '06.bmp', '07.bmp', '08.bmp', '09.bmp', '10.bmp',
   '11.bmp', '12.bmp', '13.bmp', '14.bmp', '15.bmp'
]
os.chdir('/snap')
if len(os.listdir()) == 0: #  no screenshots yet
    i=0
else:
    i = len(os.listdir()) - 1 #  there are already screenshots, continue

# ---MAIN LOOP---

while True:
    
    if time.monotonic() - last_time1 > 16:
        print( "RAM left: ",gc.mem_free() / 1024 * 1.000, " kb" )
    
    try:
        mlx.getFrame(frame)
    except ValueError:
        continue
    
    # some frame handeling with ulab.numpy
    npframe=np.array(frame) #  convert frame to np.array
    npframe[npframe < -100] = np.mean(npframe) # if there are bad pixels, set them to mean value
    min_t=np.min(npframe) #  find lowest temp. measured in current frame
    max_t=np.max(npframe) #  and the highest
    factor=last_color/(max_t-min_t) 
    inta=np.array((npframe-min_t)*factor,dtype=np.int8) #  normalize to int from 0 to last_color.

    # set color according to heatmap
#    int_bitmap=inta.reshape((24,32))
    index = 0
    for h in range(24):
        for w in range(32):
#            image_bitmap[h, w] = int_bitmap[h, w]
#            image_bitmap[h, w] = inta[w+(h<<5)]
#            image_bitmap[h, w] = inta[h*32+w]
            image_bitmap[h, w] = inta[index]
            index+=1
    # update the scale with min and max temp.
    min_string = "%0.1f" % (min_t)
    max_string = "%0.1f" % (max_t)
    min_label.x = 120 - (5 * len(min_string))
    max_label.x = 120 - (5 * len(max_string))
    min_label.text = min_string
    max_label.text = max_string

    display.refresh()

    #  take screenshot on button press
    if button.value == False:
        if i < len(filename):
            print(os.getcwd())
            print('capturing screen...')
            save_pixels('/shot.bmp', display, palette)
            print(os.listdir())
            os.rename('/shot.bmp', filename[i])
            i+=1
            print('done')
            print('screenshot(s) saved:', os.listdir())
            fs_stat = os.statvfs('/')
            print("space left: ", fs_stat[0] * fs_stat[3] / 1024 / 1024, " mb")
        else:
            print('enough screenshots')
