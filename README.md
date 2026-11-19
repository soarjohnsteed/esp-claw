# esp-claw · Waveshare ESP32-S3-Touch-LCD-3.5B

## English

### Overview

Hardware adaptation of [esp-claw](https://github.com/espressif/esp-claw) for the **Waveshare ESP32-S3-Touch-LCD-3.5B**.

The display controller is **AXS15231B with QSPI**. This adaptation requires changes to several shared source files, board configuration, and display refresh logic.

This version was reworked against the upstream code as of November 2026. It contains 11 adaptation files, all grouped under `Waveshare-ESP32-S3-Touch-LCD-3.5B/`.

The previous adaptation dated August 31, 2026, is not compatible with the November upstream version. This repository is therefore forked from the newer upstream revision, so users do not need to locate or check out an older commit.

### Directory Structure

```text
Waveshare-ESP32-S3-Touch-LCD-3.5B/
├── application/
│   └── edge_agent/
│       ├── boards/
│       │   └── waveshare/
│       │       └── waveshare_ESP32_S3_Touch_LCD_3_5B/
│       │           ├── board_devices.yaml
│       │           ├── board_info.yaml
│       │           ├── board_peripherals.yaml
│       │           ├── sdkconfig.defaults.board
│       │           └── setup_device.c
│       └── main/
│           └── app_fs.c
├── components/
│   ├── claw_modules/
│   │   └── claw_event_router/
│   │       └── src/
│   │           └── claw_event_router.c
│   └── common/
│       └── display_service/
│           ├── Kconfig.projbuild
│           └── src/
│               └── display_service.c
└── tools/
    ├── patch_force_full_refresh.py
    └── patch_psram_dma_direct.py
```

A total of 11 files. Their original relative paths are preserved.

### Build Environment

- Windows
- ESP-IDF **v5.5.5** (minimum v5.5.4; ESP-IDF v6.x is not supported)
- Python (required by the patch scripts)

**Keep the project path as short as possible.**

Windows has a 32K command-line length limit. Long project paths may cause build commands to fail. Placing the project directly in the drive root is recommended, for example:

`C:\esp-claw`

### Get the Source and Apply the Adaptation

Clone this fork:

```powershell
git clone https://github.com/soarjohnsteed/esp-claw.git
cd esp-claw
```

You can try a newer upstream version, but compatibility is not guaranteed.

Copy the contents of `Waveshare-ESP32-S3-Touch-LCD-3.5B/` into the project root, overwriting the corresponding files:

```powershell
Copy-Item -Path .\Waveshare-ESP32-S3-Touch-LCD-3.5B\* -Destination . -Recurse -Force
```

The adaptation files will be placed in their corresponding `application/`, `components/`, and `tools/` directories.

### Build

Run all commands below in PowerShell.

#### 1. Environment Variables and Working Directory

```powershell
$env:IDF_COMPONENT_REGISTRY_URL = 'https://components.espressif.com/'
$env:IDF_COMPONENT_STORAGE_URL  = 'https://components-file.espressif.com.cn/'
$env:IDF_SKIP_UNUSED_DELETE = '1'

cd .\application\edge_agent
```

#### 2. Remove Previous Configuration

`sdkconfig` must not exist, otherwise the board defaults may not be injected correctly.

```powershell
Remove-Item sdkconfig, sdkconfig.old -Force -ErrorAction SilentlyContinue
Remove-Item build -Recurse -Force -ErrorAction SilentlyContinue
```

#### 3. Generate Board Code

```powershell
idf.py bmgr -c ./boards -b waveshare_ESP32_S3_Touch_LCD_3_5B
```

#### 4. Fix PSRAM DMA Compatibility

The generated code contains the `psram_dma_direct` field, which is only supported in ESP-IDF 6.1 and later. It must be removed to avoid build failures with ESP-IDF 5.5.x.

```powershell
python ..\..\tools\patch_psram_dma_direct.py

findstr /s "psram_dma_direct" components\gen_bmgr_codes\*.c
```

The check should produce no output.

#### 5. Inject Board Defaults

Do not run CMake configuration directly. Explicitly specify the board defaults and reset the target chip configuration.

```powershell
Remove-Item sdkconfig -Force -ErrorAction SilentlyContinue

$env:SDKCONFIG_DEFAULTS = "sdkconfig.defaults;components/gen_bmgr_codes/board_manager.defaults"

idf.py set-target esp32s3
```

Check `sdkconfig`. All four settings below must be present:

```powershell
Select-String -Path sdkconfig -Pattern `
'CONFIG_IDF_TARGET="esp32s3"', `
'FLASHSIZE_16MB=y', `
'SPIRAM_MODE_OCT=y', `
'FLASHMODE_QIO=y'
```

#### 6. Apply the Full-Frame Refresh Patch

This patch modifies the display refresh logic; it is not a regular display service configuration change.

```powershell
python ..\..\tools\patch_force_full_refresh.py
```

Expected output:

```text
...display_manager.c: forced FULL refresh for PANEL_IF_OTHER (patched).
```

If the patch has already been applied:

```text
... already patched - nothing to do.
```

#### 7. Build

```powershell
idf.py build
```

Generated firmware:

`build\edge_agent.bin`

Expected size: approximately **3.3 MB**.

### Flashing

For the first flash, or when switching from another project, erase the entire flash first to remove leftover partition tables and data.

Erase flash:

```powershell
idf.py -p COMx erase-flash
```

Then flash and start the monitor:

```powershell
idf.py -p COMx flash monitor
```

Replace `COMx` with the actual serial port.

### Notes

- Use ESP-IDF v5.5.4 or a later 5.5.x release. Do not use v6.x.
- Do not skip board code generation, the PSRAM DMA patch, or the full-frame refresh patch.
- Remove any existing `sdkconfig` before configuring the project, or board defaults may not take effect.
- When switching to esp-claw from another project, erase the entire flash first.
- This adaptation modifies several shared source files and is not suitable for upstream integration as a standalone board definition. Feel free to use this code if you can make it work for your needs.

### Credits

- [esp-claw](https://github.com/espressif/esp-claw) — Original project.
- [xiaozhi-esp32](https://github.com/78/xiaozhi-esp32/) — Reference project.
- Authors: [straga](https://github.com/straga), [de-dh](https://github.com/de-dh).
  - [micropython_lcd – JC3248W535](https://github.com/straga/micropython_lcd/tree/master/device/JC3248W535) — QSPI initialization sequence reference.
  - [ESP32-JC3248W535-Micropython-LVGL](https://github.com/de-dh/ESP32-JC3248W535-Micropython-LVGL) — QSPI initialization sequence reference.

---

## 中文

### 这是什么

针对 **Waveshare ESP32-S3-Touch-LCD-3.5B** 的 [esp-claw](https://github.com/espressif/esp-claw) 硬件适配。

显示控制器为 **AXS15231B + QSPI**，需要修改多个公用文件，并调整板级配置和显示刷新逻辑。

本次适配基于 2026 年 11 月的上游版本重新修改，共涉及 11 个文件，集中放在 `Waveshare-ESP32-S3-Touch-LCD-3.5B/` 目录中。

因 2026 年 8 月 31 日的旧版适配不适用于 11 月上游，此版本直接基于较新的代码重新适配，并 Fork 了 11 月的上游版本，避免用户寻找或检出旧版本。

### 目录结构

```text
Waveshare-ESP32-S3-Touch-LCD-3.5B/
├── application/
│   └── edge_agent/
│       ├── boards/
│       │   └── waveshare/
│       │       └── waveshare_ESP32_S3_Touch_LCD_3_5B/
│       │           ├── board_devices.yaml
│       │           ├── board_info.yaml
│       │           ├── board_peripherals.yaml
│       │           ├── sdkconfig.defaults.board
│       │           └── setup_device.c
│       └── main/
│           └── app_fs.c
├── components/
│   ├── claw_modules/
│   │   └── claw_event_router/
│   │       └── src/
│   │           └── claw_event_router.c
│   └── common/
│       └── display_service/
│           ├── Kconfig.projbuild
│           └── src/
│               └── display_service.c
└── tools/
    ├── patch_force_full_refresh.py
    └── patch_psram_dma_direct.py
```

共 11 个文件，保留原始相对路径。

### 编译环境

- Windows
- ESP-IDF **v5.5.5**（最低 v5.5.4，不支持 v6.x）
- Python（供补丁脚本使用）

**项目路径必须尽量短。**

Windows 命令行存在 32K 字符长度限制，过长的项目路径可能导致编译命令失败。建议直接放在磁盘根目录，例如：

`C:\esp-claw`

### 获取源码与适配

克隆本 Fork：

```powershell
git clone https://github.com/soarjohnsteed/esp-claw.git
cd esp-claw
```

也可以尝试上游新版，但不保证能够正常使用。

将 `Waveshare-ESP32-S3-Touch-LCD-3.5B/` 中的全部内容复制到项目根目录，覆盖对应文件：

```powershell
Copy-Item -Path .\Waveshare-ESP32-S3-Touch-LCD-3.5B\* -Destination . -Recurse -Force
```

覆盖后，适配文件将进入对应的 `application/`、`components/` 和 `tools/` 目录。

### 编译

以下操作均在 PowerShell 中执行。

#### 1. 环境变量与工作目录

```powershell
$env:IDF_COMPONENT_REGISTRY_URL = 'https://components.espressif.com/'
$env:IDF_COMPONENT_STORAGE_URL  = 'https://components-file.espressif.com.cn/'
$env:IDF_SKIP_UNUSED_DELETE = '1'

cd .\application\edge_agent
```

#### 2. 清理旧配置

`sdkconfig` 必须不存在，否则板级默认配置可能无法正确注入。

```powershell
Remove-Item sdkconfig, sdkconfig.old -Force -ErrorAction SilentlyContinue
Remove-Item build -Recurse -Force -ErrorAction SilentlyContinue
```

#### 3. 生成板级代码

```powershell
idf.py bmgr -c ./boards -b waveshare_ESP32_S3_Touch_LCD_3_5B
```

#### 4. 修正 PSRAM DMA 兼容性

生成代码中包含 IDF 6.1+ 才支持的 `psram_dma_direct` 字段，需要先移除，否则会阻断 IDF 5.5.x 编译。

```powershell
python ..\..\tools\patch_psram_dma_direct.py

findstr /s "psram_dma_direct" components\gen_bmgr_codes\*.c
```

检查结果应无输出。

#### 5. 注入板级默认配置

不要直接使用裸 CMake 配置。必须显式指定板级默认配置，并重新设置目标芯片。

```powershell
Remove-Item sdkconfig -Force -ErrorAction SilentlyContinue

$env:SDKCONFIG_DEFAULTS = "sdkconfig.defaults;components/gen_bmgr_codes/board_manager.defaults"

idf.py set-target esp32s3
```

检查 `sdkconfig`，以下四项必须命中：

```powershell
Select-String -Path sdkconfig -Pattern `
'CONFIG_IDF_TARGET="esp32s3"', `
'FLASHSIZE_16MB=y', `
'SPIRAM_MODE_OCT=y', `
'FLASHMODE_QIO=y'
```

#### 6. 应用全帧刷新补丁

这是针对显示刷新逻辑的适配，不是修改 display service 的普通配置。

```powershell
python ..\..\tools\patch_force_full_refresh.py
```

预期输出：

```text
...display_manager.c: forced FULL refresh for PANEL_IF_OTHER (patched).
```

如果已经应用过：

```text
... already patched - nothing to do.
```

#### 7. 编译

```powershell
idf.py build
```

生成固件：

`build\edge_agent.bin`

预期大小约 **3.3 MB**。

### 烧录

首次烧录，或者此前烧录过其他项目，必须先整片擦除，以清除不同项目遗留的分区表和数据。

擦除 Flash：

```powershell
idf.py -p COMx erase-flash
```

然后烧录并启动串口监视器：

```powershell
idf.py -p COMx flash monitor
```

将 `COMx` 替换为实际串口号。

### 注意事项

- ESP-IDF 必须使用 v5.5.4 或更高的 5.5.x 版本，不要使用 v6.x。
- 不要跳过板级代码生成、PSRAM DMA 补丁或全帧刷新补丁。
- 配置项目之前不要保留旧的 `sdkconfig`，否则可能导致板级默认参数未生效。
- 从其他项目切换到 esp-claw 时，首次烧录必须先整片擦除。
- 本适配涉及多个公用文件，不适合直接作为独立板定义合并到上游。如果你能解决，请随意使用本项目代码。

### 致谢

- [esp-claw](https://github.com/espressif/esp-claw) —— 项目本体。
- [xiaozhi-esp32](https://github.com/78/xiaozhi-esp32/) —— 参考项目。
- 作者：[straga](https://github.com/straga)、[de-dh](https://github.com/de-dh)。
  - [micropython_lcd – JC3248W535](https://github.com/straga/micropython_lcd/tree/master/device/JC3248W535) —— QSPI 初始化序列参考。
  - [ESP32-JC3248W535-Micropython-LVGL](https://github.com/de-dh/ESP32-JC3248W535-Micropython-LVGL) —— QSPI 初始化序列参考。
