# Jci-Hitachi Home Assistant Integration

**Help wanted: I've been developing the heat exchanger support, but I've no such device to test its functionality. If you want to help with the development, please contact me via email: `qqaatw[a-t]gmail.com`. Thank you.**

**Help wanted: 我目前正在開發支援全熱交換機，但是沒有裝置可以測試。若您願意協助此功能的開發，請透過email: `qqaatw[a-t]gmail.com` 聯繫我。Thank you.**

## Feature
A home assistant integration for controlling Jci Hitachi devices, using [LibJciHitachi](https://github.com/qqaatw/LibJciHitachi) backend.

## Installation

### Configuring via UI

1. Create `config/custom_components` folder if not existing.
2. Copy `jcihitachi_tw` into `custom_components` folder.
3. Click `Configuration` button on the left side of Home Assistant panel, and then click `Integrations` tab.
4. Click `ADD INTEGRATION` button at the bottom right corner and follow the UI.

### Configuring via `configuration.yaml`

1. Create `config/custom_components` folder if not existing.
2. Copy `jcihitachi_tw` into `custom_components` folder.
3. Configure your email address, password, and device names, in `config/configuration.yaml`. If device names are not provided, they will be fetched from the API automatically. (not recommended.)
4. Restart Home Assistant.

*An example of `configuration.yaml` can be found [here](configuration.yaml).*

## Supported devices

*支援以下使用日立雲端模組(雲端智慧控)的機種與功能*

- Hitachi Air Conditioner 日立一對一冷氣
  - Power 電源
  - Mode 運轉模式
  - Air speed 風速
  - Vertical wind swingable 導風板垂直擺動 (Untested)
  - Vertical wind direction 導風板垂直方向 (Untested)
  - Horizontal wind direction 導風板水平方向 (Untested)
  - Target temperature 目標溫度
  - Indoor temperature 室內溫度
  - Mold prevention 機體防霉
  - Energy saving 節電
  - Fast operation 快速運轉
  - Power consumption 用電統計 (supports HA core v2021.9.0+)
  - Monthly power consumption 月用電統計
  - ~~Sleep timer 睡眠計時器~~ (Only supported by LibJciHitachi)
- Hitachi Dehumidifier 日立除濕機
  - Power 電源
  - Mode 運轉模式
  - Air speed 風速
  - Wind swingable 導風板擺動
  - Target humidity 目標濕度
  - Indoor humidity 室內溼度
  - Water full warning 滿水警示
  - Error warning 錯誤警示
  - Clean filter notify 濾網清潔通知
  - Mold prevention 機體防霉
  - PM2.5 value PM2.5數值
  - Odor level 異味等級
  - Air cleaning filter setting 空氣清淨濾網設定
  - Power consumption 用電統計 (supports HA core v2021.9.0+)
  - Monthly power consumption 月用電統計
  - ~~Sound control 聲音控制~~ (Only supported by LibJciHitachi)
  - ~~Display brightness 顯示器亮度~~ (Only supported by LibJciHitachi)
  - ~~Side vent 側吹~~ (Only supported by LibJciHitachi)
- ~~Hitachi HeatExchanger 日立全熱交換機~~ (Under development)

## Tested devices

### Air conditioner

- RAD-90NJF / RAC-90NK1
- RAC-63NK
- RAS-50NJF / RAC-50NK
- RAS-36NJF / RAC-36NK
- RAS-36NK  / RAC-36NK1
- RAS-28NJF / RAC-28NK
- RAS-28NB / RAC-28NB
- RA-36NV1

### Dehumidifier

- RD-360HH
- RD-240HH
- RD-200HH

## Known issues

1. Clean filter notification of the dehumidifier doesn't work now.

## License

Apache License 2.0
