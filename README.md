# Jci-Hitachi Home Assistant Integration

**Help wanted: I've been developing dehumidifier and heat exchanger supports, but I've no such device to test their functionality. If you want to help with the development, please contact me via email: `qqaatw[a-t]gmail.com`. Thank you.**

**Help wanted: 我目前正在開發支援除濕機以及全熱交換機，但是沒有裝置可以測試。若您願意協助此功能的開發，請透過email: `qqaatw[a-t]gmail.com` 聯繫我。Thank you.**

## Feature
A home assistant integration for controlling Jci Hitachi devices, using [LibJciHitachi](https://github.com/qqaatw/LibJciHitachi) backend.

## Installation

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
  - Target temperature 目標溫度
  - Indoor temperature 室內溫度
  - Outdoor temperature 室外溫度
  - Mold prevention 機體防霉
  - Energy saving 節電
  - Fast operation 快速運轉
  - ~~Sleep timer 睡眠計時器~~ (Only supported by LibJciHitachi)
- ~~Hitachi Dehumidifier 日立除濕機~~ (Under development)
- ~~Hitachi HeatExchanger 日立全熱交換機~~ (Under development)

## Tested devices

- RAD-90NJF / RAC-90NK1
- RAC-63NK
- RAS-50NJF / RAC-50NK
- RAS-36NJF / RAC-36NK
- RAS-36NK  / RAC-36NK1
- RAS-28NJF / RAC-28NK

## Known issues

  Currently none.

## License

Apache License 2.0