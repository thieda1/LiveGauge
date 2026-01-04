# iRacing Integration Guide

## Overview
This version of the Magden Dashboard supports three data sources:
1. **Mock Data** - Simulated data for testing
2. **OBD-II** - Real-time data from your vehicle
3. **iRacing** - Telemetry from iRacing simulator

## Features

### Multi-Source Support
- Automatic detection of available data sources
- Real-time switching between sources
- Data source indicator on main screen
- Optimized for Raspberry Pi 3B+ and Windows PC

### iRacing-Specific Features
- Direct telemetry from iRacing shared memory
- Live RPM, speed, temperatures
- Gear indicator
- Throttle, brake, and clutch percentages
- Oil pressure and manifold pressure
- Fuel level tracking
- Battery voltage monitoring

## Installation

### Windows (For iRacing)

#### 1. Install Python Dependencies
```bash
pip install pygame
pip install pyirsdk
```

#### 2. Install iRacing SDK
The `pyirsdk` library provides Python bindings to iRacing's shared memory.

```bash
pip install pyirsdk
```

#### 3. Optional: Install OBD Support (if you want both)
```bash
pip install obd
pip install pyserial
```

### Linux/Raspberry Pi (For OBD-II)

#### 1. Install Python Dependencies
```bash
sudo apt-get update
sudo apt-get install python3-pygame
pip3 install obd pyserial --break-system-packages
```

#### 2. For iRacing on Linux (Wine/Proton)
```bash
pip3 install pyirsdk --break-system-packages
```
Note: iRacing on Linux requires Wine/Proton and additional setup.

## Usage

### Running the Dashboard

#### On Windows (iRacing):
```bash
python MockInstrumentCluster_MultiSource.py
```

#### On Raspberry Pi (OBD-II):
```bash
python3 MockInstrumentCluster_MultiSource.py
```

### Switching Data Sources

The dashboard automatically detects available data sources on startup in this priority:
1. OBD-II (if adapter connected)
2. iRacing (if simulator running)
3. Mock data (fallback)

**Manual switching with keyboard:**
- **F1** - Switch to Mock data
- **F2** - Switch to OBD-II data (if available)
- **F3** - Switch to iRacing data (if available)

### Data Source Indicator

Top-left corner shows current source:
- **MOCK** (Yellow) - Simulated data
- **OBD-II** (Green) - Vehicle data
- **iRacing** (Blue) - Simulator data

## Screen Layout

### Screen 1 - Main Gauges
- RPM gauge (large, right side)
- Speed gauge (medium, right side)
- Engine Coolant Temperature (ECT)
- Intake Air Temperature (IAT)
- Battery voltage
- Fuel level bar

**iRacing mappings:**
- ECT → Water Temperature
- IAT → Oil Temperature
- All other gauges direct mapping

### Screen 2 - Additional Info

**For OBD-II:**
- Diagnostic Trouble Codes (DTCs)
- Clear DTC button

**For iRacing:**
- Gear indicator
- Throttle percentage
- Brake percentage
- Clutch percentage
- Oil pressure (PSI)
- Manifold pressure (PSI)

### Screen 3 - Engine Parameters
- Timing advance
- Engine load
- Throttle position
- MAF (Mass Air Flow)

**Note:** Some parameters like timing advance and MAF are not available in iRacing, so they show as 0 or approximate values.

## iRacing Telemetry Details

### Available Parameters
The dashboard accesses these iRacing telemetry points:

| Dashboard Label | iRacing Variable | Unit Conversion |
|----------------|------------------|-----------------|
| RPM | RPM | Direct |
| Speed | Speed | m/s → MPH |
| Water Temp | WaterTemp | °C → °F |
| Oil Temp | OilTemp | °C → °F |
| Fuel Level | FuelLevelPct | 0-1 → Percentage |
| Voltage | Voltage | Direct (V) |
| Throttle | Throttle | 0-1 → Percentage |
| Brake | Brake | 0-1 → Percentage |
| Clutch | Clutch | 0-1 → Percentage |
| Gear | Gear | Direct |
| Oil Pressure | OilPress | kPa → PSI |
| Manifold Pressure | ManifoldPress | kPa → PSI |

### Limitations
- **Timing Advance:** Not available in iRacing (shows 0)
- **MAF Sensor:** Not available in iRacing (shows 0)
- **DTCs:** Not applicable to simulators

## Logging

### Starting a Log
Click the **L** button in the bottom-right corner to start logging.

### Log Duration
- Automatic 5-minute recording after button press
- All parameters logged every second
- Buffer maintains last 5 minutes of data

### Log Files
Files are named by data source:
- `mock_log_YYYYMMDD_HHMMSS.csv`
- `obd_log_YYYYMMDD_HHMMSS.csv`
- `iracing_log_YYYYMMDD_HHMMSS.csv`

### Log Contents
Each log contains:
- Timestamp
- Timing advance
- Engine load
- Throttle position
- MAF
- RPM
- Speed
- Coolant temperature
- Intake temperature
- Fuel level
- Battery voltage

## Troubleshooting

### iRacing Not Detected

**Problem:** Dashboard shows "iRacing not available" when pressing F3

**Solutions:**
1. Ensure iRacing is running and you're in a car (not in menus)
2. Verify pyirsdk is installed: `pip list | grep pyirsdk`
3. Check iRacing telemetry is enabled in settings
4. Try running as administrator (Windows)

### iRacing Connection Lost

**Problem:** Dashboard switches to mock data during race

**Cause:** iRacing was closed or session ended

**Solution:** 
- Restart iRacing session
- Press F3 to reconnect

### No Telemetry Data

**Problem:** Connected to iRacing but all values show 0

**Solutions:**
1. Make sure you're driving (not in garage/menu)
2. Engine must be running for most readings
3. Some cars don't report all telemetry (check car specs)

### OBD and iRacing Together

**Problem:** Want to use both on same computer

**Solution:**
- Both can be installed simultaneously
- Dashboard prioritizes OBD if adapter connected
- Use F2/F3 to switch between them manually
- On Raspberry Pi, use OBD; on Windows PC, use iRacing

### Performance Issues

**On Windows:**
- Close unnecessary background applications
- iRacing + Dashboard together requires good CPU
- Consider running dashboard on separate screen/PC
- Reduce iRacing graphics settings if needed

**On Raspberry Pi:**
- OBD-II mode runs well on Pi 3B+
- Mock mode runs perfectly for testing
- iRacing mode not recommended on Pi (simulator won't run)

## Advanced Configuration

### Custom Refresh Rates
Edit the `TARGET_FPS` variable:
```python
TARGET_FPS = 30  # Change to 60 for smoother animation (higher CPU)
```

### Custom Max Values
Adjust gauge limits for different vehicles:
```python
# In draw_magden_gauge calls
draw_magden_gauge(surface, x, y, radius, rpm_value, 9000, "RPM", "")  # Changed from 7000
```

### Additional iRacing Parameters
Add more telemetry by extending the `iRacingConnection` class:
```python
def get_lap_time(self):
    if self.is_connected():
        return self.ir['LapLastLapTime']
    return 0
```

## Network Setup (Advanced)

### Remote Dashboard
You can run the dashboard on a separate device:

**Option 1: Raspberry Pi as Dashboard**
- Connect OBD adapter to car
- Display dashboard on car's screen

**Option 2: Stream iRacing Data**
- Run iRacing on gaming PC
- Stream telemetry to Raspberry Pi over network
- Requires custom network telemetry solution (not included)

### Multi-Monitor Setup
- Dashboard on second monitor while racing
- Perfect for sim rigs with multiple displays
- No performance impact with proper GPU

## Keyboard Shortcuts Summary

| Key | Action |
|-----|--------|
| ESC | Exit dashboard |
| F1 | Switch to Mock data |
| F2 | Switch to OBD-II data |
| F3 | Switch to iRacing data |
| 1 | Navigate to Screen 1 (Main) |
| 2 | Navigate to Screen 2 (Info/DTC) |
| 3 | Navigate to Screen 3 (Engine) |

## Racing Use Cases

### Practice Sessions
- Monitor fuel consumption rates
- Track temperature management
- Log data for analysis between sessions
- Compare different car setups

### Endurance Racing
- Critical for fuel strategy
- Temperature monitoring over long stints
- Tire pressure tracking (if added)
- Driver change telemetry comparison

### Hot Lapping
- Optimal RPM shift points
- Brake/throttle application data
- Corner speed analysis
- Consistency tracking

## Future Enhancements

Potential additions for iRacing support:
- [ ] Lap time display
- [ ] Split times
- [ ] Tire temperatures and pressure
- [ ] Brake temperatures
- [ ] Flag/position indicators
- [ ] Incident counter
- [ ] Fuel calculator
- [ ] Pit stop advisor
- [ ] Session time remaining
- [ ] Relative position to cars ahead/behind

## Credits

- OBD-II support via python-OBD library
- iRacing SDK via pyirsdk
- Optimized for Raspberry Pi 3B+
- Magden design aesthetic preserved

## Support

For issues or questions:
1. Check iRacing SDK documentation
2. Verify pyirsdk installation
3. Test with mock data first
4. Check iRacing forums for telemetry help

## License

Use freely for personal projects. Credit appreciated for the Magden style design.
