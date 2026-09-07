# Phone-Connected 2-Stage Pipelined Edge-AI Accelerator Co-Processor

[![Board](https://img.shields.io/badge/FPGA-Altera_DE2--70-blue.svg)](https://www.intel.com)
[![Toolchain](https://img.shields.io/badge/Quartus_II-v13.0sp1-orange.svg)](https://fpgasoftware.intel.com)
[![Simulation](https://img.shields.io/badge/ModelSim-Altera_Edition-green.svg)](https://www.intel.com)
[![Target](https://img.shields.io/badge/Architecture-Cyclone_II_EP2C70-red.svg)](https://www.intel.com)

An ultra-lightweight, hardware-accelerated Edge-AI co-processor implemented on the **Altera DE2-70 (Cyclone II)** platform. Featuring a custom **2-stage pipelined MAC execution engine**, M4K-based weight ROM buffers, and a real-time **Bluetooth/UART interface** to offload neural network inference from mobile devices.

---

## ?? System Architecture

\\\	ext
+-----------------+        UART/BT        +-------------------------------------------------------+
|                 |  Feature Stream (INT8) |  Altera DE2-70 FPGA (Cyclone II)                     |
|  Mobile Phone   | --------------------> |                                                       |
|  (Client App)   | <-------------------- |  +-----------------+  Stage 1   +------------------+  |
|                 |   Prediction Result   |  | UART RX Buffer  | -------->| Fetch & Multiply |  |
+-----------------+                       |  +-----------------+          +------------------+  |
                                          |                                    |                |
                                          |                                    v Stage 2        |
                                          |                           +------------------+      |
                                          |                           | Accumulate & ReLU|      |
                                          |                           +------------------+      |
                                          +-------------------------------------------------------+
\\\

---

## ?? Repository Directory Structure

\\\	ext
edge-ai-coprocessor/
+-- rtl/                        # Hardware Verilog HDL Code
¦   +-- core/                   # 2-stage pipeline datapath & MAC ALU engine
¦   +-- control/                # FSM controller, hazard detection, & stalls
¦   +-- memory/                 # M4K RAM/ROM wrappers & weight buffers
¦   +-- interface/              # Hardware UART RX/TX & packet frame decoders
+-- tb/                         # Verification & Waveform Simulation (ModelSim)
¦   +-- unit/                   # Unit testbenches for individual modules
¦   +-- integration/            # Subsystem pipeline integration tests
¦   +-- system/                 # Full co-processor end-to-end testbench
+-- fpga/                       # Quartus II Workspace & Board Setup
¦   +-- quartus/                # Quartus II project files (.qpf)
¦   +-- constraints/            # DE2-70 Pin assignments (.qsf) & timing (.sdc)
¦   +-- scripts/                # Build and synthesis automation scripts
+-- models/                     # Machine Learning Pipeline
¦   +-- training/               # Neural network definition & training
¦   +-- quantization/           # Fixed-point quantization routines (INT8)
¦   +-- export/                 # .mif / .hex Memory Initialization File generator
+-- app/                        # Communication Stack
¦   +-- firmware/               # ESP32 / HC-05 Bluetooth transceiver code
¦   +-- client/                 # Mobile companion app / terminal script
+-- docs/                       # Technical Specifications & Defense Materials
    +-- architecture/           # Datapath block diagrams & register maps
    +-- protocols/              # UART packet definitions & frame structures
    +-- reports/                # Synthesis, timing analysis, & power metrics
\\\

---

## ?? Subsystem Work Delegation Matrix

Ownership is structured by functional modules to enable parallel development while maintaining full cross-system knowledge.

| Subsystem Role | Functional Domain | Primary Workspace | Core Deliverables |
| :--- | :--- | :--- | :--- |
| **1. RTL Datapath Lead** | 2-Stage Execution Core | \tl/core/\ | Pipelined MAC unit, Stage registers, Activation logic (ReLU) |
| **2. FSM & Memory Lead** | Control Logic & Storage | \tl/control/\, \tl/memory/\ | Execution FSM, Hazard/Stall logic, M4K ROM wrappers |
| **3. Interface & Hardware Lead**| Connectivity & Framing | \tl/interface/\, \pp/firmware/\ | UART RX/TX drivers, Packet decoder, ESP32 Bluetooth link |
| **4. Verification Lead** | Simulation & Validation | \	b/\, \docs/reports/\ | ModelSim testbenches, timing checks, test coverage report |
| **5. AI & Systems Lead** | ML Engine & Board Bring-up | \models/\, \pga/\, \pp/client/\ | INT8 quantization, \.mif\ weight export, Quartus pins, Mobile app |

---

## ?? Cross-Verification & Defense Strategy

To guarantee **100% full-system mastery across every team member** for project defense:

1. **Cross-Testbench Rule:** No engineer writes testbenches for their own RTL logic. Teammates write verification testbenches for adjacent modules to master the entire system behavior.
2. **Peer-Reviewed Merges:** Every Pull Request requires **at least 2 team approvals** on GitHub before merging into \main\.
3. **Interface Protocols:** Shared register maps and packet protocols defined in \docs/protocols/\ serve as binding contracts across all sub-teams.

---

## ?? Getting Started

### 1. Prerequisites
* **Intel/Altera Quartus II:** Web Edition v13.0sp1 (Targeting Cyclone II EP2C70)
* **Simulation:** ModelSim-Altera Starter Edition
* **Software Stack:** Python 3.9+, PyTorch/NumPy, VS Code

### 2. Running Simulations (ModelSim)
\\\ash
cd tb/unit
vlib work
vlog ../../rtl/core/alu/*.v tb_mac_unit.v
vsim work.tb_mac_unit
\\\

### 3. Hardware Synthesis (Quartus II)
1. Open \pga/quartus/edge_ai_top.qpf\ in Quartus II v13.0sp1.
2. Run **Analysis & Synthesis**.
3. Verify pin assignments match the DE2-70 board specifications in \pga/constraints/\.
4. Compile and flash using **USB-Blaster**.
