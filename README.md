# Jci-Hitachi Home Assistant Integration

## Feature
A home assistant integration for controlling Jci Hitachi devices, using [LibJciHitachi](https://github.com/qqaatw/LibJciHitachi) backend.

## Installation

1. Create `config/custom_components` folder if not existing.
2. Copy `jcihitachi_tw` into `custom_components` folder.
3. Configure your email address, password, and device names, in `config/configuration.yaml`. If device names are not provided, they will be fetched form the API automatically. (not suggested.)
4. Restart Home Assistant.

## Supported devices

*支援以下使用日立雲端模組(雲端智慧控)的機種與功能*

- Hitachi Air Conditioner 日立一對一冷氣
  - Power 電源
  - Mode 運轉模式
  - Air speed 風速
  - Target temperature 目標溫度
  - Indoor temperature 室內溫度
  - Outdoor temperature 室外溫度
  - Mold prevention 機體防霉
  - Energy saving 節電
  - Fast operation 快速運轉
  - ~~Sleep timer 睡眠計時器~~ (Only supported by LibJciHitachi)
- ~~Hitachi Dehumidifier 日立除濕機~~ (Under development)
- ~~Hitachi HeatExchanger 日立全熱交換機~~ (Under development)

*An example of `configuration.yaml` can be found [here](configuration.yaml).*

## Tested devices

- RAD-90NJF / RAC-90NK1
- RAC-63NK
- RAS-50NJF / RAC-50NK
- RAS-36NJF / RAC-36NK
- RAS-28NJF / RAC-28NK

## Known issues

1. Delayed state update.
    - When a device state has been changed by user, the updated state reported by the API might be delayed for 1~5 sec. So, the user have to wait for it until the state bacomes stable.

## License

Apache License 2.0