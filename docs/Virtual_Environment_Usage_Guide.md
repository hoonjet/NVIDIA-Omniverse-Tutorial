# Virtual Environment Usage Guide

> **Location:** `E:\omniverse_env\`
> **Python Version:** 3.8
> **Key Packages:** usd-core (26.3), numpy

---

## 1. What is a Virtual Environment?

A Virtual Environment is an independent Python environment isolated from the system-wide Python environment. The `E:\omniverse_env` virtual environment allows you to install only the packages needed for USD/Omniverse learning without affecting other settings or packages on the E:\ drive.

### Separation from Existing Environments

```
System Python (global)          E:\physicsnemo_env (existing)       E:\omniverse_env (new)
├── Only base packages          ├── Python 3.10                     ├── Python 3.8
└── For system tools            ├── PyTorch, PhysicsNeMo             ├── usd-core, numpy
                                └── For AI/ML learning               └── For USD/Omniverse learning
```

> **Note:** `physicsnemo_env` and `omniverse_env` use different Python versions and packages, so they are completely independent. Using both environments simultaneously will not cause conflicts.

---

## 2. Activating the Virtual Environment

### Method 1: Command Prompt (cmd)

```batch
:: 1. Open Command Prompt (Win+R → cmd)

:: 2. Navigate to the virtual environment directory
cd E:\omniverse_env

:: 3. Activate the virtual environment
Scripts\activate
```

### Method 2: VS Code Terminal

1. Open the terminal in VS Code by pressing `Ctrl + ` ` (backtick)
2. Run the following commands in the terminal:
```batch
cd E:\omniverse_env
Scripts\activate
```

### Method 3: Run activate.bat directly

```batch
E:\omniverse_env\Scripts\activate.bat
```

### Verifying Activation

When `(omniverse_env)` appears before the prompt, activation is successful:

```
(omniverse_env) E:\omniverse_env>
```

---

## 3. Deactivating the Virtual Environment

```batch
:: Deactivate the virtual environment (return to system Python)
deactivate
```

After deactivation, the prompt will look like:
```
E:\omniverse_env>
```

---

## 4. Environment Verification

### 4.1 Check Python Version

```batch
(omniverse_env) python --version
:: Output: Python 3.8.x
```

### 4.2 Check USD Package

```batch
(omniverse_env) python -c "from pxr import Usd; print('USD version:', Usd.GetVersion())"
:: Output: USD version: (0, 26, 3)
```

### 4.3 Run Verification Script

```batch
(omniverse_env) python E:\omniverse_env\test_usd_import.py
```

Expected output:
```
============================================================
Omniverse Environment Verification
============================================================
Python version: 3.8.x
USD version: (0, 26, 3)
numpy version: 1.24.x
[OK] All packages are working correctly.
============================================================
```

---

## 5. Running Tutorials

### 5.1 Run a Single Tutorial

```batch
:: Activate the virtual environment
cd E:\omniverse_env
Scripts\activate

:: Run tutorial 01
python tutorials\01_usd_basics.py
```

### 5.2 Run All Tutorials Sequentially

```batch
cd E:\omniverse_env
Scripts\activate

python tutorials\01_usd_basics.py
python tutorials\02_usd_geometry.py
python tutorials\03_usd_materials.py
python tutorials\04_usd_animation.py
python tutorials\05_usd_assembly.py
python tutorials\06_kit_extensions.py
python tutorials\07_omniverse_connector.py
python tutorials\08_live_sync.py
python tutorials\09_physicsnemo_to_usd.py
python tutorials\10_simulation_visual.py
python tutorials\11_digital_twin.py
```

### 5.3 Check Output Files

```batch
:: List generated USD files
dir tutorials\output\*.usda

:: View the contents of a specific USD file (text format)
notepad tutorials\output\01_usd_basics.usda
```

---

## 6. Package Management

### 6.1 Check Installed Packages

```batch
(omniverse_env) pip list
```

### 6.2 Install Additional Packages

```batch
:: Example: install matplotlib (for visualization)
(omniverse_env) pip install matplotlib
```

### 6.3 Update Packages

```batch
:: Update usd-core
(omniverse_env) pip install --upgrade usd-core
```

---

## 7. Switching Between PhysicsNeMo and Omniverse Environments

When alternating between the two virtual environments:

### PhysicsNeMo Work → Omniverse Work

```batch
:: 1. Save model inference results from PhysicsNeMo environment
cd E:\physicsnemo_env
Scripts\activate
python save_predictions.py  :: Save as .npy file
deactivate

:: 2. Convert to USD in Omniverse environment
cd E:\omniverse_env
Scripts\activate
python convert_to_usd.py    :: Convert .npy → .usda
deactivate
```

### Data Exchange Directory

Data exchange between the two environments is done through a shared directory:

```
E:\omniverse_env\tutorials\output\physicsnemo_data\
    ↑ Save .npy/.json from physicsnemo_env
    ↓ Load and convert to USD in omniverse_env
```

---

## 8. Troubleshooting

### Issue: Error when running `Scripts\activate`

**Cause:** Execution policy restriction (PowerShell)

**Solution:**
```batch
:: Use Command Prompt (cmd) or
:: Change execution policy in PowerShell:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: `ModuleNotFoundError: No module named 'pxr'`

**Cause:** Virtual environment is not activated

**Solution:**
```batch
cd E:\omniverse_env
Scripts\activate
python -c "from pxr import Usd; print(Usd.GetVersion())"
```

### Issue: `FileExistsError` when creating USD stage

**Cause:** A file with the same name already exists

**Solution:** The tutorial scripts are designed to automatically delete existing files. To manually delete:
```batch
del E:\omniverse_env\tutorials\output\01_usd_basics.usda
```

### Issue: Virtual environment not activating in a different terminal

**Cause:** Each terminal window is independent

**Solution:** Activate the virtual environment every time you open a new terminal:
```batch
cd E:\omniverse_env
Scripts\activate
```

---

## 9. Summary

| Action | Command |
|--------|---------|
| Activate virtual environment | `cd E:\omniverse_env && Scripts\activate` |
| Deactivate virtual environment | `deactivate` |
| Verify environment | `python test_usd_import.py` |
| Run tutorial | `python tutorials\01_usd_basics.py` |
| List packages | `pip list` |
| Check Python version | `python --version` |
| Check USD version | `python -c "from pxr import Usd; print(Usd.GetVersion())"` |
