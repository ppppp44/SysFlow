# SysFlow 🐧⚡

### A free, open-source Linux system monitor and task manager.

SysFlow is a Linux desktop application for monitoring your computer, inspecting running processes, managing system services, viewing hardware information, checking storage, and measuring system performance.

SysFlow is designed specifically for Linux so it can take advantage of Linux-native system interfaces and provide accurate telemetry without maintaining separate Windows and macOS implementations.

> **A measuring instrument should never make up an answer.**

---

## ✨ Features

SysFlow v0.1 includes:

| #  | Page                  | What it shows                                                       |
| -- | --------------------- | ------------------------------------------------------------------- |
| 1  | 📊 **Summary**        | CPU, memory, GPU, temperatures, and system overview                 |
| 2  | 📈 **Performance**    | Per-core CPU usage, memory, and performance telemetry               |
| 3  | ⚙️ **Processes**      | Running processes, CPU usage, memory, threads, and process controls |
| 4  | 🖥️ **System Info**   | CPU, GPU, motherboard, BIOS, OS, kernel, and hardware information   |
| 5  | 🚀 **Startup Apps**   | Applications configured to start automatically                      |
| 6  | 👤 **Users**          | Currently logged-in users and sessions                              |
| 7  | 🔧 **Services**       | Linux system services and their current state                       |
| 8  | ⚡ **Power & Freq**    | CPU frequency, governors, battery, and power information            |
| 9  | 🧪 **Benchmarks**     | CPU performance testing                                             |
| 10 | 📦 **Installed Apps** | Applications installed through the Linux package system             |
| 11 | 💾 **Disk Space**     | Storage devices, partitions, capacity, and usage                    |

---

# 🐧 Linux First

SysFlow is intentionally **Linux-only**.

Instead of building a generic abstraction layer for multiple operating systems, SysFlow can focus on the Linux kernel and Linux's native interfaces.

This allows the project to make better use of:

* `/proc`
* `/sys`
* `systemd`
* `hwmon`
* `powercap`
* `lspci`
* Linux filesystem APIs
* CPU frequency governors
* RAPL energy counters
* Linux user sessions
* Linux package databases

The result is a smaller, more focused application with fewer compatibility layers.

---

# 🎯 Project Philosophy

SysFlow follows a simple rule:

> **Never invent telemetry.**

If the operating system provides reliable information, SysFlow displays it.

If the information cannot be obtained reliably, SysFlow reports it as unavailable.

For example:

```text
CPU Temperature: 51°C
```

is useful when a real sensor provides that measurement.

If no trustworthy temperature sensor is available:

```text
CPU Temperature: Unavailable
```

is better than guessing.

### Zero is not unavailable

These are different states:

```text
CPU Usage: 0%
```

means the CPU is currently reporting zero utilization.

```text
CPU Temperature: Unavailable
```

means SysFlow could not obtain a trustworthy measurement.

SysFlow keeps those states separate.

---

# 🖥️ Supported Systems

SysFlow targets modern 64-bit Linux systems.

### Primary targets

* Linux x86_64
* Linux ARM64

### Tested / intended distributions

* Linux Mint
* Ubuntu
* Debian
* Fedora
* Arch-based distributions

Distribution-specific behavior may vary depending on available system interfaces, permissions, hardware sensors, and installed utilities.

---

# 📥 Installation

## Debian / Ubuntu / Linux Mint

Download the latest `.deb` release.

Install it with:

```bash
sudo apt install ./sysflow_0.1.0_amd64.deb
```

Then launch **SysFlow** from your applications menu.

You can also launch it from a terminal:

```bash
sysflow
```

---

# 🛠️ Running From Source

## Requirements

* Python 3.12+
* PySide6
* psutil
* Linux

Clone the repository:

```bash
git clone https://github.com/ppppp44/SysFlow.git
cd SysFlow
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run SysFlow:

```bash
python app.py
```

---

# 📦 Building the Debian Package

SysFlow includes Debian packaging files.

From the project root:

```bash
dpkg-deb --build debian/sysflow
```

This produces:

```text
debian/sysflow.deb
```

Install the package:

```bash
sudo apt install ./debian/sysflow.deb
```

---

# 🏗️ Architecture

SysFlow uses a Python + PySide6 interface with Linux-focused telemetry backends.

```text
                         SysFlow
                            │
             ┌──────────────┴──────────────┐
             │                             │
          PySide6                     Core Metrics
             │                             │
      ┌──────┴──────┐              ┌───────┴───────┐
      │             │              │               │
    Pages          UI           psutil         Linux APIs
      │                              │               │
      └──────────────┬───────────────┴───────────────┘
                     │
               Linux telemetry
                     │
        ┌────────────┼────────────┐
        │            │            │
      /proc         /sys       systemd
        │            │            │
        └────────────┼────────────┘
                     │
                  SysFlow
```

The interface is separated into pages while system measurements are handled by dedicated core modules.

---

# 📁 Project Structure

```text
SysFlow/
├── app.py
├── main.py
├── requirements.txt
│
├── core/
│   ├── gpu.py
│   ├── processes.py
│   └── system_metrics.py
│
├── pages/
│   ├── benchmarks.py
│   ├── disk_space.py
│   ├── installed_apps.py
│   ├── performance.py
│   ├── power_freq.py
│   ├── processes.py
│   ├── services.py
│   ├── startup.py
│   ├── system_info.py
│   └── users.py
│
├── debian/
│   └── sysflow/
│       ├── DEBIAN/
│       └── usr/
│
└── .github/
    └── workflows/
```

---

# 📊 Monitoring

SysFlow can monitor a variety of system resources.

### CPU

* Overall CPU utilization
* Per-logical-processor utilization
* CPU frequency
* CPU temperature when available
* CPU information
* CPU benchmarks

### Memory

* Used memory
* Total memory
* Memory percentage
* Memory history

### GPU

* GPU identification
* GPU utilization when supported
* GPU temperature when supported
* GPU memory information when supported
* GPU clock information when supported

### Storage

* Filesystem capacity
* Used space
* Available space
* Disk information

### Processes

* Process ID
* Process name
* User
* CPU usage
* Memory usage
* Threads
* Status
* Command
* Executable
* Parent process

Process controls include:

* End
* Kill
* Suspend
* Resume

---

# ⚡ Power & Frequency

SysFlow uses Linux-specific interfaces for power and frequency information where available.

Depending on the hardware and kernel configuration, this can include:

* CPU frequency
* CPU frequency governors
* CPU policies
* Battery information
* Energy counters
* RAPL information
* Power-related telemetry

Hardware support varies between processors and Linux kernels.

When a measurement is unavailable, SysFlow reports it as unavailable rather than estimating it.

---

# 🔧 Services

SysFlow can inspect Linux `systemd` services.

Service information can include:

* Service name
* Description
* State
* Enabled/disabled state
* Service status

Where permissions allow it, SysFlow can also interact with services.

Some service operations require administrator privileges.

---

# 🚀 Startup Applications

SysFlow can inspect applications configured to start automatically when a Linux desktop session begins.

Linux startup information may come from:

* `/etc/xdg/autostart`
* User autostart directories
* `.desktop` files

SysFlow displays the available startup information rather than assuming that every startup mechanism is identical across Linux environments.

---

# 📦 Installed Applications

SysFlow can inspect installed Linux applications through the system package database.

On Debian-based systems this includes package information from:

* `dpkg`
* APT package metadata

The goal is to show what is actually installed on the system rather than maintaining a separate application database.

---

# 👤 Users

SysFlow can display active user sessions using Linux system information.

Information may include:

* Username
* Terminal
* Login time
* Remote/local session information
* Current session state

---

# 🖥️ System Information

SysFlow provides information about the Linux system and its hardware.

Depending on the system, this can include:

* Distribution
* Kernel version
* Architecture
* CPU
* GPU
* Motherboard
* BIOS
* System uptime
* Hardware information

Linux-native interfaces and available system utilities are used to gather this information.

---

# 🧪 Benchmarks

SysFlow includes CPU benchmarking tools for basic performance testing.

Benchmarks are intended to provide useful relative measurements rather than replace dedicated benchmarking applications.

Results can vary depending on:

* CPU temperature
* Background processes
* CPU frequency scaling
* Power settings
* Thermal throttling
* System load

---

# 🔐 Privacy

SysFlow is designed for local system monitoring.

Normal monitoring does not require a remote telemetry server.

System information is collected locally from the Linux machine and displayed locally in the application.

SysFlow does not need an online account to monitor your computer.

---

# ⚙️ Performance

SysFlow is designed to minimize unnecessary system overhead.

A system monitor should not become the thing consuming all the resources it is supposed to measure.

The project therefore aims to:

* Avoid unnecessary polling
* Keep telemetry collection separate from UI rendering
* Avoid blocking the interface
* Update graphs efficiently
* Avoid collecting information that is not needed
* Keep unavailable measurements unavailable instead of repeatedly retrying expensive operations

Performance improvements remain an ongoing part of development.

---

# 📸 Screenshots

<img width="3072" height="1633" alt="image" src="https://github.com/user-attachments/assets/7aef376f-e074-4756-8027-1cdd274c9f0a" />

<img width="3072" height="1614" alt="image" src="https://github.com/user-attachments/assets/b82c0f0a-05f5-40f3-8853-8b9006484dc8" />

<img width="3064" height="1645" alt="image" src="https://github.com/user-attachments/assets/1f31f608-d091-4876-9517-6613fecfbab2" />

<img width="3072" height="1649" alt="image" src="https://github.com/user-attachments/assets/9dcd07ba-e77d-41f3-86b3-7d01e2c20757" />

<img width="3072" height="1648" alt="image" src="https://github.com/user-attachments/assets/6c448914-3e3f-4d2d-af32-7577a306dd86" />

<img width="3040" height="1639" alt="image" src="https://github.com/user-attachments/assets/689328b2-10aa-4bcd-b057-4223a20f82f4" />



---

# 🛠️ Built With

* 🐍 **Python**
* 🎨 **PySide6**
* 📊 **psutil**
* 🐧 Linux system interfaces
* 📦 Debian packaging
* ☁️ GitHub Actions

---

# 🚧 Project Status

## SysFlow v0.1.0

Current pages:

* 🟢 Summary
* 🟢 Performance
* 🟢 Processes
* 🟢 System Info
* 🟢 Startup Apps
* 🟢 Users
* 🟢 Services
* 🟢 Power & Freq
* 🟢 Benchmarks
* 🟢 Installed Apps
* 🟢 Disk Space

Current platform:

* 🟢 Linux

Windows and macOS builds are **not supported targets**.

SysFlow is actively being developed.

---

# 🗺️ Roadmap

Possible future improvements include:

* 📈 More historical performance graphs
* 🎮 Improved GPU telemetry
* 🌡️ More hardware sensors
* 🔋 Deeper power telemetry
* 💾 More detailed disk statistics
* 🌐 Network monitoring
* 🧪 Additional benchmarks
* 🎨 Additional themes
* ⚡ Lower telemetry overhead
* 📦 More Linux package formats
* 🏎️ Faster native implementation if performance requirements grow

---

# 🤝 Contributing

Bug reports, ideas, testing, and contributions are welcome.

When reporting a bug, include:

```text
SysFlow version:
Linux distribution:
Kernel:
CPU:
GPU:
What happened:
What you expected:
Steps to reproduce:
```

For hardware telemetry problems, include your CPU/GPU and relevant hardware information when possible.

Please do not include passwords, private keys, personal files, or other sensitive information.

---

# 🐛 Issues

If you encounter a problem, open an issue in the GitHub repository.

Useful bug reports should include enough information to reproduce the problem.

---

# 📜 License

SysFlow is free and open source.

See the repository license for the applicable license terms.

---

# 🚀 SysFlow

**Free Linux system monitoring without the subscription nonsense.**

Built for Linux.
Designed to measure honestly.
Made to stay out of your way.

```text
┌──────────────────────────────────────────────┐
│                    SYSFLOW                   │
│                                              │
│       Measure it. Understand it.             │
│              Control it.                     │
│                                              │
│             🐧  ⚡  📊  🔧                   │
└──────────────────────────────────────────────┘
```

**SysFlow v0.1.0**

[GitHub](https://github.com/ppppp44/SysFlow)
