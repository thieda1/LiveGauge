import pygame
import math
import time
import obd  # Add real OBD-II support
import serial.tools.list_ports  # For port detection
import csv
from collections import deque
import datetime

# Initialize Pygame with optimizations for Raspberry Pi
pygame.init()

# Use hardware acceleration if available and set optimal flags for RPi
screen = pygame.display.set_mode((800, 480), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("OBD2 Dashboard - Magden Style")
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GRAY = (50, 50, 50)
DARK_GRAY = (30, 30, 30)
INNER_CIRCLE = (20, 20, 40)

# Font cache - load fonts once at startup
font_cache = {}

def get_font(size):
    """Cache fonts to avoid reloading from disk"""
    if size not in font_cache:
        try:
            font_cache[size] = pygame.font.Font("Race Sport.ttf", size)
        except:
            font_cache[size] = pygame.font.Font(None, size)  # Fallback to default
    return font_cache[size]

# Pre-load commonly used fonts
FONT_BIG = get_font(60)
FONT_MED = get_font(30)
FONT_SMALL = get_font(25)
FONT_TINY = get_font(20)

# Logging setup
logging_active = False
logging_start_time = None
logging_end_time = None
log_buffer = deque(maxlen=300)  # 5 minutes at 1-second intervals
log_file = None


# Mock OBD classes
class MockOBDValue:
    def __init__(self, magnitude):
        self.magnitude = magnitude


class MockOBDResponse:
    def __init__(self, value):
        self.value = value


class MockOBD:
    def __init__(self):
        self.connected = True
        self.dtcs = [("P0301", "Cylinder 1 Misfire Detected"), ("P0420", "Catalyst System Efficiency Below Threshold")]
        # Cache time values for mock data
        self._last_time = time.time()
        self._time_offset = 0

    def is_connected(self):
        return self.connected

    def query(self, cmd):
        # Use cached time value to reduce time.time() calls
        t = self._last_time + self._time_offset
        
        if cmd == "GET_DTC":
            return MockOBDResponse(self.dtcs)
        elif cmd == "CLEAR_DTC":
            self.dtcs = []
            return MockOBDResponse(True)
        elif cmd == "TIMING_ADVANCE":
            return MockOBDResponse(10 + 5 * math.sin(t * 0.5))
        elif cmd == "ENGINE_LOAD":
            return MockOBDResponse(50 + 25 * math.sin(t * 0.5))
        elif cmd == "THROTTLE_POS":
            return MockOBDResponse(30 + 20 * math.sin(t * 0.5))
        elif cmd == "MAF":
            return MockOBDResponse(100 + 50 * math.sin(t * 0.5))
        elif cmd == "RPM":
            return MockOBDResponse(4000 + 3000 * math.sin(t * 0.5))
        elif cmd == "SPEED":
            return MockOBDResponse(100 + 60 * math.sin(t * 0.5))
        elif cmd == "COOLANT_TEMP":
            return MockOBDResponse(185 + 35 * math.sin(t * 0.5))
        elif cmd == "INTAKE_TEMP":
            return MockOBDResponse(70 + 50 * math.sin(t * 0.5))
        elif cmd == "FUEL_LEVEL":
            return MockOBDResponse(50 + 50 * math.sin(t * 0.5))
        elif cmd == "ELM_VOLTAGE":
            return MockOBDResponse(13.5 + 2 * math.sin(t * 0.5))
        return MockOBDResponse(0)
    
    def update_time(self, current_time):
        """Update cached time value"""
        self._last_time = current_time


class MockCommands:
    RPM = "RPM"
    SPEED = "SPEED"
    COOLANT_TEMP = "COOLANT_TEMP"
    INTAKE_TEMP = "INTAKE_TEMP"
    ELM_VOLTAGE = "ELM_VOLTAGE"
    FUEL_LEVEL = "FUEL_LEVEL"
    GET_DTC = "GET_DTC"
    CLEAR_DTC = "CLEAR_DTC"
    TIMING_ADVANCE = "TIMING_ADVANCE"
    ENGINE_LOAD = "ENGINE_LOAD"
    THROTTLE_POS = "THROTTLE_POS"
    MAF = "MAF"


# OBD connection setup
def find_obd_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "usbserial" in port.device or "ttyUSB" in port.device or "ttyACM" in port.device:
            print(f"Found potential OBD port: {port.device}")
            return port.device
    print("No OBD port found. Falling back to mock data.")
    return None


port = find_obd_port()
if port:
    try:
        real_connection = obd.OBD(port)
    except:
        real_connection = None
else:
    real_connection = None

use_real_data = real_connection is not None and real_connection.is_connected()
if use_real_data:
    connection = real_connection
    commands = obd.commands
else:
    print("No OBD connection established. Using mock data.")
    connection = MockOBD()
    commands = MockCommands()


def get_value(cmd, mock_value, max_value, is_temp=False, is_speed=False):
    if use_real_data:
        try:
            response = connection.query(cmd)
            if response is not None and not response.is_null():
                value = response.value.magnitude
                if is_temp:
                    value = (value * 9 / 5) + 32
                elif is_speed:
                    value = value * 0.621371
                return min(value, max_value)
            return 0
        except Exception as e:
            print(f"Error querying {cmd}: {e}")
            return 0
    else:
        return mock_value


def log_parameters(timing, load, throttle, maf, rpm, speed, ect, iat, fuel, bat):
    timestamp = datetime.datetime.now().isoformat()
    data = {
        "timestamp": timestamp,
        "timing_advance": timing,
        "engine_load": load,
        "throttle_pos": throttle,
        "maf": maf,
        "rpm": rpm,
        "speed": speed,
        "coolant_temp": ect,
        "intake_temp": iat,
        "fuel_level": fuel,
        "battery_voltage": bat
    }
    log_buffer.append(data)
    if logging_active and log_file:
        writer = csv.DictWriter(log_file, fieldnames=data.keys())
        writer.writerow(data)


def start_logging():
    global logging_active, logging_start_time, logging_end_time, log_file
    if not logging_active:
        logging_active = True
        logging_start_time = time.time()
        logging_end_time = logging_start_time + 300  # 5 minutes after button press
        filename = f"obd_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        log_file = open(filename, 'w', newline='')
        writer = csv.DictWriter(log_file, fieldnames=[
            "timestamp", "timing_advance", "engine_load", "throttle_pos", "maf",
            "rpm", "speed", "coolant_temp", "intake_temp", "fuel_level", "battery_voltage"
        ])
        writer.writeheader()
        # Write buffered data
        for data in log_buffer:
            writer.writerow(data)
        print(f"Logging started, writing to {filename}")


# Pre-calculate commonly used values
TWO_PI = 2 * math.pi
HALF_PI = math.pi / 2


def draw_magden_gauge(surface, x, y, radius, value, max_value, label, units="", decimal_places=0):
    """Optimized gauge drawing with reduced pygame calls"""
    # Draw background circle and outline
    pygame.draw.circle(surface, INNER_CIRCLE, (x, y), radius + 5, 0)
    pygame.draw.circle(surface, BLUE, (x, y), radius + 2, 2)

    # Determine arc color based on RPM value (only for RPM gauge)
    arc_color = BLUE
    if label == "RPM":
        if value >= 6000:
            arc_color = RED
        elif value >= 4000:
            arc_color = YELLOW

    # Calculate arc parameters
    angle = (value / max_value) * 270
    start_angle = math.radians(230)
    end_angle = math.radians(250 - angle)
    inner_radius = radius - 5
    
    pygame.draw.arc(surface, arc_color, 
                    (x - inner_radius, y - inner_radius, inner_radius * 2, inner_radius * 2),
                    end_angle, start_angle, 15)

    # Draw value text
    value_text = FONT_BIG.render(f"{value:.{decimal_places}f}", True, WHITE)
    surface.blit(value_text, (x - value_text.get_width() // 2, y - 20))
    
    # Draw label and units
    label_text = FONT_SMALL.render(label, True, WHITE)
    surface.blit(label_text, (x - label_text.get_width() // 2, y + 30))
    
    if units:
        units_text = FONT_TINY.render(units, True, WHITE)
        surface.blit(units_text, (x - units_text.get_width() // 2, y + 55))


def draw_digital_box(surface, x, y, width, height, value, max_value, label, units="", decimal_places=1):
    """Optimized digital display box"""
    # Draw box background and outline
    box_rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
    pygame.draw.rect(surface, DARK_GRAY, box_rect, 0)
    pygame.draw.rect(surface, BLUE, box_rect, 2)

    # Draw value
    value_text = FONT_MED.render(f"{value:.{decimal_places}f}", True, WHITE)
    surface.blit(value_text, (x - value_text.get_width() // 2, y - 20))

    # Draw label and units
    label_units = f"{label} ({units})" if units else label
    label_text = FONT_TINY.render(label_units, True, WHITE)
    surface.blit(label_text, (x - label_text.get_width() // 2, y + 15))


def draw_button(surface, x, y, width, height, text, active=False):
    """Optimized button drawing"""
    color = BLUE if active else DARK_GRAY
    button_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, color, button_rect, 0)
    pygame.draw.rect(surface, WHITE, button_rect, 2)
    
    button_text = FONT_TINY.render(text, True, WHITE)
    surface.blit(button_text, 
                (x + (width - button_text.get_width()) // 2, 
                 y + (height - button_text.get_height()) // 2))


def draw_magden_cluster_screen1(surface, x, y):
    """Screen 1 - Main gauges"""
    pygame.draw.rect(surface, GRAY, (x - 400, y - 200, 800, 480), 0)
    
    # Logo
    logo_text = FONT_MED.render("magden", True, BLUE)
    surface.blit(logo_text, (x - logo_text.get_width() // 2, y - 190))

    # Get current time for all calculations
    t = time.time()
    
    # Update mock connection time if using mock data
    if not use_real_data:
        connection.update_time(t)
    
    # Calculate mock values once
    mock_rpm = 4000 + 3000 * math.sin(t * 0.5)
    mock_speed = 100 + 60 * math.sin(t * 0.5)
    mock_ect = 185 + 35 * math.sin(t * 0.5)
    mock_iat = 70 + 50 * math.sin(t * 0.5)
    mock_fuel = 50 + 50 * math.sin(t * 0.5)
    mock_bat = 13.5 + 2 * math.sin(t * 0.5)

    # Get values
    rpm_value = get_value(commands.RPM, mock_rpm, 7000)
    speed_value = get_value(commands.SPEED, mock_speed, 160, is_speed=True)
    ect_value = get_value(commands.COOLANT_TEMP, mock_ect, 250, is_temp=True)
    iat_value = get_value(commands.INTAKE_TEMP, mock_iat, 250, is_temp=True)
    fuel_value = get_value(commands.FUEL_LEVEL, mock_fuel, 100)
    bat_value = get_value(commands.ELM_VOLTAGE, mock_bat, 20)

    # Draw main gauges
    draw_magden_gauge(surface, x - 200, y, 90, rpm_value, 7000, "RPM")
    draw_magden_gauge(surface, x + 200, y, 90, speed_value, 160, "MPH")

    # Draw smaller info boxes
    box_width = 100
    box_height = 70
    spacing = 20
    
    start_x = x - (3 * box_width + 2 * spacing) // 2
    box_y = y + 140

    draw_digital_box(surface, start_x + box_width // 2, box_y, box_width, box_height, 
                    ect_value, 250, "ECT", "°F", 0)
    draw_digital_box(surface, start_x + box_width + spacing + box_width // 2, box_y, 
                    box_width, box_height, iat_value, 250, "IAT", "°F", 0)
    draw_digital_box(surface, start_x + 2 * (box_width + spacing) + box_width // 2, box_y, 
                    box_width, box_height, fuel_value, 100, "FUEL", "%", 0)

    # Battery voltage indicator
    bat_text = FONT_SMALL.render(f"BAT: {bat_value:.1f}V", True, WHITE)
    surface.blit(bat_text, (x - bat_text.get_width() // 2, y - 150))

    # Log button
    draw_button(surface, 770, 450, 25, 25, "L", active=logging_active)

    return rpm_value, speed_value, ect_value, iat_value, fuel_value, bat_value


def wrap_text(text, font, max_width):
    """Optimized text wrapping"""
    words = text.split(' ')
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines


def draw_magden_cluster_screen2(surface, x, y):
    """Screen 2 - DTC codes"""
    pygame.draw.rect(surface, GRAY, (x - 400, y - 200, 800, 480), 0)
    
    logo_text = FONT_MED.render("magden", True, BLUE)
    surface.blit(logo_text, (x - logo_text.get_width() // 2, y - 190))

    dtc_response = connection.query(commands.GET_DTC)
    dtcs = dtc_response.value

    title_text = FONT_SMALL.render("Diagnostic Trouble Codes", True, WHITE)
    surface.blit(title_text, (x - title_text.get_width() // 2, y - 100))

    if dtcs:
        y_offset = -50
        max_width = 700
        for code, desc in dtcs[:5]:
            dtc_text = f"{code}: {desc}"
            wrapped_lines = wrap_text(dtc_text, FONT_TINY, max_width)
            for line in wrapped_lines:
                text_surface = FONT_TINY.render(line, True, WHITE)
                surface.blit(text_surface, (x - 350, y + y_offset))
                y_offset += 30
            y_offset += 10
    else:
        no_dtc_text = FONT_TINY.render("No DTCs Found", True, WHITE)
        surface.blit(no_dtc_text, (x - no_dtc_text.get_width() // 2, y - 50))

    draw_button(surface, x - 75, y + 150, 150, 40, "Clear DTC")
    draw_button(surface, 770, 450, 25, 25, "L", active=logging_active)


def draw_magden_cluster_screen3(surface, x, y):
    """Screen 3 - Engine parameters"""
    pygame.draw.rect(surface, GRAY, (x - 400, y - 200, 800, 480), 0)
    
    logo_text = FONT_MED.render("magden", True, BLUE)
    surface.blit(logo_text, (x - logo_text.get_width() // 2, y - 190))

    title_text = FONT_SMALL.render("Engine Parameters", True, WHITE)
    surface.blit(title_text, (x - title_text.get_width() // 2, y - 100))

    t = time.time()
    mock_timing = 10 + 5 * math.sin(t * 0.5)
    mock_load = 50 + 25 * math.sin(t * 0.5)
    mock_throttle = 30 + 20 * math.sin(t * 0.5)
    mock_maf = 100 + 50 * math.sin(t * 0.5)

    timing_value = get_value(commands.TIMING_ADVANCE, mock_timing, 50)
    load_value = get_value(commands.ENGINE_LOAD, mock_load, 100)
    throttle_value = get_value(commands.THROTTLE_POS, mock_throttle, 100)
    maf_value = get_value(commands.MAF, mock_maf, 500)

    # Draw 2x2 grid of parameters
    box_width = 120
    box_height = 80
    h_spacing = 20
    v_spacing = 20
    grid_width = (2 * box_width) + h_spacing
    grid_height = (2 * box_height) + v_spacing
    grid_x = x - grid_width // 2
    grid_y = y - 50 + grid_height // 2

    draw_digital_box(surface, grid_x + box_width // 2, 
                    grid_y - box_height // 2 - v_spacing // 2, 
                    box_width, box_height, timing_value, 50, "TIMING", "°", 1)
    draw_digital_box(surface, grid_x + box_width + h_spacing + box_width // 2,
                    grid_y - box_height // 2 - v_spacing // 2, 
                    box_width, box_height, load_value, 100, "LOAD", "%", 1)
    draw_digital_box(surface, grid_x + box_width // 2, 
                    grid_y + box_height // 2 + v_spacing // 2, 
                    box_width, box_height, throttle_value, 100, "THRTL", "%", 1)
    draw_digital_box(surface, grid_x + box_width + h_spacing + box_width // 2,
                    grid_y + box_height // 2 + v_spacing // 2, 
                    box_width, box_height, maf_value, 500, "MAF", "g/s", 1)

    draw_button(surface, 770, 450, 25, 25, "L", active=logging_active)

    return timing_value, load_value, throttle_value, maf_value


# Main loop with optimizations
current_screen = 1
running = True
last_log_time = time.time()
last_frame_time = time.time()

# Target 30 FPS for better performance on RPi
TARGET_FPS = 30
FRAME_TIME = 1.0 / TARGET_FPS

# Cache parameter values between frames
cached_params = {
    'timing': 0, 'load': 0, 'throttle': 0, 'maf': 0,
    'rpm': 0, 'speed': 0, 'ect': 0, 'iat': 0,
    'fuel': 0, 'bat': 0
}

while running:
    frame_start = time.time()
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Screen navigation buttons
            if 340 <= mouse_pos[0] <= 365 and 40 <= mouse_pos[1] <= 65:
                current_screen = 1
            elif 390 <= mouse_pos[0] <= 415 and 40 <= mouse_pos[1] <= 65:
                current_screen = 2
            elif 440 <= mouse_pos[0] <= 465 and 40 <= mouse_pos[1] <= 65:
                current_screen = 3
            
            # Clear DTC button (Screen 2)
            elif current_screen == 2 and 325 <= mouse_pos[0] <= 475 and 350 <= mouse_pos[1] <= 390:
                try:
                    connection.query(commands.CLEAR_DTC)
                    print("DTCs cleared successfully")
                except Exception as e:
                    print(f"Error clearing DTCs: {e}")
            
            # Log button
            elif 770 <= mouse_pos[0] <= 795 and 450 <= mouse_pos[1] <= 475:
                start_logging()

    # Clear screen
    screen.fill(BLACK)

    # Update cached parameter values
    t = time.time()
    
    if current_screen == 1:
        rpm, speed, ect, iat, fuel, bat = draw_magden_cluster_screen1(screen, 400, 240)
        cached_params.update({
            'rpm': rpm, 'speed': speed, 'ect': ect,
            'iat': iat, 'fuel': fuel, 'bat': bat
        })
    elif current_screen == 2:
        draw_magden_cluster_screen2(screen, 400, 240)
    elif current_screen == 3:
        timing, load, throttle, maf = draw_magden_cluster_screen3(screen, 400, 240)
        cached_params.update({
            'timing': timing, 'load': load,
            'throttle': throttle, 'maf': maf
        })

    # Draw navigation buttons
    draw_button(screen, 340, 40, 25, 25, "1", active=(current_screen == 1))
    draw_button(screen, 390, 40, 25, 25, "2", active=(current_screen == 2))
    draw_button(screen, 440, 40, 25, 25, "3", active=(current_screen == 3))

    # Log data every second
    if t - last_log_time >= 1.0:
        # Get all current values for logging
        if current_screen != 1:
            # Refresh main screen values if not currently displayed
            mock_rpm = 4000 + 3000 * math.sin(t * 0.5)
            mock_speed = 100 + 60 * math.sin(t * 0.5)
            mock_ect = 185 + 35 * math.sin(t * 0.5)
            mock_iat = 70 + 50 * math.sin(t * 0.5)
            mock_fuel = 50 + 50 * math.sin(t * 0.5)
            mock_bat = 13.5 + 2 * math.sin(t * 0.5)
            
            cached_params['rpm'] = get_value(commands.RPM, mock_rpm, 7000)
            cached_params['speed'] = get_value(commands.SPEED, mock_speed, 160, is_speed=True)
            cached_params['ect'] = get_value(commands.COOLANT_TEMP, mock_ect, 250, is_temp=True)
            cached_params['iat'] = get_value(commands.INTAKE_TEMP, mock_iat, 250, is_temp=True)
            cached_params['fuel'] = get_value(commands.FUEL_LEVEL, mock_fuel, 100)
            cached_params['bat'] = get_value(commands.ELM_VOLTAGE, mock_bat, 20)
        
        if current_screen != 3:
            # Refresh engine params if not currently displayed
            mock_timing = 10 + 5 * math.sin(t * 0.5)
            mock_load = 50 + 25 * math.sin(t * 0.5)
            mock_throttle = 30 + 20 * math.sin(t * 0.5)
            mock_maf = 100 + 50 * math.sin(t * 0.5)
            
            cached_params['timing'] = get_value(commands.TIMING_ADVANCE, mock_timing, 50)
            cached_params['load'] = get_value(commands.ENGINE_LOAD, mock_load, 100)
            cached_params['throttle'] = get_value(commands.THROTTLE_POS, mock_throttle, 100)
            cached_params['maf'] = get_value(commands.MAF, mock_maf, 500)
        
        log_parameters(
            cached_params['timing'], cached_params['load'], 
            cached_params['throttle'], cached_params['maf'],
            cached_params['rpm'], cached_params['speed'], 
            cached_params['ect'], cached_params['iat'],
            cached_params['fuel'], cached_params['bat']
        )
        last_log_time = t

    # Stop logging after 5 minutes
    if logging_active and t > logging_end_time:
        logging_active = False
        if log_file:
            log_file.close()
            log_file = None
            print("Logging stopped")

    # Update display
    pygame.display.flip()
    
    # Frame rate control - maintain consistent 30 FPS
    frame_time = time.time() - frame_start
    if frame_time < FRAME_TIME:
        time.sleep(FRAME_TIME - frame_time)

# Cleanup
pygame.quit()
if use_real_data and real_connection:
    real_connection.close()
if log_file:
    log_file.close()
