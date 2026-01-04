import pygame
import math
import time
import csv
from collections import deque
import datetime

# iRacing SDK import
try:
    import irsdk
    IRACING_AVAILABLE = True
except ImportError:
    IRACING_AVAILABLE = False
    print("ERROR: iRacing SDK not available. Please install with: pip install pyirsdk")
    print("This version requires iRacing support.")
    import sys
    sys.exit(1)

# Initialize Pygame with hardware acceleration
pygame.init()
screen = pygame.display.set_mode((800, 480), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("Magden Dashboard - iRacing")
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (50, 50, 50)
DARK_GRAY = (30, 30, 30)

# Font cache
font_cache = {}

def get_cached_font(size):
    if size not in font_cache:
        try:
            font_cache[size] = pygame.font.Font("Race Sport.ttf", size)
        except:
            font_cache[size] = pygame.font.Font(None, size)
    return font_cache[size]

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
log_buffer = deque(maxlen=300)
log_file = None


# iRacing connection class
class iRacingConnection:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.connected = False
        self.last_check = 0
        self.check_interval = 1.0  # Check connection every second
        print("Attempting to connect to iRacing...")
        self.reconnect()
    
    def reconnect(self):
        try:
            self.connected = self.ir.startup()
            if self.connected:
                print("✓ Connected to iRacing!")
            else:
                print("✗ iRacing not detected. Make sure the simulator is running and you're in a car.")
        except Exception as e:
            print(f"Connection error: {e}")
            self.connected = False
        self.last_check = time.time()
    
    def is_connected(self):
        # Periodic connection check
        if time.time() - self.last_check > self.check_interval:
            if self.ir and self.connected:
                if not self.ir.is_initialized or not self.ir.is_connected:
                    print("iRacing connection lost, attempting reconnect...")
                    self.reconnect()
            elif not self.connected:
                self.reconnect()
            self.last_check = time.time()
        return self.connected
    
    def get_rpm(self):
        if self.is_connected():
            rpm = self.ir['RPM']
            return rpm if rpm is not None else 0
        return 0
    
    def get_speed(self):
        if self.is_connected():
            speed_ms = self.ir['Speed']
            if speed_ms is not None:
                return speed_ms * 2.23694  # m/s to MPH
        return 0
    
    def get_water_temp(self):
        if self.is_connected():
            temp_c = self.ir['WaterTemp']
            if temp_c is not None:
                return (temp_c * 9/5) + 32  # C to F
        return 0
    
    def get_oil_temp(self):
        if self.is_connected():
            temp_c = self.ir['OilTemp']
            if temp_c is not None:
                return (temp_c * 9/5) + 32
        return 0
    
    def get_fuel_level(self):
        if self.is_connected():
            fuel_pct = self.ir['FuelLevelPct']
            if fuel_pct is not None:
                return fuel_pct * 100
        return 0
    
    def get_voltage(self):
        if self.is_connected():
            voltage = self.ir['Voltage']
            return voltage if voltage is not None else 13.5
        return 13.5
    
    def get_throttle(self):
        if self.is_connected():
            throttle = self.ir['Throttle']
            return throttle * 100 if throttle is not None else 0
        return 0
    
    def get_brake(self):
        if self.is_connected():
            brake = self.ir['Brake']
            return brake * 100 if brake is not None else 0
        return 0
    
    def get_clutch(self):
        if self.is_connected():
            clutch = self.ir['Clutch']
            return clutch * 100 if clutch is not None else 0
        return 0
    
    def get_gear(self):
        if self.is_connected():
            gear = self.ir['Gear']
            return gear if gear is not None else 0
        return 0
    
    def get_oil_pressure(self):
        if self.is_connected():
            pressure = self.ir['OilPress']
            if pressure is not None:
                return pressure * 0.145038  # kPa to PSI
        return 0
    
    def get_manifold_pressure(self):
        if self.is_connected():
            pressure = self.ir['ManifoldPress']
            if pressure is not None:
                return pressure * 0.145038  # kPa to PSI
        return 0
    
    def get_session_time(self):
        if self.is_connected():
            session_time = self.ir['SessionTime']
            return session_time if session_time is not None else 0
        return 0
    
    def get_lap_time(self):
        if self.is_connected():
            lap_time = self.ir['LapLastLapTime']
            return lap_time if lap_time is not None else 0
        return 0


# Initialize iRacing connection
ir_connection = iRacingConnection()


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
        logging_end_time = logging_start_time + 300
        filename = f"iracing_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        log_file = open(filename, 'w', newline='')
        writer = csv.DictWriter(log_file, fieldnames=[
            "timestamp", "timing_advance", "engine_load", "throttle_pos", "maf",
            "rpm", "speed", "coolant_temp", "intake_temp", "fuel_level", "battery_voltage"
        ])
        writer.writeheader()
        for data in log_buffer:
            writer.writerow(data)
        print(f"Logging started: {filename}")


def draw_magden_gauge(surface, x, y, radius, value, max_value, label, units="", decimal_places=0):
    pygame.draw.circle(surface, (20, 20, 40), (x, y), radius + 5, 0)
    pygame.draw.circle(surface, BLUE, (x, y), radius + 2, 2)

    arc_color = BLUE
    if label == "RPM":
        if value >= 6000:
            arc_color = RED
        elif value >= 4000:
            arc_color = YELLOW

    angle = (value / max_value) * 270
    start_angle = math.radians(230)
    end_angle = math.radians(250 - angle)
    inner_radius = radius - 5
    pygame.draw.arc(surface, arc_color, (x - inner_radius, y - inner_radius, inner_radius * 2, inner_radius * 2),
                    end_angle, start_angle, 15)

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


def draw_magden_cluster_screen1(surface, x, y):
    pygame.draw.rect(surface, GRAY, (x - 400, y - 200, 800, 480), 0)
    logo_text = FONT_30.render("magden", True, BLUE)
    surface.blit(logo_text, (x - logo_text.get_width() // 2, y - 190))
    
    # Connection status
    if ir_connection.is_connected():
        status_text = FONT_18.render("iRacing", True, GREEN)
    else:
        status_text = FONT_18.render("NO CONNECTION", True, RED)
    surface.blit(status_text, (10, 10))

    iat_value = ir_connection.get_oil_temp()
    fuel_value = ir_connection.get_fuel_level()
    bat_value = ir_connection.get_voltage()
    speed_value = ir_connection.get_speed()
    ect_value = ir_connection.get_water_temp()
    rpm_value = ir_connection.get_rpm()

    draw_magden_gauge(surface, x - 290, y - 90, 100, iat_value, 300, "OIL", "°F")
    draw_magden_horizontal_bar(surface, x - 0, y + 220, 200, 25, fuel_value, 100, "FUEL", "%")
    draw_magden_gauge(surface, x - 120, y + 40, 100, bat_value, 20, "BAT", "V", decimal_places=1)
    draw_magden_gauge(surface, x - 290, y + 170, 100, ect_value, 300, "WATER", "°F")
    draw_magden_gauge(surface, x + 240, y - 40, 150, rpm_value, 10000, "RPM", "")
    draw_magden_gauge(surface, x + 240, y + 147.5, 125, speed_value, 200, "SPD", "MPH")

    draw_button(surface, 770, 450, 25, 25, "L", active=logging_active)

    return rpm_value, speed_value, ect_value, iat_value, fuel_value, bat_value


def draw_magden_cluster_screen2(surface, x, y):
    pygame.draw.rect(surface, GRAY, (x - 400, y - 200, 800, 480), 0)
    logo_text = FONT_30.render("magden", True, BLUE)
    surface.blit(logo_text, (x - logo_text.get_width() // 2, y - 190))

    title_text = FONT_25.render("iRacing Telemetry", True, WHITE)
    surface.blit(title_text, (x - title_text.get_width() // 2, y - 100))
    
    # Get telemetry
    gear = ir_connection.get_gear()
    throttle = ir_connection.get_throttle()
    brake = ir_connection.get_brake()
    clutch = ir_connection.get_clutch()
    oil_press = ir_connection.get_oil_pressure()
    manifold = ir_connection.get_manifold_pressure()
    
    # Grid layout
    box_width = 120
    box_height = 70
    spacing = 20
    
    grid_width = 3 * box_width + 2 * spacing
    grid_x = x - grid_width // 2
    
    # Row 1
    row1_y = y - 50
    draw_digital_box(surface, grid_x + box_width // 2, row1_y, box_width, box_height,
                    gear, 6, "GEAR", "", 0)
    draw_digital_box(surface, grid_x + box_width + spacing + box_width // 2, row1_y, 
                    box_width, box_height, throttle, 100, "THRTL", "%", 0)
    draw_digital_box(surface, grid_x + 2 * (box_width + spacing) + box_width // 2, row1_y,
                    box_width, box_height, brake, 100, "BRAKE", "%", 0)
    
    # Row 2
    row2_y = y + 40
    draw_digital_box(surface, grid_x + box_width // 2, row2_y, box_width, box_height,
                    clutch, 100, "CLUTCH", "%", 0)
    draw_digital_box(surface, grid_x + box_width + spacing + box_width // 2, row2_y,
                    box_width, box_height, oil_press, 150, "OIL", "PSI", 0)
    draw_digital_box(surface, grid_x + 2 * (box_width + spacing) + box_width // 2, row2_y,
                    box_width, box_height, manifold, 50, "MAP", "PSI", 1)

    draw_button(surface, 770, 450, 25, 25, "L", active=logging_active)

    return 0, 0, 0, 0, 0, 0


def draw_magden_cluster_screen3(surface, x, y):
    pygame.draw.rect(surface, GRAY, (x - 400, y - 200, 800, 480), 0)
    logo_text = FONT_30.render("magden", True, BLUE)
    surface.blit(logo_text, (x - logo_text.get_width() // 2, y - 190))

    title_text = FONT_25.render("Engine Parameters", True, WHITE)
    surface.blit(title_text, (x - title_text.get_width() // 2, y - 100))

    # Get values (some approximate)
    timing_value = 0  # Not available in iRacing
    load_value = ir_connection.get_throttle()  # Approximate with throttle
    throttle_value = ir_connection.get_throttle()
    maf_value = 0  # Not available in iRacing

    box_width = 120
    box_height = 80
    h_spacing = 20
    v_spacing = 20
    grid_width = (2 * box_width) + h_spacing
    grid_height = (2 * box_height) + v_spacing
    grid_x = x - grid_width // 2
    grid_y = y - 50 + grid_height // 2

    draw_digital_box(surface, grid_x + box_width // 2, grid_y - box_height // 2 - v_spacing // 2, 
                     box_width, box_height, timing_value, 50, "TIMING", "°", 1)
    draw_digital_box(surface, grid_x + box_width + h_spacing + box_width // 2,
                     grid_y - box_height // 2 - v_spacing // 2, box_width, box_height, 
                     load_value, 100, "LOAD", "%", 1)
    draw_digital_box(surface, grid_x + box_width // 2, grid_y + box_height // 2 + v_spacing // 2, 
                     box_width, box_height, throttle_value, 100, "THRTL", "%", 1)
    draw_digital_box(surface, grid_x + box_width + h_spacing + box_width // 2,
                     grid_y + box_height // 2 + v_spacing // 2, box_width, box_height, 
                     maf_value, 500, "MAF", "g/s", 1)

    draw_button(surface, 770, 450, 25, 25, "L", active=logging_active)

    return 0, 0, 0, 0, 0, 0, timing_value, load_value, throttle_value, maf_value


# Main loop
current_screen = 1
running = True
last_log_time = time.time()
TARGET_FPS = 60  # Higher FPS for racing sim

print("\n=== iRacing Dashboard Started ===")
print("Make sure iRacing is running and you're in a car")
print("Press ESC to exit")
print("================================\n")

while running:
    frame_start = time.time()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                # Manual reconnect
                print("Manual reconnect requested...")
                ir_connection.reconnect()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if 340 <= mouse_pos[0] <= 370 and 40 <= mouse_pos[1] <= 65:
                current_screen = 1
            if 390 <= mouse_pos[0] <= 460 and 40 <= mouse_pos[1] <= 65:
                current_screen = 2
            if 440 <= mouse_pos[0] <= 550 and 40 <= mouse_pos[1] <= 65:
                current_screen = 3
            if 775 <= mouse_pos[0] <= 800 and 455 <= mouse_pos[1] <= 480:
                start_logging()

    screen.fill(BLACK)

    # Get all telemetry
    timing_value = 0
    load_value = ir_connection.get_throttle()
    throttle_value = ir_connection.get_throttle()
    maf_value = 0
    iat_value = ir_connection.get_oil_temp()
    fuel_value = ir_connection.get_fuel_level()
    bat_value = ir_connection.get_voltage()
    speed_value = ir_connection.get_speed()
    ect_value = ir_connection.get_water_temp()
    rpm_value = ir_connection.get_rpm()

    # Log data every second
    if time.time() - last_log_time >= 1.0:
        log_parameters(timing_value, load_value, throttle_value, maf_value, rpm_value, speed_value, ect_value,
                       iat_value, fuel_value, bat_value)
        last_log_time = time.time()

    # Stop logging after 5 minutes
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
    
    elapsed = time.time() - frame_start
    target_frame_time = 1.0 / TARGET_FPS
    if elapsed < target_frame_time:
        time.sleep(target_frame_time - elapsed)

pygame.quit()
if log_file:
    log_file.close()

print("\nDashboard closed.")
