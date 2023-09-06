# MLX90640-ThermalCam with Raspberry Pico and TFT Display

This project is my CircuitPython implementation of thermal camera based on rasperry pico and the mlx90640 24x32 thermal array.

After having a hard time trying to find working CircuitPython examples for MLX90640 I decided to create one myself and share it. 
My code is an updated modification based on ![the code of David Glaude](https://github.com/dglaude/circuitpython_phat_on_pico/blob/main/mlx90640_240x240.py). 

![](https://raw.githubusercontent.com/FamosoMocoso/mlx90640_thermal-cam_circuitpython/main/highfive.bmp)

**What I changed/added:**
  - Code updated to work with CircuitPython 8+ and Libraries
  - added a function to handle bad/faulty pixels
  - added the possibility to take screenshots
  - Reduced the required hardware to:
      - Rasperry Pico,
      - MLX90640,
      - 128x160 TFT LCD Display (ST7735R)
      - and optional 1 Push-Button

# Dependencies

The code depends on the following Libraries:
* adafruit_display_text
* adafruit_bitmapsaver
* adafruit_mlx90640
* adafruit_st7735r
* simpleio

# Wiring
## 128x160 TFT-LCD Display (ST7735r)

| DISP  | PICO |
|-------|------|
| MOSI  | GP11 |
| CLK   | GP10 |
| DC    | GP16 |
| RESET | GP17 |
| CS    | GP18 |

## MLX90640
| MLX  | PICO  |
|------|-------|
| VIN  | 3v3   |
| GND  | GND   |
| SCL  | GP21  |
| SDA  | GP20  |
| (PS) | (GND) |

## Storage-Switch and Button
|      |     |                           |
|------|-----|---------------------------|
| GP0  | GND | JUMPER FOR STORAGE STATE  |
| GP22 | GND | BUTTON TO TAKE SCREENSHOT |  
