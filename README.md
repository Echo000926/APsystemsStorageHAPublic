# APsystems 储能系统(LAKE) Home Assistant 集成

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Maintenance](https://img.shields.io/maintenance/yes/2026)]()

<img src="https://github.com/HAEdwin/homeassistant-apsystems_ecu_reader/blob/main/apsystemslogo.png?raw=true" width="3%"> **APsystems Storage**

> ⚠️ **注意**: 本集成仅适用于 **APsystems 储能系统**（如 LAKE 系列）。
> 如果您使用的是光伏微逆系统（ECU-B/R/C），请使用 [APsystems ECU Reader](https://github.com/HAEdwin/homeassistant-apsystems_ecu_reader)。
> 如果您使用的是 EZ1 微逆，请使用 HA 官方集成 [APsystems](https://www.home-assistant.io/integrations/apsystems/)。

## 概述

APsystems Storage 是一个用于与 APsystems 储能设备（LAKE 系列）进行本地通信的 Home Assistant 自定义集成。它通过设备的本地 HTTP API 实现实时监控与配置管理，无需依赖云端服务。

### 核心特性

-   📡 **纯本地控制**: 直接通过局域网 IP 与设备通信，响应迅速且稳定。
-   🔋 **全面能源监控**: 实时获取电池 SOC、温度、充放电功率、累计充放电量及并网/离网功率数据。
-   ⚙️ **深度配置管理**: 支持在 HA 内直接修改运行模式、功率限制、放电深度 (DoD) 及备用充电功率。
-   🕒 **时段策略配置**: 提供 JSON 格式的文本实体，允许高级用户自定义复杂的充放电时段策略。
-   🛡️ **完整告警诊断**: 集成电池过温/欠压/过流、通信错误、系统故障等 15+ 种状态告警传感器。
-   ✅ **批量确认机制**: 采用“本地暂存 + 手动确认”的设计，避免误操作，所有配置更改需点击确认按钮后才会写入设备。
-   🔄 **乐观更新**: 配置下发后立即更新 UI 状态并自动刷新设备数据，提供流畅的操作体验。

## 支持设备

| 设备类型 | 型号示例 | 备注 |
| :--- | :--- | :--- |
| 储能一体机 | LAKE 系列 | ✅ 完全支持 |
| 光伏微逆 ECU | ECU-B / ECU-R / ECU-C | ❌ 不支持 (请使用 ECU Reader) |
| EZ1 微逆 | EZ1-M | ❌ 不支持 (请使用官方集成) |

## 前置要求

-   Home Assistant 已安装 HACS。
-   储能设备已连接至局域网并分配了 **固定 IP 地址**。
-   Home Assistant 能够通过网络访问该设备的 HTTP 端口（默认 80）。
-   确保没有其他自动化或集成频繁占用设备通信接口。

## 安装

### 通过 HACS 安装

1.  打开 HACS → 集成 → 点击右上角菜单 → 自定义仓库。
2.  添加本集成的 GitHub 仓库地址。
3.  搜索 "APsystems Storage" 并下载。
4.  重启 Home Assistant。
5.  前往 **设置** → **设备与服务** → **+ 添加集成** → 搜索 "APsystems Storage"。

## 配置选项

### 初始配置

在添加集成时，您需要提供以下信息：

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| IP Address | 储能设备的局域网 IP 地址 | - |
| Port | 设备 HTTP API 端口 | 80 |

> 💡 集成会在创建前自动测试连接。如果无法连接，请检查 IP 地址、端口及网络连通性。

### 重新配置

支持在不删除集成的情况下修改 IP 和端口设置。进入集成页面 → 点击三点菜单 → 重新配置。

## 实体说明

本集成提供以下类型的实体，分为 **监控类** 和 **配置类** 两大类别：

### 📊 监控传感器 (Sensors)

| 实体名称 | 单位 | 说明 |
| :--- | :--- | :--- |
| Battery SOC | % | 电池剩余电量 |
| Battery Power | W | 电池实时充放电功率 |
| Battery Temperature | °C | 电池温度 |
| Device Temperature | °C | 设备机内温度 |
| On-grid Power | W | 并网侧实时功率 |
| Off-grid Power | W | 离网侧实时功率 |
| Battery Accumulated Charge Energy | kWh | 电池累计充电量 |
| Battery Accumulated Discharge Energy | kWh | 电池累计放电量 |
| On-grid Accumulated Output/Input Energy | kWh | 并网累计输出/输入电量 |
| Off-grid Accumulated Output/Input Energy | kWh | 离网累计输出/输入电量 |
| Battery Capacity | kWh | 电池额定容量 |
| Battery Manufacturer / Model | - | 电池厂商及型号信息 |
| Battery Status | - | 电池工作状态 |

### 🔧 配置实体 (Config Entities)

> ⚠️ **重要提示**: 所有配置实体的修改均为 **本地暂存**，UI 上会显示 `*` 标记。必须点击对应的 **Confirm** 按钮后，更改才会真正写入设备。

#### 开关 (Switch)

| 实体 | 说明 |
| :--- | :--- |
| Eco Mode | 节能模式开关 |
| Off-grid On Hold | 离网保持开启开关 |
| Control Panel Mode | 控制面板模式开关 |

#### 选择器 (Select)

| 实体 | 可选值 | 说明 |
| :--- | :--- | :--- |
| Operating Mode | AI Mode / Self Consumption / Time of Use / Backup | 系统运行模式 |
| Power Limit | 800W / 2500W | 功率上限设置 |

#### 数值 (Number)

| 实体 | 范围 | 单位 | 说明 |
| :--- | :--- | :--- | :--- |
| Depth of Discharge | 15 - 100 | % | 放电深度设置 |
| Backup Charge Power | 0 - 2500 | W | 备用模式充电功率 |

#### 文本 (Text)

| 实体 | 格式 | 说明 |
| :--- | :--- | :--- |
| Time Configuration | JSON Array | 运行模式时段策略配置 |
| Control Panel Configuration | JSON Object | 控制面板时段策略配置 |

#### 按钮 (Button)

| 实体 | 说明 |
| :--- | :--- |
| Confirm Modes Settings | 将上述所有模式相关配置批量写入设备 |
| Confirm Control Panels Settings | 将控制面板相关配置批量写入设备 |

### 🔔 诊断告警 (Diagnostic)

集成提供完整的设备告警状态，包括：电池过温/低温、过压/欠压、过流、通信错误、内部错误、设备温度保护、系统错误、电池关机、并网异常、离网过流/短路、电池容量校准等。这些实体默认归类于 Diagnostic 分类。

## 工作原理

```text
┌─────────────┐     HTTP GET      ┌──────────────────┐
│             │ ◄──────────────── │                  │
│  Home       │                   │  APsystems       │
│  Assistant  │     HTTP POST     │  Storage Device  │
│             │ ────────────────► │  (ELS/ELT)       │
└─────────────┘   (Confirm Only)  └──────────────────┘
```

### 本集成采用 “本地暂存 + 批量确认 + 乐观更新” 三阶段设计，确保配置安全与用户体验兼得：

1.  数据采集: Coordinator 定期轮询 /devices, /alarms, /energies, /modes, /control-panels 五个端点。
2.  本地暂存: 用户在 UI 修改配置时，变更仅保存在内存中，实体名称显示 * 标记。
3.  批量提交: 用户点击 Confirm 按钮后，集成收集所有暂存的配置项，组装为统一 payload 发送至设备。
4.  乐观更新: 提交成功后立即更新 Coordinator 数据并清除所有暂存标记，随后触发一次即时刷新以同步设备真实状态。


💡 此设计显著降低通信频率（避免每改一项就发请求），提升稳定性，并提供清晰的操作反馈。

## 故障排除

表格

| 问题现象       | 可能原因                                      | 解决方案                                                                 |
|----------------|---------------------------------------------|--------------------------------------------------------------------------|
| 无法连接设备   | • IP 地址错误 / 端口非 80<br>• 设备未启用 HTTP API<br>• 防火墙/路由器拦截 | 1. 在 HA 中 `ping <设备IP>`<br>2. 浏览器访问 `http://<设备IP>` 确认网页可打开<br>3. 检查设备 Web 界面 → 设置 → 网络 → 确保 “HTTP 服务” 已启用 |
| 配置写入失败   | • JSON 格式错误（尤其 Time Configuration）<br>• 设备忙（正在处理其他请求） | 1. 使用 JSONLint 校验 Text 实体内容<br>2. 等待 30 秒后重试|




