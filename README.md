# SysFlow 🖥️⚡

### Free. Open. Your system, measured honestly.

SysFlow is a free, open system monitor and task manager designed to give you a clear view of what your computer is doing.

It monitors CPU, memory, processes, disks, users, services, startup applications, power, hardware information, installed applications, and more, while avoiding made-up telemetry when information isn't available.

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
| 5  | 🚀 **Startup Apps**   | Applications configured to launch automatically                     |
| 6  | 👤 **Users**          | Currently logged-in users and sessions                              |
| 7  | 🔧 **Services**       | Installed and running system services                               |
| 8  | ⚡ **Power & Freq**    | CPU frequency, power information, battery, and performance settings |
| 9  | 🧪 **Benchmarks**     | CPU performance testing                                             |
| 10 | 📦 **Installed Apps** | Applications installed on the system                                |
| 11 | 💾 **Disk Space**     | Storage devices, partitions, capacity, and usage                    |

### Free means free

SysFlow does **not** lock monitoring features behind a Pro tier.

There are no:

* 💳 Subscriptions
* 🔒 Pro-only pages
* ⏳ Feature trials
* 💰 Paid telemetry
* 🚫 Artificial feature restrictions

The goal is simple: **system monitoring should be a utility, not a subscription.**

---

## 🖥️ Supported Platforms

SysFlow is being developed with platform-specific measurement backends while keeping the interface shared.

### 🐧 Linux

**Supported**

* Linux x86_64
* PySide6
* `psutil`
* Native Linux system interfaces
* systemd integration
* Linux hardware telemetry where available

A Debian package is available for Linux builds.

### 🪟 Windows

**Supported**

* Windows 10/11
* Windows x64
* Windows-specific system backends
* Windows Services
* Windows startup applications
* Windows installed applications
* Windows hardware information
* NVIDIA GPU telemetry when available

Windows builds are produced automatically using GitHub Actions.

### 🍎 macOS

macOS support is part of the planned cross-platform architecture.

---

# 📥 Installation

## 🐧 Linux

Download the latest `.deb` package from the project's releases.

Then install it with:

```bash
sudo apt install ./sysflow_0.1.0_amd64.deb
```

Launch SysFlow from your Applications menu.

---

## 🪟 Windows

Download the Windows build and extract the archive.

The folder contains:

```text
SysFlow/
├── SysFlow.exe
└── _internal/
```

Run:

```text
SysFlow.exe
```

**Keep the `_internal` folder next to `SysFlow.exe`.**

The Windows build is packaged with PyInstaller, so Python does not need to be installed separately.

> Windows or browser security software may display reputation warnings for newly built unsigned applications. Always obtain SysFlow from the official project releases and verify the release before running it.

---

# 🛠️ Building From Source

## Requirements

* Python 3.12+
* PySide6
* psutil

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run SysFlow:

```bash
python app.py
```

---

## 🪟 Building Windows

Windows builds are generated automatically through GitHub Actions.

The workflow:

```text
Git push
   │
   ▼
GitHub Actions
   │
   ▼
Windows runner
   │
   ├── Python
   ├── PySide6
   ├── psutil
   └── PyInstaller
   │
   ▼
SysFlow.exe
```

To manually trigger a build, open the **Actions** tab in the GitHub repository and run the Windows build workflow.

---

# 🏗️ Architecture

SysFlow separates the user interface from the system measurement layer.

```text
                         SysFlow
                            │
                 ┌──────────┴──────────┐
                 │                     │
              UI Layer            Core Metrics
                 │                     │
        ┌────────┴────────┐     ┌──────┴──────┐
        │                 │     │             │
      Pages          Shared UI  psutil    Platform APIs
        │                           │             │
        └──────────────┬────────────┘             │
                       │                          │
                 Platform Backend ◄────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
        Linux       Windows       macOS
```

The interface stays consistent while platform-specific code handles the parts that differ between operating systems.

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
        └── windows-build.yml
```

---

# 📊 Telemetry Philosophy

SysFlow is built around one important rule:

> **Never pretend unavailable data exists.**

If a sensor or operating system does not provide reliable information, SysFlow should report it as unavailable instead of displaying a fabricated value.

For example:

```text
CPU Temperature: 52°C
```

is useful when a real sensor provides that measurement.

But if the operating system provides no trustworthy temperature source:

```text
CPU Temperature: Unavailable
```

is better than guessing.

This principle applies throughout SysFlow.

### Zero is not unavailable

A measurement of:

```text
0%
```

means something.

A measurement that could not be obtained means:

```text
Unavailable
```

Those are deliberately different states.

---

# 🔐 Privacy

SysFlow is designed to monitor the computer it is running on.

Normal system telemetry is collected locally using operating-system APIs and local libraries.

SysFlow does not need a remote server to display:

* CPU usage
* Memory usage
* Processes
* Disk usage
* System information
* Logged-in users
* Services
* Local hardware telemetry

The application is intended to keep system monitoring local to the machine.

---

# 🧰 Built With

* 🐍 **Python**
* 🎨 **PySide6**
* 📊 **psutil**
* 📦 **PyInstaller**
* 🐧 **Debian packaging**
* ☁️ **GitHub Actions**

Platform-specific system APIs are used where cross-platform libraries cannot provide reliable information.

---

# 🧪 Development Status

## v0.1.0

Current development milestone:

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
* 🟢 Linux build
* 🟢 Windows build pipeline
* 🟢 GitHub repository

SysFlow is actively being developed.

---

# 🗺️ Roadmap

Future development may include:

* 🍎 Expanded macOS backend
* 🎮 More GPU telemetry
* 🌡️ Additional hardware sensors
* 📡 Network monitoring
* 🔋 Deeper power telemetry
* 📊 More benchmark types
* 🎨 Additional themes
* 📈 More historical graphs
* 📦 Additional package formats
* 🪟 Windows hardware telemetry improvements

Features will be added without turning core monitoring functionality into a paid tier.

---



# 🤝 Contributing

Contributions, bug reports, ideas, and testing feedback are welcome.

If you find a problem:

1. Check the existing issues.
2. Create a new issue if the problem has not already been reported.
3. Include your operating system and SysFlow version.
4. Include relevant error messages or logs.
5. Explain how the issue can be reproduced.

For hardware-specific telemetry problems, include the relevant CPU/GPU and operating system information when possible.

---

# 🐛 Reporting Bugs

When reporting a bug, useful information includes:

```text
SysFlow version:
Operating system:
CPU:
GPU:
Python version:
What happened:
What you expected:
Steps to reproduce:
```

Please avoid posting passwords, private keys, personal files, or other sensitive information.

---

# 📜 License

SysFlow is free and open source.

See the repository license for the applicable license terms.

---

# 🚀 SysFlow

**Free system monitoring without the subscription nonsense.**

Made to measure your computer honestly.

```text
┌──────────────────────────────────────────────┐
│                  SYSFLOW                     │
│                                              │
│       Measure it. Understand it.             │
│                 Control it.                  │
│                                              │
│              🖥️  ⚡  📊  🔧                  │
└──────────────────────────────────────────────┘
```

**SysFlow v0.1.0**
