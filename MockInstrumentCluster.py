import pygame
import math
import time
import obd  # Add real OBD-II support
import serial.tools.list_ports  # For port detection
import csv
from collections import deque
import datetime

# Initialize Pygame with hardware acceleration
pygame.init()
screen = pygame.display.set_mode((800, 480), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("OBD2 Dashboard - Magden Style")
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)  # Added for 5000 RPM threshold
RED = (255, 0, 0)  # Added for 6000 RPM threshold
GRAY = (50, 50, 50)
DARK_GRAY = (30, 30, 30)  # For button background

# Font cache to avoid reloading fonts every frame
font_cache = {}


def get_cached_font(size):
    """Load and cache fonts to improve performance"""
    if size not in font_cache:
        try:
            font_cache[size] = pygame.font.Font("Race Sport.ttf", size)
        except:
            font_cache[size] = pygame.font.Font(None, size)  # Fallback to default
    return font_cache[size]


# Pre-load commonly used fonts
FONT_60 = get_cached_font(60)
FONT_40 = get_cached_font(40)
FONT_30 = get_cached_font(30)
FONT_25 = get_cached_font(25)
FONT_20 = get_cached_font(20)
FONT_18 = get_cached_font(18)

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

    def is_connected(self):
        return self.connected

    def query(self, cmd):
        t = time.time()
        if cmd == "GET_DTC":
            return MockOBDResponse(self.dtcs)  # Return the DTC list directly
        elif cmd == "CLEAR_DTC":
            self.dtcs = []
            return MockOBDResponse(True)
        elif cmd == "TIMING_ADVANCE":
            return MockOBDResponse(10 + 5 * math.sin(t * 0.5))  # Mock timing advance
        elif cmd == "ENGINE_LOAD":
            return MockOBDResponse(50 + 25 * math.sin(t * 0.5))  # Mock engine load
        elif cmd == "THROTTLE_POS":
            return MockOBDResponse(30 + 20 * math.sin(t * 0.5))  # Mock throttle position
        elif cmd == "MAF":
            return MockOBDResponse(100 + 50 * math.sin(t * 0.5))  # Mock MAF
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


def draw_magden_gauge(surface, x, y, radius, value, max_value, label, units="", decimal_places=0):
    pygame.draw.circle(surface, (20, 20, 40), (x, y), radius + 5, 0)  # Dark inner fill
    pygame.draw.circle(surface, BLUE, (x, y), radius + 2, 2)  # Neon outline

    # Determine arc color based on RPM value (only for RPM gauge)
    arc_color = BLUE
    if label == "RPM":
        if value >= 6000:
            arc_color = RED
        elif value >= 4000:
            arc_color = YELLOW

    angle = (value / max_value) * 270  # Proportion of 270° range
    start_angle = math.radians(230)  # Start at bottom left
    end_angle = math.radians(250 - angle)  # Decrease angle for counterclockwise sweep
    inner_radius = radius - 5  # Bar follows inside edge
    pygame.draw.arc(surface, arc_color, (x - inner_radius, y - inner_radius, inner_radius * 2, inner_radius * 2),
                    end_angle, start_angle, 15)  # Reverse order for counterclockwise

    value_text = FONT_60.render(f"{value:.{decimal_places}f}", True, WHITE)
    surface.blit(value_text, (x - value_text.get_width() // 2, y - 20))
    label_text = FONT_25.render(f"{label}", True, WHITE)
    units_text = FONT_25.render(f"{units}", True, WHITE)
    surface.blit(label_text, (x - label_text.get_width() // 2, y + 30))
    surface.blit(units_text, (x - units_text.get_width() // 2, y + 70))


def draw_magden_horizontal_bar(surface, x, y, width, height, value, max_value, label, units=""):
    pygame.draw.rect(surface, (20, 20, 40), (x - width // 2, y - height // 2, width, height))
    pygame.draw.rect(surface, BLUE, (x - width // 2, y - height // 2, width, height), 2)
    fill_width = (value / max_value) * (width - 10)
    fill_x = x - width // 2 + 5
    pygame.draw.rect(surface, BLUE, (fill_x, y - height // 2 + 5, fill_width, height - 10))
    tick_positions = [0, 0.25, 0.5, 0.75, 1]
    for tick in tick_positions:
        tick_x = x - width // 2 + 5 + (tick * (width - 10))
        pygame.draw.line(surface, WHITE, (tick_x, y + height // 2 + 5), (tick_x, y + height // 2 + 15), 2)
    label_text = FONT_25.render(f"{label}", True, WHITE)
    units_text = FONT_25.render(f"{units}", True, WHITE)
    surface.blit(label_text, (x - label_text.get_width() // 2, y + height // 2 + 20))
    surface.blit(units_text, (x - units_text.get_width() // 2, y + height // 2 + 45))


def draw_button(surface, x, y, width, height, text, active=False):
    color = BLUE if active else DARK_GRAY
    pygame.draw.rect(surface, color, (x, y, width, height))
    pygame.draw.rect(surface, WHITE, (x, y, width, height), 2)
    text_surface = FONT_18.render(text, True, WHITE)
    surface.blit(text_surface, (x + (width - text_surface.get_width()) // 2,
                                y + (height - text_surface.get_height()) // 2))


def draw_digital_box(surface, x, y, width, height, value, max_value, label, units="", decimal_places=1):
    pygame.draw.rect(surface, (20, 20, 40), (x - width // 2, y - height // 2, width, height))
    pygame.draw.rect(surface, BLUE, (x - width // 2, y - height // 2, width, height), 2)
    value_text = FONT_40.render(f"{value:.{decimal_places}f}", True, WHITE)
    label_text = FONT_20.render(f"{label}", True, WHITE)
    units_text = FONT_20.render(f"{units}", True, WHITE)
    surface.blit(value_text, (x - value_text.get_width() // 2, y - 10))
    surface.blit(label_text, (x - label_text.get_width() // 2, y - 30))
    surface.blit(units_text, (x - units_text.get_width() // 2, y + 20))


# Screen 1
def draw_magden_cluster_screen1(surface, x, y):
    pygame.draw.rect(surface, GRAY, (x - 400, y - 200, 800, 480), 0)
    logo_text = FONT_30.render("magden", True, BLUE)
    surface.blit(logo_text, (x - logo_text.get_width() // 2, y - 190))

    t = time.time()
    mock_iat = 70 + 50 * math.sin(t * 0.5)
    mock_fuel = 50 + 50 * math.sin(t * 0.5)
    mock_bat = 13.5 + 2 * math.sin(t * 0.5)
    mock_speed = 100 + 60 * math.sin(t * 0.5)
    mock_ect = 185 + 35 * math.sin(t * 0.5)
    mock_rpm = 4000 + 3000 * math.sin(t * 0.5)

    iat_value = get_value(commands.INTAKE_TEMP, mock_iat, 250, is_temp=True)
    fuel_value = get_value(commands.FUEL_LEVEL if use_real_data else commands.FUEL_LEVEL, mock_fuel, 100)
    bat_value = get_value(commands.ELM_VOLTAGE if use_real_data else commands.ELM_VOLTAGE, mock_bat, 20)
    speed_value = get_value(commands.SPEED, mock_speed, 160, is_speed=True)
    ect_value = get_value(commands.COOLANT_TEMP, mock_ect, 250, is_temp=True)
    rpm_value = get_value(commands.RPM, mock_rpm, 7000)

    draw_magden_gauge(surface, x - 290, y - 90, 100, iat_value, 150, "IAT", "°F")
    draw_magden_horizontal_bar(surface, x - 0, y + 220, 200, 25, fuel_value, 100, "FUEL", "")
    draw_magden_gauge(surface, x - 120, y + 40, 100, bat_value, 20, "BAT", "V", decimal_places=1)
    draw_magden_gauge(surface, x - 290, y + 170, 100, ect_value, 250, "ECT", "°F")
    draw_magden_gauge(surface, x + 240, y - 40, 150, rpm_value, 7000, "RPM", "")
    draw_magden_gauge(surface, x + 240, y + 147.5, 125, speed_value, 160, "SPD", "MPH")

    # Draw Log button in bottom-right corner as a small square
    draw_button(surface, 770, 450, 25, 25, "L", active=logging_active)

    return rpm_value, speed_value, ect_value, iat_value, fuel_value, bat_value


# Helper function to wrap text
def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = []
    current_width = 0

    for word in words:
        test_line = ' '.join(current_line + [word])
        # Optimized: use font.size() instead of rendering
        text_width = font.size(test_line)[0]
        if text_width <= max_width:
            current_line.append(word)
            current_width = text_width
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_width = font.size(word)[0]

    if current_line:
        lines.append(' '.join(current_line))

    return lines


# Screen 2 (formerly Screen 4)
def draw_magden_cluster_screen2(surface, x, y):
    pygame.draw.rect(surface, GRAY, (x - 400, y - 200, 800, 480), 0)
    logo_text = FONT_30.render("magden", True, BLUE)
    surface.blit(logo_text, (x - logo_text.get_width() // 2, y - 190))

    dtc_response = connection.query(commands.GET_DTC)
    dtcs = dtc_response.value if use_real_data and dtc_response is not None else connection.query(
        commands.GET_DTC).value

    title_text = FONT_25.render("Diagnostic Trouble Codes", True, WHITE)
    surface.blit(title_text, (x - title_text.get_width() // 2, y - 100))

    if dtcs:  # empty lists are False-y
        y_offset = -50
        max_width = 700  # Limit text width to fit within screen
        for code, desc in dtcs[:5]:
            dtc_text = f"{code}: {desc}"
            wrapped_lines = wrap_text(dtc_text, FONT_20, max_width)
            for line in wrapped_lines:
                text_surface = FONT_20.render(line, True, WHITE)
                surface.blit(text_surface, (x - 350, y + y_offset))
                y_offset += 30
            y_offset += 10  # Extra spacing between DTC entries
    else:
        no_dtc_text = FONT_20.render("No DTCs Found", True, WHITE)
        surface.blit(no_dtc_text, (x - no_dtc_text.get_width() // 2, y - 50))

    # Draw Clear DTC button
    draw_button(surface, x - 75, y + 150, 150, 40, "Clear DTC")

    # Draw Log button in bottom-right corner as a small square
    draw_button(surface, 770, 450, 25, 25, "L", active=logging_active)

    # Return dummy values for parameters not displayed on this screen
    return 0, 0, 0, 0, 0, 0


# Screen 3 (formerly Screen 5)
def draw_magden_cluster_screen3(surface, x, y):
    pygame.draw.rect(surface, GRAY, (x - 400, y - 200, 800, 480), 0)
    logo_text = FONT_30.render("magden", True, BLUE)
    surface.blit(logo_text, (x - logo_text.get_width() // 2, y - 190))

    title_text = FONT_25.render("Engine Parameters", True, WHITE)
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

    # Draw digital boxes in a tightened 2x2 grid, centered and moved down
    box_width = 120
    box_height = 80
    h_spacing = 20  # Reduced horizontal spacing
    v_spacing = 20  # Reduced vertical spacing
    grid_width = (2 * box_width) + h_spacing
    grid_height = (2 * box_height) + v_spacing
    grid_x = x - grid_width // 2
    grid_y = y - 50 + grid_height // 2  # Moved down to clear title

    draw_digital_box(surface, grid_x + box_width // 2, grid_y - box_height // 2 - v_spacing // 2, box_width, box_height,
                     timing_value, 50, "TIMING", "°", 1)
    draw_digital_box(surface, grid_x + box_width + h_spacing + box_width // 2,
                     grid_y - box_height // 2 - v_spacing // 2, box_width, box_height, load_value, 100, "LOAD", "%", 1)
    draw_digital_box(surface, grid_x + box_width // 2, grid_y + box_height // 2 + v_spacing // 2, box_width, box_height,
                     throttle_value, 100, "THRTL", "%", 1)
    draw_digital_box(surface, grid_x + box_width + h_spacing + box_width // 2,
                     grid_y + box_height // 2 + v_spacing // 2, box_width, box_height, maf_value, 500, "MAF", "g/s", 1)

    # Draw Log button in bottom-right corner as a small square
    draw_button(surface, 770, 450, 25, 25, "L", active=logging_active)

    return 0, 0, 0, 0, 0, 0, timing_value, load_value, throttle_value, maf_value


# Main loop
current_screen = 1
running = True
last_log_time = time.time()

# Target 30 FPS for better Raspberry Pi performance
TARGET_FPS = 30

while running:
    frame_start = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if 340 <= mouse_pos[0] <= 370 and 40 <= mouse_pos[1] <= 65:
                current_screen = 1
            if 390 <= mouse_pos[0] <= 460 and 40 <= mouse_pos[1] <= 65:
                current_screen = 2
            if 440 <= mouse_pos[0] <= 550 and 40 <= mouse_pos[1] <= 65:
                current_screen = 3
            if current_screen == 2 and 325 <= mouse_pos[0] <= 475 and 350 <= mouse_pos[1] <= 390:
                try:
                    connection.query(commands.CLEAR_DTC)
                    print("DTCs cleared successfully")
                except Exception as e:
                    print(f"Error clearing DTCs: {e}")
            if 775 <= mouse_pos[0] <= 800 and 455 <= mouse_pos[1] <= 480:
                start_logging()

    screen.fill(BLACK)

    # Collect parameters for logging
    t = time.time()
    mock_timing = 10 + 5 * math.sin(t * 0.5)
    mock_load = 50 + 25 * math.sin(t * 0.5)
    mock_throttle = 30 + 20 * math.sin(t * 0.5)
    mock_maf = 100 + 50 * math.sin(t * 0.5)
    mock_iat = 70 + 50 * math.sin(t * 0.5)
    mock_fuel = 50 + 50 * math.sin(t * 0.5)
    mock_bat = 13.5 + 2 * math.sin(t * 0.5)
    mock_speed = 100 + 60 * math.sin(t * 0.5)
    mock_ect = 185 + 35 * math.sin(t * 0.5)
    mock_rpm = 4000 + 3000 * math.sin(t * 0.5)

    timing_value = get_value(commands.TIMING_ADVANCE, mock_timing, 50)
    load_value = get_value(commands.ENGINE_LOAD, mock_load, 100)
    throttle_value = get_value(commands.THROTTLE_POS, mock_throttle, 100)
    maf_value = get_value(commands.MAF, mock_maf, 500)
    iat_value = get_value(commands.INTAKE_TEMP, mock_iat, 250, is_temp=True)
    fuel_value = get_value(commands.FUEL_LEVEL if use_real_data else commands.FUEL_LEVEL, mock_fuel, 100)
    bat_value = get_value(commands.ELM_VOLTAGE if use_real_data else commands.ELM_VOLTAGE, mock_bat, 20)
    speed_value = get_value(commands.SPEED, mock_speed, 160, is_speed=True)
    ect_value = get_value(commands.COOLANT_TEMP, mock_ect, 250, is_temp=True)
    rpm_value = get_value(commands.RPM, mock_rpm, 7000)

    # Log data every second
    if time.time() - last_log_time >= 1.0:
        log_parameters(timing_value, load_value, throttle_value, maf_value, rpm_value, speed_value, ect_value,
                       iat_value, fuel_value, bat_value)
        last_log_time = time.time()

    # Stop logging after 5 minutes post-button press
    if logging_active and time.time() > logging_end_time:
        logging_active = False
        if log_file:
            log_file.close()
            log_file = None
            print("Logging stopped")

    if current_screen == 1:
        draw_magden_cluster_screen1(screen, 400, 200)
    elif current_screen == 2:
        draw_magden_cluster_screen2(screen, 400, 200)
    elif current_screen == 3:
        draw_magden_cluster_screen3(screen, 400, 200)

    draw_button(screen, 340, 40, 25, 25, "1", active=(current_screen == 1))
    draw_button(screen, 390, 40, 25, 25, "2", active=(current_screen == 2))
    draw_button(screen, 440, 40, 25, 25, "3", active=(current_screen == 3))

    pygame.display.flip()

    # Frame rate control - maintain consistent 30 FPS
    elapsed = time.time() - frame_start
    target_frame_time = 1.0 / TARGET_FPS
    if elapsed < target_frame_time:
        time.sleep(target_frame_time - elapsed)

pygame.quit()
if use_real_data:
    real_connection.close()
if log_file:
    log_file.close()