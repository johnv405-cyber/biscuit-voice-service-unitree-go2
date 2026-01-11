"""
Sensor Monitor - Detects physical interactions from IMU data

Monitors the Unitree Go2's IMU sensor data via SSH to detect:
- Push: Sudden acceleration spike
- Pet: Gentle sustained motion
- Lift: All feet off ground while standing
- Fall: Extreme tilt angles
- Shake: High angular velocity

Designed for Go2 robots with SSH access (jailbroken or developer mode).
"""
import asyncio
import subprocess
import json
import time
import math
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass, field
from enum import Enum


class SensorEvent(str, Enum):
    """Physical interaction events detected from sensors."""
    PUSHED = "pushed"
    TOUCHED = "touched"
    LIFTED = "lifted"
    FALL_DETECTED = "fall_detected"
    RECOVERED = "recovered"
    SHAKE_DETECTED = "shake_detected"
    PETTED = "petted"


@dataclass
class IMUState:
    """Current IMU sensor state."""
    # Accelerometer (m/s²) - gravity is ~9.8 on Z when flat
    accel_x: float = 0.0
    accel_y: float = 0.0
    accel_z: float = 9.8

    # Gyroscope (rad/s)
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0

    # Orientation (degrees)
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    # Foot force (N) - 4 feet: FR, FL, RR, RL
    foot_force: List[float] = field(default_factory=lambda: [0, 0, 0, 0])

    # Robot mode (0=sit, 1=stand)
    mode: int = 0

    # Timestamp
    timestamp: float = 0.0


class SensorMonitor:
    """
    Monitors robot sensors and detects physical interactions.

    Thresholds are tuned for Unitree Go2 robot.

    Usage:
        monitor = SensorMonitor(robot_ip="192.168.12.1")
        monitor.set_event_callback(my_callback)
        await monitor.start()
    """

    # Detection thresholds
    PUSH_ACCEL_THRESHOLD = 5.0       # m/s² - acceleration spike for push detection
    SHAKE_GYRO_THRESHOLD = 3.0       # rad/s - angular velocity for shake detection
    FALL_ROLL_THRESHOLD = 60.0       # degrees - roll angle indicating fall
    FALL_PITCH_THRESHOLD = 60.0      # degrees - pitch angle indicating fall
    LIFT_FOOT_THRESHOLD = 5.0        # N - minimum foot force when standing
    TOUCH_DURATION = 0.5             # seconds - sustained contact for touch detection

    # Cooldowns (seconds) - prevent event spam
    EVENT_COOLDOWNS = {
        SensorEvent.PUSHED: 3.0,
        SensorEvent.TOUCHED: 5.0,
        SensorEvent.LIFTED: 5.0,
        SensorEvent.FALL_DETECTED: 10.0,
        SensorEvent.RECOVERED: 5.0,
        SensorEvent.SHAKE_DETECTED: 5.0,
        SensorEvent.PETTED: 5.0,
    }

    # IMU helper script deployed to robot
    IMU_SCRIPT = '''#!/usr/bin/env python3
import sys
sys.path.insert(0, '/unitree/module/pet_go')
from util import sub_sport_state
import json
import time

for _ in range(10):
    s = sub_sport_state()
    if s:
        print(json.dumps({
            'accel': list(s.imu_state.accelerometer),
            'gyro': list(s.imu_state.gyroscope),
            'rpy': list(s.imu_state.rpy),
            'foot': list(s.foot_force),
            'mode': s.mode
        }))
        break
    time.sleep(0.05)
else:
    print('{}')
'''

    def __init__(
        self,
        robot_ip: str = "192.168.12.1",
        robot_password: str = "123",
        poll_interval: float = 0.1,  # 10Hz polling
    ):
        """
        Initialize sensor monitor.

        Args:
            robot_ip: Robot's IP address (192.168.12.1 or LAN IP)
            robot_password: SSH password for root user
            poll_interval: Seconds between sensor polls (default 0.1 = 10Hz)
        """
        self.robot_ip = robot_ip
        self.robot_password = robot_password
        self.poll_interval = poll_interval

        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._state = IMUState()
        self._prev_state = IMUState()

        # Event callback
        self._on_event: Optional[Callable] = None

        # Event timing
        self._last_event_time: Dict[SensorEvent, float] = {}
        self._touch_start_time: Optional[float] = None
        self._was_fallen = False

        # History for spike detection
        self._accel_history: List[float] = []
        self._gyro_history: List[float] = []
        self._history_size = 5

    def set_event_callback(self, callback: Callable):
        """
        Set callback for sensor events.

        Callback signature: async def callback(event: SensorEvent)
        """
        self._on_event = callback

    async def start(self):
        """Start sensor monitoring."""
        if self._running:
            return

        # Deploy helper script to robot
        await self._deploy_imu_script()

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        print(f"Sensor monitor started - polling {self.robot_ip} at {1/self.poll_interval}Hz")

    async def stop(self):
        """Stop sensor monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("Sensor monitor stopped")

    async def _deploy_imu_script(self):
        """Deploy the IMU reading script to the robot."""
        cmd = f"cat > /tmp/get_imu.py << 'IMUEOF'\n{self.IMU_SCRIPT}IMUEOF\nchmod +x /tmp/get_imu.py"
        await self._ssh_command(cmd, timeout=5.0)
        print("IMU helper script deployed to robot")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                # Get latest IMU state from robot
                await self._update_state()

                # Check for events
                await self._check_events()

                # Store previous state
                self._prev_state = IMUState(
                    accel_x=self._state.accel_x,
                    accel_y=self._state.accel_y,
                    accel_z=self._state.accel_z,
                    gyro_x=self._state.gyro_x,
                    gyro_y=self._state.gyro_y,
                    gyro_z=self._state.gyro_z,
                    roll=self._state.roll,
                    pitch=self._state.pitch,
                    yaw=self._state.yaw,
                    foot_force=self._state.foot_force.copy(),
                    mode=self._state.mode,
                    timestamp=self._state.timestamp,
                )

                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Sensor monitor error: {e}")
                await asyncio.sleep(1.0)

    async def _update_state(self):
        """Fetch latest IMU state from robot via SSH."""
        try:
            result = await self._ssh_command("python3 /tmp/get_imu.py 2>/dev/null", timeout=2.0)

            if result and result.strip():
                data = json.loads(result.strip())

                if 'accel' in data:
                    self._state.accel_x = data['accel'][0]
                    self._state.accel_y = data['accel'][1]
                    self._state.accel_z = data['accel'][2]

                if 'gyro' in data:
                    self._state.gyro_x = data['gyro'][0]
                    self._state.gyro_y = data['gyro'][1]
                    self._state.gyro_z = data['gyro'][2]

                if 'rpy' in data:
                    self._state.roll = math.degrees(data['rpy'][0])
                    self._state.pitch = math.degrees(data['rpy'][1])
                    self._state.yaw = math.degrees(data['rpy'][2])

                if 'foot' in data:
                    self._state.foot_force = data['foot']

                if 'mode' in data:
                    self._state.mode = data['mode']

                self._state.timestamp = time.time()

        except Exception as e:
            pass  # Silently ignore fetch failures

    async def _ssh_command(self, command: str, timeout: float = 1.0) -> Optional[str]:
        """Execute SSH command on robot."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "sshpass", "-p", self.robot_password,
                "ssh", "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "ConnectTimeout=1",
                f"root@{self.robot_ip}",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return stdout.decode().strip() if stdout else None

        except asyncio.TimeoutError:
            return None
        except Exception:
            return None

    async def _check_events(self):
        """Check for sensor events based on current state."""
        now = time.time()

        # Calculate acceleration magnitude (excluding gravity)
        accel_mag = math.sqrt(
            self._state.accel_x ** 2 +
            self._state.accel_y ** 2 +
            (self._state.accel_z - 9.8) ** 2
        )

        # Track acceleration history
        self._accel_history.append(accel_mag)
        if len(self._accel_history) > self._history_size:
            self._accel_history.pop(0)

        # Calculate angular velocity magnitude
        gyro_mag = math.sqrt(
            self._state.gyro_x ** 2 +
            self._state.gyro_y ** 2 +
            self._state.gyro_z ** 2
        )

        # Track gyro history
        self._gyro_history.append(gyro_mag)
        if len(self._gyro_history) > self._history_size:
            self._gyro_history.pop(0)

        # 1. PUSH DETECTION - sudden acceleration spike
        if accel_mag > self.PUSH_ACCEL_THRESHOLD:
            if self._can_trigger(SensorEvent.PUSHED, now):
                await self._trigger_event(SensorEvent.PUSHED)

        # 2. SHAKE DETECTION - high angular velocity
        if gyro_mag > self.SHAKE_GYRO_THRESHOLD:
            if self._can_trigger(SensorEvent.SHAKE_DETECTED, now):
                await self._trigger_event(SensorEvent.SHAKE_DETECTED)

        # 3. FALL DETECTION - extreme roll or pitch
        is_fallen = (
            abs(self._state.roll) > self.FALL_ROLL_THRESHOLD or
            abs(self._state.pitch) > self.FALL_PITCH_THRESHOLD
        )

        if is_fallen and not self._was_fallen:
            if self._can_trigger(SensorEvent.FALL_DETECTED, now):
                await self._trigger_event(SensorEvent.FALL_DETECTED)
                self._was_fallen = True
        elif not is_fallen and self._was_fallen:
            if self._can_trigger(SensorEvent.RECOVERED, now):
                await self._trigger_event(SensorEvent.RECOVERED)
                self._was_fallen = False

        # 4. LIFT DETECTION - when standing and all feet lose contact
        total_foot_force = sum(self._state.foot_force)
        if (total_foot_force < self.LIFT_FOOT_THRESHOLD and
            not is_fallen and
            self._state.mode == 1):  # Only when robot is standing
            if self._can_trigger(SensorEvent.LIFTED, now):
                await self._trigger_event(SensorEvent.LIFTED)

        # 5. PET DETECTION - gentle sustained motion
        if 1.0 < accel_mag < 5.0 and 0.1 < gyro_mag < 1.0:
            if self._touch_start_time is None:
                self._touch_start_time = now
            elif now - self._touch_start_time > self.TOUCH_DURATION:
                if self._can_trigger(SensorEvent.PETTED, now):
                    await self._trigger_event(SensorEvent.PETTED)
                    self._touch_start_time = None
        else:
            self._touch_start_time = None

    def _can_trigger(self, event: SensorEvent, now: float) -> bool:
        """Check if event can be triggered (cooldown check)."""
        cooldown = self.EVENT_COOLDOWNS.get(event, 5.0)
        last_time = self._last_event_time.get(event, 0)
        return (now - last_time) >= cooldown

    async def _trigger_event(self, event: SensorEvent):
        """Trigger a sensor event."""
        self._last_event_time[event] = time.time()

        print(f"Event: {event.value} | "
              f"accel=({self._state.accel_x:.1f}, {self._state.accel_y:.1f}, {self._state.accel_z:.1f}) | "
              f"roll={self._state.roll:.1f}° pitch={self._state.pitch:.1f}°")

        if self._on_event:
            try:
                await self._on_event(event)
            except Exception as e:
                print(f"Event callback error: {e}")

    def get_state(self) -> IMUState:
        """Get current sensor state."""
        return self._state

    def get_status(self) -> Dict:
        """Get monitor status."""
        return {
            "running": self._running,
            "robot_ip": self.robot_ip,
            "poll_interval": self.poll_interval,
            "state": {
                "accel": [self._state.accel_x, self._state.accel_y, self._state.accel_z],
                "gyro": [self._state.gyro_x, self._state.gyro_y, self._state.gyro_z],
                "rpy": [self._state.roll, self._state.pitch, self._state.yaw],
                "foot_force": self._state.foot_force,
                "mode": self._state.mode,
            },
            "was_fallen": self._was_fallen,
        }


# Example usage
if __name__ == "__main__":
    async def on_event(event: SensorEvent):
        """Example event handler."""
        if event == SensorEvent.PUSHED:
            print(">>> Robot was pushed!")
        elif event == SensorEvent.PETTED:
            print(">>> Robot is being petted")
        elif event == SensorEvent.LIFTED:
            print(">>> Robot was picked up!")
        elif event == SensorEvent.FALL_DETECTED:
            print(">>> Robot fell over!")
        elif event == SensorEvent.RECOVERED:
            print(">>> Robot recovered from fall")

    async def main():
        print("=== Sensor Monitor Demo ===")
        print("Push, pet, or lift the robot to trigger events")
        print("Press Ctrl+C to stop\n")

        # Create monitor - adjust IP as needed
        monitor = SensorMonitor(
            robot_ip="192.168.12.1",  # Change to your robot's IP
            robot_password="123",     # Change to your robot's password
        )

        # Set callback
        monitor.set_event_callback(on_event)

        # Start monitoring
        await monitor.start()

        try:
            # Run until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            await monitor.stop()

    asyncio.run(main())
