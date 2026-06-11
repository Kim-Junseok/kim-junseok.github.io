---
title: "Sionna Setup Guide: WSL2, Ubuntu 24.04, and CUDA 13.0"
date: 2026-06-09 15:00:00 +0000
categories: [Sionna Learning]
tags: [sionna, wsl2, ubuntu, cuda, pytorch]
---

> A practical setup guide for running NVIDIA Sionna PHY / SYS / RT on Windows through WSL2.  
> This guide includes notes from an actual installation, including RTX 50-series compatibility warnings and large PyTorch package download timeouts.

**Tested environment**

- Windows 11, NVIDIA GeForce RTX 5060 Laptop GPU (8 GB)
- WSL2 Ubuntu 24.04, Python 3.12, CUDA 13.0
- Sionna (PHY + SYS + RT)

---

## 1. WSL2 vs Dual Boot

| | WSL2 (Recommended) | Dual Boot |
|---|---|---|
| Setup difficulty | Low, usually under 1 hour | Higher, usually 2-3 hours with partitioning |
| GPU performance | Around 5-10% overhead | Native maximum performance |
| CUDA support | Officially supported through WSL-CUDA | Fully supported |
| VS Code integration | Excellent with Remote-WSL | Requires local Linux setup |
| Recommended for | Learning and development | Large-scale RT simulation optimization |

**Conclusion: WSL2 is enough for learning and development.**  
Sionna RT can run on WSL2 + CUDA, and it can also run without a GPU by using the CPU LLVM backend.

---

## 2. Install WSL2

Open PowerShell as Administrator and run:

```powershell
wsl --install -d Ubuntu-24.04
```

After installation, reboot the PC, launch "Ubuntu 24.04" from the Start menu, and create a username and password.

> The password field does not show any characters while typing. This is normal.

Update packages and install the basic tools:

```bash
sudo apt update && sudo apt upgrade -y
```

```bash
sudo apt install -y python3 python3-venv python3-pip git curl build-essential
```

> **Note:** Ubuntu 24.04 uses Python 3.12 by default. If you try to install `python3.11`, you may see:
>
> ```text
> E: Unable to locate package python3.11
> ```
>
> Installing `python3` gives you Python 3.12, which satisfies Sionna's Python requirement of 3.11 or newer.

---

## 3. NVIDIA Driver + CUDA

### 3-1. NVIDIA Driver

When using GPU acceleration inside WSL2, install the NVIDIA driver on **Windows only**.  
Do not install a separate NVIDIA driver inside Ubuntu running under WSL.

```text
Windows (NVIDIA driver installed) yes
    -> WSL-CUDA bridge handles GPU access automatically
WSL Ubuntu (no separate driver, CUDA toolkit only) yes
```

Installing [NVIDIA App](https://www.nvidia.com/en-us/software/nvidia-app/) is a convenient way to keep the Windows driver up to date.

### 3-2. CUDA Toolkit 13.0

> **Important for RTX 50-series users:**  
> GPUs such as the RTX 5060 use NVIDIA's Blackwell architecture and have Compute Capability 12.0. To use this hardware natively instead of falling back to compatibility behavior, CUDA 13.0 or newer is recommended. If an older CUDA 12.x toolkit is already installed, clean up the old packages and folders first to reduce conflicts.

```bash
# Remove older CUDA packages and leftover folders
sudo apt-get purge "cuda*" "libcudnn*" "libnccl*"
sudo rm -rf /usr/local/cuda-12.6
sudo rm -rf /usr/local/cuda
sudo apt-get autoremove
sudo apt-get autoclean

# Download and register the NVIDIA package repository key
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb

# Register the key so apt trusts the NVIDIA repository
sudo dpkg -i cuda-keyring_1.1-1_all.deb

# Refresh package lists
sudo apt update

# Install CUDA 13.0 toolkit
sudo apt install -y cuda-toolkit-13-0
```

> **Note:** Installing `cuda-toolkit-12-4` on Ubuntu 24.04 may fail with:
>
> ```text
> nsight-systems-2023.4.4 : Depends: libtinfo5 but it is not installable
> ```
>
> Ubuntu 24.04 uses `libtinfo6`, and `libtinfo5` is no longer available by default. For RTX 50-series systems, it is better to move directly to a CUDA 13.0 setup.

### 3-3. PATH and Library Paths

Use the generic CUDA symlink path (`/usr/local/cuda`) instead of hardcoding a specific version folder such as `/usr/local/cuda-13.0`. This makes future CUDA version switching easier.

```bash
# Add nvcc to PATH
echo 'export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}' >> ~/.bashrc

# Add CUDA shared libraries to the runtime library path
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}' >> ~/.bashrc

# Apply changes to the current terminal session
source ~/.bashrc
```

> `~/.bashrc` is loaded automatically when a new terminal starts.  
> Without `source ~/.bashrc`, the new environment variables apply only after opening a new terminal.
>
> **Ubuntu alternatives note:**  
> Running `ls -l /usr/local/cuda` may show a chain through `/etc/alternatives/cuda` and eventually point to `/usr/local/cuda-13.0`. This is a normal Ubuntu alternatives structure for switching between installed versions, so you do not need to modify it manually.

### 3-4. Verify CUDA

```bash
nvidia-smi     # Check GPU visibility and driver version
nvcc --version # Check that the CUDA compiler reports release 13.0
```

The `CUDA Version` shown by `nvidia-smi` is the maximum CUDA version supported by the Windows driver.  
It does not have to exactly match the installed toolkit version, such as CUDA 13.0.

---

## 4. Python Virtual Environment

```bash
# Create a workspace directory
mkdir ~/sionna-workspace && cd ~/sionna-workspace

# Create an isolated Python environment in .venv
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

After activation, your shell prompt should include `(.venv)`.

> **Why use a virtual environment?**  
> It isolates Python packages from the system Python installation. This makes it easier to manage different Sionna versions or experiments independently.
>
> **Why name it `.venv`?**  
> Directories starting with `.` are hidden by default, and tools such as VS Code usually recognize `.venv` automatically.

---

## 5. Install PyTorch + Sionna

Run this section while the virtual environment is active.

### 5-1. PyTorch (cu130)

For RTX 50-series GPUs, use the `cu130` PyTorch index so the installed PyTorch build matches the CUDA 13.0 stack.

> **Troubleshooting: ReadTimeoutError during installation**  
> Large dependency packages such as `nvidia-cusparse-cu*` can be several hundred MB. On slower or unstable networks, `pip` may time out while downloading them. Adding `--default-timeout=1000` gives `pip` more time to finish the download.

```bash
# Remove old or incompatible PyTorch packages first, if present
pip uninstall -y torch torchvision torchaudio

# Install PyTorch for CUDA 13.0
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130 --default-timeout=1000
```

### 5-2. GPU Detection

After installation, run the following command and check that the GPU is detected without compatibility warnings:

```bash
python3 -c "import torch; print(f'Device: {torch.cuda.get_device_name(0)}'); print(f'CC: {torch.cuda.get_device_capability(0)}'); print(f'Is Compatible: {torch.cuda.is_available()}')"
```

Expected output example:

```text
Device: NVIDIA GeForce RTX 5060 Laptop GPU
CC: (12, 0)
Is Compatible: True
```

If warnings such as `sm_120 is not compatible` are gone, the native GPU acceleration environment is set up correctly.

### CPU-only Setup

If you only want CPU execution without GPU acceleration, install the standard PyPI build:

```bash
pip install torch torchvision torchaudio
```

### 5-3. Sionna

```bash
pip install sionna
```

When running `pip install sionna`, packages required for Sionna RT, such as `drjit` and `mitsuba`, are installed automatically.  
If you later run `pip install drjit mitsuba`, seeing `Requirement already satisfied` is normal.

### RT CPU Backend (LLVM)

Sionna RT can use LLVM to run ray-tracing operations on CPU when no GPU backend is available.

```bash
sudo apt install -y llvm-15
```

> **What LLVM does:**  
> `drjit` uses LLVM as the CPU backend when compiling code at runtime. If a CUDA-capable GPU is available, the CUDA backend is selected automatically, while LLVM remains useful as a fallback.

### JupyterLab

```bash
pip install jupyterlab
```

Start JupyterLab:

```bash
jupyter lab --no-browser
```

Copy the printed `http://localhost:8888/...` URL and open it in a Windows browser.

---

## 6. VS Code Workspace

### VS Code + Remote WSL

1. Install VS Code from [code.visualstudio.com](https://code.visualstudio.com). During installation, make sure "Add to PATH" is enabled.
2. Install these extensions:
   - `WSL` (`ms-vscode-remote.remote-wsl`)
   - `Python` (`ms-python.python`)
   - `Jupyter` (`ms-toolsai.jupyter`)

### Open VS Code

```bash
code ~/sionna-workspace/sionna-workspace.code-workspace
```

On the first launch, VS Code Server is installed automatically inside WSL. If you are already inside the workspace directory, you can also run `code sionna-workspace.code-workspace`.

> If the `code` command is not found, run `wsl --shutdown` from PowerShell and restart Ubuntu.

### Workspace File

```bash
cat > ~/sionna-workspace/sionna-workspace.code-workspace << 'EOF'
{
  "folders": [{ "path": "." }],
  "settings": {
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "jupyter.notebookFileRoot": "${workspaceFolder}"
  }
}
EOF
```

When this workspace file is opened, VS Code automatically uses the `~/sionna-workspace/.venv/bin/python` interpreter and sets the Jupyter notebook root to the workspace folder.

---

## 7. Verify Installation

### Official Example Notebooks

```bash
cd ~/sionna-workspace
git clone --recursive https://github.com/NVlabs/sionna
cd sionna/notebooks
```

### Verification Order

| Notebook | What to check |
|---|---|
| `Part1_Sionna_PHY.ipynb` | Basic PHY channel simulation |
| `Part2_Sionna_SYS.ipynb` | Link-level simulation |
| `Ray_Tracing_Introduction.ipynb` | RT scene rendering and channel generation |

> RT notebooks may take several minutes on the first run while scenes are compiled. This is normal.

### Sionna Version

```bash
python -c "import sionna; print(sionna.__version__)"
```

---

## 8. Daily Startup

```bash
cd ~/sionna-workspace
source .venv/bin/activate

# For notebook work
jupyter lab --no-browser

# For VS Code work
code .
```

---

## References

- [Sionna documentation](https://nvlabs.github.io/sionna/)
- [Sionna installation guide](https://nvlabs.github.io/sionna/installation.html)
- [NVIDIA WSL-CUDA guide](https://docs.nvidia.com/cuda/wsl-user-guide/)
- [PyTorch installation](https://pytorch.org/get-started/locally/)
