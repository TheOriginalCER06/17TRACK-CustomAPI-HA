# 17TRACK Home Assistant Integration

⚠️ **DISCLAIMER**  
This integration was **AI GENERATED** with the assistance of a large language model and has not been reviewed, endorsed, or supported by 17TRACK or the Home Assistant project.

---

## Features

- Track packages using the 17TRACK API
- One sensor per package
- Package list summary sensor
- Manual refresh button
- Per-package refresh service
- Delivery event for automations
- Configurable polling interval
- Dashboard-based package adding
- Home Assistant device grouping
- HACS-ready structure

---

## Installation

### Manual

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
### Remove a package
```yaml
service: track17.remove_package
data:
  tracking_number: LP123456789CN
```
### Refresh a package
```yaml
service: track17.refresh_package
data:
  tracking_number: LP123456789CN
```

## Adding packages from the dashboard

Create a helper:

```yaml
- Type: Text
- Entity ID: `input_text.track17_new_package`
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
    tap_action:
      action: call-service
      service: track17.add_package
      service_data:
        tracking_number: "{{ states('input_text.track17_new_package') }}"
      - entity: input_text.track17_new_package
        name: Tracking number

  - type: button
    name: Add package
    tap_action:
      action: call-service
      service: track17.add_package
      service_data:
        tracking_number: "{{ states('input_text.track17_new_package') }}"
```

When you enter a tracking number and press the button, the package will be added to the integration.

