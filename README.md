# **Satellite Tracking System**

This repository contains the code and technical documentation for an automatic satellite tracking system, developed to control a dual-axis antenna using Moteus r4.11 motors.

## **Overview**

The goal of the project is to track low Earth orbit (LEO) satellites in real-time, using the Gpredict software to calculate satellite positions and command the azimuth and elevation motors accordingly.  
The entire system is implemented in Python, as it is easy to extend and integrate additional modules for future features.

## **System Architecture**

This project integrates:

- **Gpredict** for satellite position tracking and rotor control through the `rotctld` protocol.
- **Moteus r4.11** motors for precise azimuth and elevation control.
- A **custom Python GUI** for manual testing and debugging of motor positions.
- A **BNO055 sensor** for automatic north correction, ensuring consistent azimuth reference regardless of base orientation.

## **BNO055 Integration – Automatic North Correction**

A BNO055 USB Stick sensor is used to provide real-time heading data. This heading is used to compensate for any rotational misalignment of the rotor base, allowing the azimuth control to always be referenced to true north.

When using Gpredict or the manual GUI, this heading compensation ensures consistent behavior—even if the antenna base is rotated or repositioned. The correction is handled automatically by adjusting the azimuth motor’s position in software based on the current BNO heading.

## **Technical Progress Report**

A complete technical progress report is available in the repository. It includes:

- System design and architecture  
- Implementation details  
- Results and testing procedures  
- Future improvements  

## **Getting Started**

To use this system, ensure you have:

- Python 3.8+  
- A Moteus-compatible CAN interface (e.g., fdcanusb)  
- BNO055 USB Stick connected and recognized (e.g., `/dev/ttyACM1`)  
- Gpredict installed and configured to communicate with `rotctld`
- This project is primarily developed and tested on Linux, but it is also compatible with Windows

## **Contributing**

Feel free to contribute improvements or suggestions.  
You can open an issue or submit a pull request if you have ideas or enhancements to share.

---

Made with 💡 and a passion for antennas and embedded systems.
