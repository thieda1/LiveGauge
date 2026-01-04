# Magden Dashboard

> Real-time automotive and sim racing telemetry dashboard with a sleek neon aesthetic

A high-performance, multi-platform dashboard for displaying vehicle telemetry from OBD-II adapters or iRacing simulator. Features optimized rendering, professional gauge layouts, and comprehensive data logging.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Raspberry%20Pi-lightgrey.svg)

## ✨ Features

- 🎨 **Beautiful Neon UI** - Custom-designed gauges with color-coded RPM zones
- 🚗 **OBD-II Support** - Real-time data from your vehicle via ELM327 adapter
- 🏎️ **iRacing Integration** - Full telemetry from iRacing simulator
- 📊 **Three Screen Layouts** - Main gauges, diagnostics/telemetry, and engine parameters
- 📝 **Data Logging** - CSV logging with 5-minute buffer
- 🔧 **DTC Reading** - Read and clear diagnostic trouble codes
- ⚡ **Optimized Performance** - Runs smoothly on Raspberry Pi 3B+
- 🔄 **Multi-Source Support** - Switch between OBD-II, iRacing, or mock data

## 🖼️ Screenshots

### Screen 1 - Main Gauges
Main dashboard with RPM, speed, temperatures, battery voltage, and fuel level.

### Screen 2 - Additional Info
- **OBD Mode**: Diagnostic Trouble Codes with descriptions
- **iRacing Mode**: Gear, throttle/brake/clutch, oil pressure, manifold pressure

### Screen 3 - Engine Parameters
Timing advance, engine load, throttle position, and mass air flow.

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.7 or higher
python --version

# For OBD-II support
pip install pygame obd pyserial

# For iRacing support
pip install pygame pyirsdk
```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/magden-dashboard.git
cd magden-dashboard
```

2. Install dependencies:
```bash
# For OBD-II only
pip install -r requirements-obd.txt

# For iRacing only
pip install -r requirements-iracing.txt

# For both (universal version)
pip install -r requirements.txt
```

3. Run the dashboard:
```bash
# OBD-II version
python Dashboard_OBD_Only.py

# iRacing version
python Dashboard_iRacing_Only.py

# Universal version (all features)
python MockInstrumentCluster_MultiSource.py
```

## 📦 Available Versions

### 1. Dashboard_OBD_Only.py
**For vehicles with OBD-II adapter**
- Optimized for Raspberry Pi 3B+
- 30 FPS performance
- DTC reading and clearing
- Mock data fallback for testing
- Ideal for permanent car installation

### 2. Dashboard_iRacing_Only.py
**For sim racing setups**
- Optimized for gaming PCs
- 60 FPS for smooth display
- Auto-reconnect functionality
- Real-time pedal and gear telemetry
- Perfect for secondary monitor

### 3. MockInstrumentCluster_MultiSource.py
**Universal dashboard with all features**
- Supports OBD-II, iRacing, and mock data
- Switch between sources on-the-fly
- Great for testing and development
- Maximum flexibility

See [VERSION_COMPARISON.md](VERSION_COMPARISON.md) for detailed comparison.

## 🎮 Controls

### Navigation
- **1, 2, 3** - Switch between screens
- **ESC** - Exit dashboard
- **Mouse** - Click screen buttons and controls

### Data Source Switching (Multi-Source version only)
- **F1** - Mock data
- **F2** - OBD-II data
- **F3** - iRacing data

### Logging
- **L Button** (bottom-right) - Start 5-minute data logging session

## 🔌 Hardware Setup

### OBD-II Setup (Vehicle)

**Required Hardware:**
- ELM327 OBD-II adapter (USB or Bluetooth)
- Raspberry Pi 3B+ or 4 (recommended)
- 7" touchscreen display (optional)
- 12V to 5V power adapter for permanent installation

**Connection:**
1. Plug ELM327 adapter into vehicle's OBD-II port
2. Connect adapter to Raspberry Pi via USB
3. Run the dashboard

**Port Permissions (Linux/Raspberry Pi):**
```bash
sudo usermod -a -G dialout $USER
# Log out and back in for changes to take effect
```

### iRacing Setup (Simulator)

**Required:**
- Windows PC with iRacing installed
- iRacing must be running and you must be in a car (not menu)

**Connection:**
Dashboard automatically connects via iRacing's shared memory interface.

## 📊 Data Logging

The dashboard logs telemetry data to CSV files with the following parameters:
- Timestamp
- RPM
- Speed
- Coolant/Water Temperature
- Intake/Oil Temperature
- Fuel Level
- Battery Voltage
- Throttle Position
- Engine Load
- Timing Advance (OBD only)
- MAF (OBD only)

**Log Files:**
- `obd_log_YYYYMMDD_HHMMSS.csv` - OBD-II data
- `iracing_log_YYYYMMDD_HHMMSS.csv` - iRacing data
- `mock_log_YYYYMMDD_HHMMSS.csv` - Mock data

Logs are automatically created in the current directory.

## 🎨 Customization

### Changing Max RPM
Edit the RPM gauge max value in screen drawing functions:
```python
draw_magden_gauge(surface, x, y, radius, rpm_value, 9000, "RPM", "")  # Changed from 7000
```

### Adjusting Frame Rate
```python
TARGET_FPS = 30  # Change to 60 for smoother animation (higher CPU usage)
```

### Custom Font
Place your custom font file in the same directory and update:
```python
font_cache[size] = pygame.font.Font("YourFont.ttf", size)
```

### Color Scheme
Modify color constants at the top of the file:
```python
BLUE = (0, 120, 255)    # Neon blue
YELLOW = (255, 255, 0)  # 4000+ RPM warning
RED = (255, 0, 0)       # 6000+ RPM danger
```

## 🔧 Optimization for Raspberry Pi

The dashboard is optimized for Raspberry Pi 3B+ with these techniques:
- Font caching (loaded once at startup)
- Hardware acceleration (HWSURFACE, DOUBLEBUF)
- 30 FPS target for lower CPU usage
- Efficient rendering loop
- Minimal memory allocations

**Expected Performance on Pi 3B+:**
- CPU Usage: 25-35%
- Temperature: 55-65°C
- Frame Rate: Consistent 30 FPS

**Additional Optimizations:**
See [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) for system-level tweaks like:
- Enabling KMS driver
- CPU governor settings
- GPU memory allocation
- Overclocking (optional)

## 📖 Documentation

- [VERSION_COMPARISON.md](VERSION_COMPARISON.md) - Detailed comparison of all versions
- [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) - Performance tuning for Raspberry Pi
- [IRACING_SETUP_GUIDE.md](IRACING_SETUP_GUIDE.md) - Complete iRacing integration guide

## 🐛 Troubleshooting

### OBD-II Issues

**"No OBD port found"**
```bash
# Check available ports
ls /dev/tty*

# Look for: ttyUSB0, ttyACM0, or usbserial

# Add user to dialout group
sudo usermod -a -G dialout $USER
```

**Mock data showing instead of real data**
- Verify adapter is plugged in and powered
- Check vehicle ignition is on
- Try a different USB port
- Test adapter with another OBD tool

### iRacing Issues

**"iRacing not available"**
- Ensure iRacing is running
- Must be in a car (not garage/menu)
- Check pyirsdk installation: `pip list | grep pyirsdk`
- Press R key to manually reconnect

**Connection lost during session**
- Dashboard auto-reconnects every second
- Manually press R to force reconnect
- Check if iRacing session ended

### Performance Issues

**Low frame rate on Raspberry Pi**
- Ensure desktop environment is minimal
- Close background applications
- Check CPU temperature: `vcgencmd measure_temp`
- Consider heatsink or fan

**High CPU usage**
- Reduce TARGET_FPS value
- Disable screen compositing
- Use Raspberry Pi OS Lite (no desktop)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Coding Standards
- Follow PEP 8 style guide
- Add comments for complex logic
- Test on both Raspberry Pi and Windows
- Update documentation for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **python-OBD** - OBD-II library for Python
- **pyirsdk** - iRacing SDK for Python
- **pygame** - Graphics and UI framework
- Original "Magden" design aesthetic

## 💡 Future Enhancements

Potential features for future releases:
- [ ] Lap time display for iRacing
- [ ] Tire temperature and pressure
- [ ] Customizable gauge layouts
- [ ] Multiple color themes
- [ ] WiFi data streaming
- [ ] Mobile app companion
- [ ] GPS integration
- [ ] Video recording integration
- [ ] Track day mode with split times
- [ ] Multi-language support

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/magden-dashboard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/magden-dashboard/discussions)
- **Email**: your.email@example.com

## ⭐ Show Your Support

If you find this project useful, please consider giving it a star on GitHub!

## 📊 Project Stats

![GitHub stars](https://img.shields.io/github/stars/yourusername/magden-dashboard?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/magden-dashboard?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/magden-dashboard)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/magden-dashboard)

---

**Made with ❤️ for car enthusiasts and sim racers**
