"""
Example Integration - Voice + Sensor System

This example shows how to integrate the sensor monitor with the voice service
to create a reactive robot personality.

The robot will:
1. Detect physical interactions (push, pet, lift, fall)
2. Trigger voice responses for each interaction
3. Make idle comments when nothing is happening

Run with: python3 example_integration.py --robot-ip 192.168.12.1
"""
import asyncio
import argparse
from sensor_monitor import SensorMonitor, SensorEvent
from voice_service import VoiceService, VoiceEvent


# Map sensor events to voice events
SENSOR_TO_VOICE = {
    SensorEvent.PUSHED: VoiceEvent.PUSHED,
    SensorEvent.PETTED: VoiceEvent.PETTED,
    SensorEvent.LIFTED: VoiceEvent.LIFTED,
    SensorEvent.FALL_DETECTED: VoiceEvent.FALL_DOWN,
    SensorEvent.RECOVERED: VoiceEvent.RECOVERY_STAND,
    SensorEvent.SHAKE_DETECTED: VoiceEvent.ANGRY,
    SensorEvent.TOUCHED: VoiceEvent.TOUCHED,
}


class RobotVoiceSystem:
    """
    Complete voice + sensor integration for Go2.

    Combines sensor monitoring with voice responses to create
    a reactive personality system.
    """

    def __init__(
        self,
        robot_ip: str = "192.168.12.1",
        robot_password: str = "123",
        idle_interval: float = 15.0,
    ):
        self.robot_ip = robot_ip
        self.robot_password = robot_password
        self.idle_interval = idle_interval

        # Initialize services
        self.voice = VoiceService()
        self.voice.config.idle_interval = idle_interval

        self.sensor = SensorMonitor(
            robot_ip=robot_ip,
            robot_password=robot_password,
        )

        # Track state
        self._running = False
        self._last_activity_time = 0

    async def start(self):
        """Start the voice + sensor system."""
        if self._running:
            return

        self._running = True
        print(f"Starting voice system for robot at {self.robot_ip}")

        # Startup announcement
        await self.voice.trigger(VoiceEvent.STARTUP)

        # Set up sensor callback
        self.sensor.set_event_callback(self._on_sensor_event)

        # Start services
        await self.sensor.start()
        await self.voice.start_idle_loop()

        print("Voice system running - push, pet, or lift the robot!")

    async def stop(self):
        """Stop the voice + sensor system."""
        self._running = False

        await self.voice.trigger(VoiceEvent.SHUTDOWN)
        await self.sensor.stop()
        await self.voice.stop_idle_loop()

        print("Voice system stopped")

    async def _on_sensor_event(self, event: SensorEvent):
        """Handle sensor events and trigger voice responses."""
        # Map sensor event to voice event
        voice_event = SENSOR_TO_VOICE.get(event)

        if voice_event:
            await self.voice.trigger(voice_event)

    async def trigger_trick_voice(self, trick_name: str):
        """Trigger voice for a trick command."""
        trick_voices = {
            "paw": VoiceEvent.TRICK_PAW,
            "shake": VoiceEvent.TRICK_PAW,
            "bow": VoiceEvent.TRICK_BOW,
            "roll_over": VoiceEvent.TRICK_ROLL_OVER,
            "rollover": VoiceEvent.TRICK_ROLL_OVER,
            "play_dead": VoiceEvent.TRICK_PLAY_DEAD,
            "dead": VoiceEvent.TRICK_PLAY_DEAD,
            "spin": VoiceEvent.TRICK_SPIN,
            "handstand": VoiceEvent.TRICK_HANDSTAND,
            "heart": VoiceEvent.TRICK_HEART,
        }

        event = trick_voices.get(trick_name.lower())
        if event:
            await self.voice.trigger(event)

    async def trigger_movement_voice(self, action: str):
        """Trigger voice for movement commands."""
        movement_voices = {
            "sit": VoiceEvent.SIT_DOWN,
            "stand": VoiceEvent.STAND_UP,
            "walk": VoiceEvent.WALK_START,
            "run": VoiceEvent.RUN_START,
            "dance": VoiceEvent.DANCE_START,
            "jump": VoiceEvent.JUMP,
        }

        event = movement_voices.get(action.lower())
        if event:
            await self.voice.trigger(event)


async def main():
    parser = argparse.ArgumentParser(description="Robot Voice System")
    parser.add_argument("--robot-ip", default="192.168.12.1",
                        help="Robot IP address")
    parser.add_argument("--password", default="123",
                        help="Robot SSH password")
    parser.add_argument("--idle-interval", type=float, default=15.0,
                        help="Seconds between idle comments")
    args = parser.parse_args()

    system = RobotVoiceSystem(
        robot_ip=args.robot_ip,
        robot_password=args.password,
        idle_interval=args.idle_interval,
    )

    print("=== Robot Voice System ===")
    print(f"Robot IP: {args.robot_ip}")
    print(f"Idle interval: {args.idle_interval}s")
    print("")

    await system.start()

    try:
        # Run until interrupted
        print("\nPress Ctrl+C to stop\n")
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
