# Unitree Go2 Voice & Interaction System

My implementation for adding personality and voice responses to the Unitree Go2 robot. This system detects physical interactions (pushes, pets, lifts) via IMU sensors and triggers voice responses with a customizable personality.

## What It Does

- **Detects physical interactions** - Push, pet, lift, fall, shake detection via IMU data
- **Triggers voice responses** - Each event triggers a spoken response
- **Personality system** - Sarcastic, playful responses for each action
- **Idle chatter** - Random comments when the robot is idle
- **Event-driven architecture** - Easy to extend with new triggers

## Quick Start

### Sensor Detection

The sensor monitor reads IMU data from the robot to detect physical interactions:

```python
from sensor_monitor import SensorMonitor, SensorEvent

async def on_sensor_event(event: SensorEvent):
    print(f"Detected: {event.value}")

    if event == SensorEvent.PUSHED:
        # Robot was pushed - play angry response
        await play_voice("Hey! Watch it!")
    elif event == SensorEvent.PETTED:
        # Robot is being petted
        await play_voice("Oh that's nice...")

monitor = SensorMonitor(robot_ip="192.168.12.1")
monitor.set_event_callback(on_sensor_event)
await monitor.start()
```

### Voice Events

Trigger voice responses for any robot action:

```python
from voice_service import VoiceService, VoiceEvent

voice = VoiceService()

# When robot does a trick
await voice.trigger(VoiceEvent.TRICK_PAW)

# When robot sits down
await voice.trigger(VoiceEvent.SIT_DOWN)

# Random idle comment
await voice.trigger(VoiceEvent.IDLE)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Your Control Server                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │  Sensor Monitor  │───▶│   Event Router   │───▶│ Voice Service│  │
│  │  (IMU polling)   │    │  (callbacks)     │    │ (TTS output) │  │
│  └──────────────────┘    └──────────────────┘    └──────────────┘  │
│          │                                              │           │
│          │ SSH (get IMU data)                          │ Audio     │
│          ▼                                              ▼           │
├─────────────────────────────────────────────────────────────────────┤
│                        Unitree Go2 Robot                            │
│                     (192.168.12.1 / LAN IP)                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Detection Methods

### Push Detection
Monitors accelerometer data for sudden spikes. When acceleration exceeds threshold (default 5 m/s²), a push is detected.

```python
# Acceleration magnitude (excluding gravity)
accel_mag = sqrt(accel_x² + accel_y² + (accel_z - 9.8)²)

if accel_mag > PUSH_THRESHOLD:
    trigger_event(PUSHED)
```

### Pet Detection
Detects gentle, sustained motion - small accelerations with low angular velocity over time.

```python
# Gentle motion pattern
if 1.0 < accel_mag < 5.0 and 0.1 < gyro_mag < 1.0:
    if sustained_for > 0.5 seconds:
        trigger_event(PETTED)
```

### Lift Detection
When the robot is standing (mode 1) and all foot force sensors read near zero, it's been lifted.

```python
total_foot_force = sum(foot_force[0:4])

if total_foot_force < THRESHOLD and robot_mode == 1:
    trigger_event(LIFTED)
```

### Fall Detection
Extreme roll or pitch angles indicate the robot has fallen over.

```python
if abs(roll) > 60° or abs(pitch) > 60°:
    trigger_event(FALL_DETECTED)
```

## Files

```
├── sensor_monitor.py      # IMU sensor polling and event detection
├── voice_service.py       # Voice event system with personality responses
├── example_integration.py # Full example integrating both systems
└── systemd/
    └── voice-service.service  # Optional systemd service file
```

## Installation

### Windows 10

1. Open a Command Prompt in the repository folder.
2. Run:

```bat
install_windows.bat
```

3. Start the service with:

```bat
run_voice_service.bat
```

You can override the robot connection settings with environment variables:

```bat
set ROBOT_IP=10.0.0.148
set ROBOT_PASSWORD=123
set IDLE_INTERVAL=20
run_voice_service.bat
```

### Linux / macOS

### 1. Copy files to your server

```bash
scp sensor_monitor.py voice_service.py root@<server_ip>:/opt/voice-control/
```

### 2. Install dependencies

```bash
pip install asyncio structlog
```

### 3. Configure robot IP

Set the robot's LAN IP in your code or environment:

```python
monitor = SensorMonitor(robot_ip="10.0.0.148")  # Your robot's LAN IP
```

### 4. Run the service

```bash
python3 example_integration.py
```

## Voice Events Reference

### System Events
| Event | Trigger | Example Response |
|-------|---------|------------------|
| `STARTUP` | System starts | "Systems online. Let's do this." |
| `SHUTDOWN` | System stopping | "Powering down. Don't forget about me." |
| `ERROR` | System error | "Something went wrong..." |

### Battery Events
| Event | Trigger | Example Response |
|-------|---------|------------------|
| `BATTERY_FULL` | 100% charge | "Fully charged and ready!" |
| `BATTERY_LOW` | < 20% | "Running low on power here..." |
| `BATTERY_CRITICAL` | < 10% | "Need to charge, now!" |
| `CHARGING_START` | Plugged in | "Ahh, sweet electricity." |
| `CHARGING_COMPLETE` | Fully charged | "All charged up!" |

### Movement Events
| Event | Trigger | Example Response |
|-------|---------|------------------|
| `SIT_DOWN` | Robot sits | "Fine, I'll sit. Happy now?" |
| `STAND_UP` | Robot stands | "Alright, I'm up. What do you want?" |
| `WALK_START` | Walking begins | "Here we go, walking again..." |
| `RUN_START` | Running begins | "Let's go fast!" |
| `DANCE_START` | Dance triggered | "Oh, we're doing this? Okay..." |
| `FALL_DOWN` | Robot falls | "I meant to do that." |
| `RECOVERY_STAND` | Gets back up | "I'm fine, I'm fine..." |
| `JUMP` | Robot jumps | "Wheee!" |

### Trick Events
| Event | Trigger | Example Response |
|-------|---------|------------------|
| `TRICK_PAW` | Shake paw | "Here's my paw. You're welcome." |
| `TRICK_BOW` | Bow gesture | "I bow to no one... except right now." |
| `TRICK_ROLL_OVER` | Roll over | "This is beneath me, literally." |
| `TRICK_PLAY_DEAD` | Play dead | "I'm dead. Very dramatic." |
| `TRICK_SPIN` | Spin around | "Wheee... okay I'm dizzy now." |
| `TRICK_HANDSTAND` | Handstand | "Look ma, no... legs?" |
| `TRICK_HEART` | Heart gesture | "A heart for you. Don't let it go to your head." |
| `TRICK_REFUSED` | Trick failed | "Yeah, I'm not doing that." |

### Physical Interaction Events
| Event | Trigger | Example Response |
|-------|---------|------------------|
| `PUSHED` | IMU detects push | "Push me again, I dare you!" |
| `PETTED` | Gentle sustained touch | "Oh, that's actually nice..." |
| `LIFTED` | Picked up | "Put me down! I have legs!" |
| `TOUCHED` | Brief contact | "Hey! Personal space!" |

### Emotional/Idle Events
| Event | Trigger | Example Response |
|-------|---------|------------------|
| `IDLE` | No activity for X seconds | Random sarcastic comment |
| `HAPPY` | Positive interaction | "This is great!" |
| `BORED` | Extended idle | "So... we just standing here?" |
| `ANGRY` | Repeated pushing | "I'm getting real tired of this." |

### Guard/Patrol Events
| Event | Trigger | Example Response |
|-------|---------|------------------|
| `GUARD_MODE` | Guard mode active | "Security protocol activated." |
| `PATROL_START` | Patrol begins | "Beginning patrol route." |
| `INTRUDER_ALERT` | Unknown detected | "Alert! Unknown presence detected!" |

## Customizing Responses

Each event has multiple response options. The system randomly selects one:

```python
PERSONALITY_RESPONSES = {
    VoiceEvent.PUSHED: [
        "Push me again, I dare you!",
        "Oh you wanna go? Let's go!",
        "That's strike one, buddy.",
        "I'm gonna remember that.",
    ],
    VoiceEvent.IDLE: [
        "So we just standing here or what?",
        "I could be doing literally anything else.",
        "This is riveting, truly.",
    ],
}
```

Add your own personality by modifying the `PERSONALITY_RESPONSES` dictionary.

## Tuning Detection Thresholds

Adjust these values in `sensor_monitor.py` to tune sensitivity:

```python
class SensorMonitor:
    # Push detection - lower = more sensitive
    PUSH_ACCEL_THRESHOLD = 5.0      # m/s²

    # Shake detection
    SHAKE_GYRO_THRESHOLD = 3.0      # rad/s

    # Fall detection angles
    FALL_ROLL_THRESHOLD = 60.0      # degrees
    FALL_PITCH_THRESHOLD = 60.0     # degrees

    # Lift detection - minimum foot force when standing
    LIFT_FOOT_THRESHOLD = 5.0       # Newtons

    # Pet detection - duration of gentle touch
    TOUCH_DURATION = 0.5            # seconds

    # Event cooldowns - prevent spam
    EVENT_COOLDOWNS = {
        SensorEvent.PUSHED: 3.0,    # 3 seconds between push events
        SensorEvent.PETTED: 5.0,
        SensorEvent.LIFTED: 5.0,
    }
```

## My Setup

I run this as part of my home automation setup:

- **Server**: Always-on server handles the sensor monitoring and voice synthesis
- **Robot**: Unitree Go2 Pro connected via WiFi
- **TTS**: Using Piper for fast, local text-to-speech

The sensor monitor polls the robot's IMU data via SSH, detects events, and routes them to the voice service. Audio plays through speakers connected to the server or streams to the robot.

I built this because I wanted Biscuit (my Go2) to have personality - not just perform tricks, but react and comment on what's happening. The push detection is great for when friends get too curious with the robot.

## Troubleshooting

**Events not triggering:**
- Check SSH connectivity to robot
- Verify robot IP is correct
- Check IMU data is being received: `python3 -c "from sensor_monitor import *; print('OK')"`

**Too many false positives:**
- Increase `PUSH_ACCEL_THRESHOLD` (default 5.0)
- Increase `EVENT_COOLDOWNS` values

**Events too slow:**
- Decrease `poll_interval` (default 0.1s = 10Hz)
- But don't go below 0.05s to avoid overloading

**No audio playing:**
- Verify TTS service is running
- Check audio output device

## Technical Notes

- IMU polling at 10Hz provides responsive detection without overloading
- Event cooldowns prevent spam (configurable per event type)
- SSH connection uses persistent connection with timeout handling
- Detection algorithms tuned specifically for Go2's sensor characteristics

## License

MIT - Use freely.
