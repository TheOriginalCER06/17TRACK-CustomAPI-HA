# 17TRACK Home Assistant Integration

⚠️ **DISCLAIMER**  
This integration was **AI GENERATED** with the assistance of a large language model and has not been reviewed, endorsed, or supported by 17TRACK or the Home Assistant project.

---
## Badges

![HACS Default](https://img.shields.io/badge/HACS-Default-orange?logo=home-assistant)
![Release](https://img.shields.io/github/v/release/TheOriginalCER06/17TRACK-CustomAPI-HA?color=brightgreen)

---

## Features

- Track packages using the 17TRACK API
- One sensor per package
- Package list summary sensor
- Manual refresh button
- Per-package refresh service
- Delivery event for automations
- Configurable polling interval
- Dashboard-based package adding (auto-creates helper)
- Home Assistant device grouping
- HACS-ready structure

---

## Installation

### HACS (recommended)

1. Go to **HACS → Integrations** in Home Assistant
2. Click the **three dots** in the top right corner → **Custom repositories**
3. Add the repository URL: https://github.com/TheOriginalCER06/17TRACK-CustomAPI-HA
4. Set **Category** to **Integration**  
5. Click **Add**
6. Search for **17TRACK** in HACS and install it
7. Restart Home Assistant
8. Go to **Settings → Devices & Services → Add Integration → 17TRACK** and enter your Security Key

> HACS will automatically install the latest **tagged release** (e.g., v1.1.0).  
> You can also select older releases if needed.

### Manual Installation

1. Copy `custom_components/track17` into your Home Assistant config directory
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration**
4. Search for **17TRACK**
5. Enter your 17TRACK Security Key

---

## Services

### Add a package
```yaml
service: track17.add_package
data:
  tracking_number: LP123456789CN
```
### Refresh a package
```yaml
service: track17.refresh_package
data:
  tracking_number: LP123456789CN
```
### Refresh all packages
```yaml
service: track17.refresh_all_packages
```

## Dashboard: Add package from UI

The integration will automatically create the following helper:
``` yaml
Type: Text
Entity ID: input_text.track17_new_package
Max length: 40
```
Add this to your dashboard:
```yaml
type: vertical-stack
cards:
  - type: entities
    entities:
      - entity: input_text.track17_new_package
        name: Tracking number

  - type: button
    name: Add package
    icon: mdi:package-variant
    tap_action:
      action: call-service
      service: track17.add_package
      service_data:
        tracking_number: "{{ states('input_text.track17_new_package') }}"
```

## Automation Examples

### Notify on delivery

```yaml
automation:
  - alias: Package Delivered
    trigger:
      - platform: event
        event_type: track17_delivered
    action:
      - service: notify.notify
        data:
          message: >
            Package {{ trigger.event.data.tracking_number }} has been delivered!
```

### Refresh single package daily

```yaml
automation:
  - alias: Refresh Single Package
    trigger:
      - platform: time
        at: "03:00:00"
    action:
      - service: track17.refresh_package
        data:
          tracking_number: LP123456789CN
```

### Remove delivered packages weekly

```yaml
automation:
  - alias: Remove Delivered Packages
    trigger:
      - platform: time
        at: "03:00:00"
        weekday:
          - mon
    action:
      - service: track17.remove_delivered_packages
```


## Release Notes
### 1.1.1
- Auto create `input_text` helper for adding packages from the dashboard