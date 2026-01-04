# Magden Dashboard - Version Comparison Guide

## Available Versions

### 1. Dashboard_OBD_Only.py
**Purpose:** Dedicated OBD-II vehicle telemetry
**Best For:** Raspberry Pi installation in actual vehicles

**Features:**
- ✅ OBD-II adapter support
- ✅ Mock data fallback for testing
- ✅ Diagnostic Trouble Codes (DTCs)
- ✅ Clear DTC functionality
- ✅ All engine parameters
- ✅ Optimized for Raspberry Pi 3B+ (30 FPS)
- ❌ No iRacing support

**Installation:**
```bash
# Raspberry Pi
sudo apt-get install python3-pygame
pip3 install obd pyserial --break-system-packages
python3 Dashboard_OBD_Only.py
```

**Use Cases:**
- Daily driver telemetry display
- Track day data logging
- Tuning and diagnostics
- Engine monitoring
- Permanent car installation

---

### 2. Dashboard_iRacing_Only.py
**Purpose:** Dedicated iRacing simulator telemetry
**Best For:** Windows PC sim racing setups

**Features:**
- ✅ Full iRacing telemetry integration
- ✅ Real-time gear, throttle, brake, clutch
- ✅ Oil and manifold pressure
- ✅ Auto-reconnect functionality
- ✅ Higher refresh rate (60 FPS)
- ❌ No OBD-II support
- ❌ No mock data fallback

**Installation:**
```bash
# Windows
pip install pygame pyirsdk
python Dashboard_iRacing_Only.py
```

**Use Cases:**
- Sim racing rigs
- Practice session monitoring
- Race telemetry display
- Endurance racing fuel management
- Secondary monitor display

---

### 3. MockInstrumentCluster_MultiSource.py
**Purpose:** Universal dashboard with all data sources
**Best For:** Dual-purpose setups or testing

**Features:**
- ✅ OBD-II support
- ✅ iRacing support
- ✅ Mock data support
- ✅ Switch between sources with F1/F2/F3
- ✅ Auto-detection of available sources
- ✅ Visual indicator of active source
- ⚠️ Larger file size (includes all dependencies)

**Installation:**
```bash
# Full installation
pip install pygame obd pyserial pyirsdk
python MockInstrumentCluster_MultiSource.py
```

**Use Cases:**
- Development and testing
- Demonstrating all features
- Systems that need both OBD and sim support
- When you're not sure which you'll use

---

## Feature Comparison Matrix

| Feature | OBD Only | iRacing Only | Multi-Source |
|---------|----------|--------------|--------------|
| **OBD-II Support** | ✅ | ❌ | ✅ |
| **iRacing Support** | ❌ | ✅ | ✅ |
| **Mock Data** | ✅ | ❌ | ✅ |
| **DTC Codes** | ✅ | ❌ | ✅ |
| **Auto-reconnect** | ❌ | ✅ | ✅ |
| **Source Switching** | ❌ | ❌ | ✅ |
| **File Size** | Small | Small | Large |
| **Dependencies** | 2 | 2 | 4 |
| **Target FPS** | 30 | 60 | 30 |
| **Optimized For** | Raspberry Pi | Gaming PC | Both |

---

## Screen Layouts (All Versions)

### Screen 1 - Main Gauges
**Same layout for all versions:**
- RPM gauge (large, right)
- Speed gauge (medium, right)
- Temperature gauges (left)
- Battery voltage
- Fuel level bar

**Differences:**
- OBD: Shows ECT (Coolant), IAT (Intake Air)
- iRacing: Shows Water Temp, Oil Temp
- Multi: Adapts based on active source

### Screen 2 - Additional Info

**OBD Only:**
- Diagnostic Trouble Codes list
- Clear DTC button
- Shows up to 5 codes with descriptions

**iRacing Only:**
- Gear indicator
- Throttle, Brake, Clutch percentages
- Oil Pressure (PSI)
- Manifold Pressure (PSI)

**Multi-Source:**
- Shows DTC for OBD mode
- Shows telemetry for iRacing mode
- Adapts based on active source

### Screen 3 - Engine Parameters
**Same for all versions:**
- Timing Advance
- Engine Load
- Throttle Position
- MAF (Mass Air Flow)

**Note:** Some parameters unavailable in iRacing (shown as 0)

---

## Which Version Should You Use?

### Choose OBD Only If:
- ✓ Installing in your actual vehicle
- ✓ Using Raspberry Pi 3B+
- ✓ Need diagnostics and DTC reading
- ✓ Want smallest, most optimized code
- ✓ No interest in sim racing

**Ideal Hardware:**
- Raspberry Pi 3B+ or 4
- 7" touchscreen display
- ELM327 OBD-II adapter
- Permanent 12V power installation

---

### Choose iRacing Only If:
- ✓ Dedicated sim racing setup
- ✓ Windows PC
- ✓ Want highest refresh rate (60 FPS)
- ✓ Only use for iRacing
- ✓ Need gear/pedal telemetry

**Ideal Hardware:**
- Gaming PC with iRacing
- Second monitor or tablet
- USB connection
- High-performance GPU

---

### Choose Multi-Source If:
- ✓ Want maximum flexibility
- ✓ Testing/development purposes
- ✓ Need both car and sim support
- ✓ Demonstrating features
- ✓ Unsure which you'll use most

**Ideal Hardware:**
- Portable laptop/tablet
- Can move between car and sim rig
- USB OBD adapter for car
- Windows for iRacing support

---

## Performance Expectations

### OBD Only (Raspberry Pi 3B+)
- CPU Usage: ~25-35%
- RAM Usage: ~150-200 MB
- Temperature: 55-65°C
- Frame Rate: Consistent 30 FPS
- Startup Time: 2-3 seconds

### iRacing Only (Gaming PC)
- CPU Usage: ~5-15% (single core)
- RAM Usage: ~100-150 MB
- Frame Rate: Consistent 60 FPS
- Startup Time: 1-2 seconds
- No impact on iRacing performance

### Multi-Source (Either Platform)
- CPU Usage: ~30-40% (Pi) / 10-20% (PC)
- RAM Usage: ~200-250 MB
- Frame Rate: 30 FPS (default)
- Startup Time: 3-4 seconds
- Slightly higher overhead

---

## Installation Quick Reference

### Raspberry Pi (OBD Only)
```bash
sudo apt-get update
sudo apt-get install python3-pygame
pip3 install obd pyserial --break-system-packages
python3 Dashboard_OBD_Only.py
```

### Windows PC (iRacing Only)
```bash
pip install pygame
pip install pyirsdk
python Dashboard_iRacing_Only.py
```

### Universal (Multi-Source)
```bash
# Raspberry Pi
pip3 install pygame obd pyserial pyirsdk --break-system-packages

# Windows
pip install pygame obd pyserial pyirsdk

python MockInstrumentCluster_MultiSource.py
```

---

## Keyboard Shortcuts

### All Versions
- **ESC** - Exit
- **1** - Screen 1 (Main)
- **2** - Screen 2 (Info)
- **3** - Screen 3 (Engine)

### Multi-Source Only
- **F1** - Switch to Mock data
- **F2** - Switch to OBD-II
- **F3** - Switch to iRacing

### iRacing Only
- **R** - Manual reconnect

---

## Common Issues & Solutions

### OBD Only
**Problem:** "No OBD port found"
**Solution:** 
- Check adapter is plugged in
- Verify with `ls /dev/tty*`
- Add user to dialout group: `sudo usermod -a -G dialout $USER`

### iRacing Only
**Problem:** "iRacing not available"
**Solution:**
- Make sure iRacing is running
- Must be in a car (not menu)
- Try pressing R to reconnect
- Check pyirsdk installation

### Multi-Source
**Problem:** Wrong source selected
**Solution:**
- Press F1/F2/F3 to switch manually
- Check top-left indicator
- Verify connections

---

## File Sizes

- `Dashboard_OBD_Only.py` - ~15 KB
- `Dashboard_iRacing_Only.py` - ~17 KB
- `MockInstrumentCluster_MultiSource.py` - ~25 KB
- Total with all 3 versions - ~57 KB

---

## Recommendations

### For Most Users:
Start with the **dedicated version** for your use case (OBD or iRacing). They're simpler, faster, and have fewer dependencies.

### For Developers:
Use the **Multi-Source version** for testing and demonstrating all features.

### For Future-Proofing:
Keep all three versions. They're small files and you might want different ones for different scenarios.

---

## Support & Troubleshooting

All versions include:
- Clear console output for debugging
- Connection status indicators
- Error handling with messages
- Graceful fallback behavior

Check the console/terminal output for detailed error messages and connection status.

---

## Summary

- **OBD Only** = Car telemetry, Raspberry Pi optimized
- **iRacing Only** = Sim racing, gaming PC optimized  
- **Multi-Source** = Everything, maximum flexibility

Choose based on your primary use case for best performance and simplicity.
