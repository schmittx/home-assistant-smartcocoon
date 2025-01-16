[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
# Smart Cocoon Home Assistant Integration
Custom component to allow control of [Smart Cocoon devices](https://mysmartcocoon.com) in [Home Assistant](https://home-assistant.io).

## Features
- This is a small integration to allow basic control (mode and fan speed) via Home Assistant.
- A `binary_sensor`, `fan`, and two `select` entities will be created for each booster fan.

## Install
1. Ensure Home Assistant is updated to version 2025.1.0 or newer.
2. Use HACS and add as a [custom repo](https://hacs.xyz/docs/faq/custom_repositories); or download and manually move to the `custom_components` folder.
3. Once the integration is installed follow the standard process to setup via UI and search for `Smart Cocoon`.
4. Follow the prompts.

## Options
- Systems and fans can be updated via integration options.
- If `Advanced Mode` is enabled for the current profile, additional options are available (interval, timeout, and response logging).

## Future Plans
- Temperature feedback and control if mode is set to `auto`
