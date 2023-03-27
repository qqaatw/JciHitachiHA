<!-- This file is heavily inspired by https://github.com/github/docs/blob/main/CONTRIBUTING.md-->
# Welcome to JciHitachiHA contributing guide

Thank you for investing your time in contributing to Jci-Hitachi Home Assistant Integration!

<!--Read our [Code of Conduct](./CODE_OF_CONDUCT.md) to keep our community approachable and respectable.-->

In this guide you will get an overview of the contribution workflow from opening an issue, creating a PR, reviewing, and merging the PR.

<!--Use the table of contents icon <img src="./assets/images/table-of-contents.png" width="25" height="25" /> on the top left corner of this document to get to a specific section of this guide quickly.-->

## New contributor guide

To get an overview of the project, read the [README](README.md). Here are some resources to help you get started with open source contributions:

- [Finding ways to contribute to open source on GitHub](https://docs.github.com/en/get-started/exploring-projects-on-github/finding-ways-to-contribute-to-open-source-on-github)
- [Set up Git](https://docs.github.com/en/get-started/quickstart/set-up-git)
- [Collaborating with pull requests](https://docs.github.com/en/github/collaborating-with-pull-requests)


## Getting started

Please be informed that the project owner and contributors are unpaid volunteers who devote their time building this project and dependencies. We are not affiliated with Jci-Hitachi and therefore do not have a comprehensive understanding of the Hitachi IoT's full picture.

### Issues

If you are having trouble with controlling your devices or have questions, suggestions, feature requests, please open an issue.

In addition to the content in question, the issue should include your environment information, included but not limited to device models, Internet connection type, HA system information.

Please be patient while waiting replies from maintainers and understnad the fact that not all the issues occurring on your side are resolvable.


### Codebase

The codebase of the project is constructed by two git repositories, [JcihitachiHA](https://github.com/qqaatw/JciHitachiHA) and [LibJciHitachi](https://github.com/qqaatw/LibJciHitachi). The former one, i.e. the integration, is responsible for constructing Home Assistant (HA) entities for each Jci-Hitachi device and integrated into your HA system. To connect to the Hitachi cloud, retrieve your device info, as well as send commands to your devices, the integration relies on LibJciHitachi, i.e. the backend, a Python library for controlling Jci-Hitachi devices.

### Adding a new entity for a device

To add an entity, you should first make sure the functionality of the entity to be added is supported by the official Hitachi app, meaning that it shows on or is controllable by the app.

Then, navigate to LibJciHitachi and check if the functionality is in the `STATUS_DICT` variable in [JciHitachi/model.py](https://github.com/qqaatw/LibJciHitachi/blob/master/JciHitachi/model.py/). If so, this functionality/status is already supported by the backend. You could then create a new entity by copying other existing entities in the corresponding `.py` file as a template and access its status value using `self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name].status_name` in JciHitachiHA.

Otherwise, (Under construction.)