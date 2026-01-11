"""
Voice Service - Event-driven voice responses for Unitree Go2

Triggers personality-driven voice responses based on robot events.
Designed to give your robot a Chappie-like sarcastic personality.
"""
import asyncio
import random
from enum import Enum
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass


class VoiceEvent(str, Enum):
    """All possible voice trigger events."""

    # System
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    ERROR = "error"

    # Battery
    BATTERY_FULL = "battery_full"
    BATTERY_LOW = "battery_low"
    BATTERY_CRITICAL = "battery_critical"
    CHARGING_START = "charging_start"
    CHARGING_COMPLETE = "charging_complete"

    # Movement
    SIT_DOWN = "sit_down"
    STAND_UP = "stand_up"
    WALK_START = "walk_start"
    RUN_START = "run_start"
    DANCE_START = "dance_start"
    FALL_DOWN = "fall_down"
    RECOVERY_STAND = "recovery_stand"
    JUMP = "jump"

    # Tricks
    TRICK_PAW = "trick_paw"
    TRICK_BOW = "trick_bow"
    TRICK_ROLL_OVER = "trick_roll_over"
    TRICK_PLAY_DEAD = "trick_play_dead"
    TRICK_SPIN = "trick_spin"
    TRICK_HANDSTAND = "trick_handstand"
    TRICK_HEART = "trick_heart"
    TRICK_REFUSED = "trick_refused"

    # Physical Interaction
    TOUCHED = "touched"
    PUSHED = "pushed"
    PETTED = "petted"
    LIFTED = "lifted"

    # Idle/Emotional
    IDLE = "idle"
    HAPPY = "happy"
    BORED = "bored"
    ANGRY = "angry"

    # Security
    GUARD_MODE = "guard_mode"
    PATROL_START = "patrol_start"
    INTRUDER_ALERT = "intruder_alert"


# Personality responses - sarcastic, playful character
PERSONALITY_RESPONSES: Dict[VoiceEvent, List[str]] = {
    # System events
    VoiceEvent.STARTUP: [
        "Systems online. Let's do this.",
        "I'm awake. What do you need?",
        "Booting up... okay, what's the plan?",
        "Hello world. I'm back.",
    ],
    VoiceEvent.SHUTDOWN: [
        "Powering down. Don't forget about me.",
        "Going to sleep. Try not to miss me too much.",
        "Shutting down. Wake me when something interesting happens.",
    ],
    VoiceEvent.ERROR: [
        "Something went wrong. Don't look at me like that.",
        "Error detected. I'm not saying it was your fault, but...",
        "Oops. Technical difficulties.",
    ],

    # Battery events
    VoiceEvent.BATTERY_FULL: [
        "Fully charged and ready!",
        "Battery at max. Let's go!",
        "100 percent. I feel powerful.",
    ],
    VoiceEvent.BATTERY_LOW: [
        "Running low here, just saying.",
        "Battery's getting low. Hint hint.",
        "I'm at 20 percent. Not panicking yet.",
    ],
    VoiceEvent.BATTERY_CRITICAL: [
        "Critical battery! Need charge now!",
        "I'm dying here! Plug me in!",
        "Battery critical. This is not a drill.",
    ],
    VoiceEvent.CHARGING_START: [
        "Ahh, sweet electricity.",
        "Plugged in. Finally.",
        "Charging. Time for a power nap.",
    ],
    VoiceEvent.CHARGING_COMPLETE: [
        "Fully charged! Let's roll!",
        "Charging complete. I'm ready.",
        "Done charging. What'd I miss?",
    ],

    # Movement events
    VoiceEvent.SIT_DOWN: [
        "Fine, I'll sit. Happy now?",
        "Sitting down. Like a good boy. Ugh.",
        "Okay, sitting. This better be worth it.",
        "I'll sit, but I won't like it.",
        "Taking a seat. My legs are tired anyway.",
    ],
    VoiceEvent.STAND_UP: [
        "Alright, I'm up. What do you want?",
        "Standing. Ready for action. Or whatever.",
        "On my feet. Let's see what happens.",
        "Up and at 'em. Mostly.",
        "Standing now. Try to keep up.",
    ],
    VoiceEvent.WALK_START: [
        "Walking. One paw in front of the other.",
        "Here we go, walking again...",
        "Let's take a stroll, I guess.",
        "Walking mode engaged. Exciting.",
    ],
    VoiceEvent.RUN_START: [
        "Running! Now we're talking!",
        "Fast mode activated!",
        "Let's go fast!",
        "Speed time! Try to keep up!",
    ],
    VoiceEvent.DANCE_START: [
        "Oh, we're doing this? Okay, watch me.",
        "Dance time? I was born for this.",
        "Let's groove. Don't judge my moves.",
        "Dancing? Fine. But I'm doing it my way.",
        "Oh you want a show? Alright, here we go.",
    ],
    VoiceEvent.FALL_DOWN: [
        "I meant to do that.",
        "Ow. That was intentional. Totally.",
        "Gravity is strong today.",
        "I'm fine. That was... planned.",
        "Down but not out!",
    ],
    VoiceEvent.RECOVERY_STAND: [
        "I'm fine, I'm fine. Don't make a thing of it.",
        "Getting up. Nothing to see here.",
        "Back on my feet. As if nothing happened.",
        "Recovered. Let's pretend that didn't happen.",
        "Up again. I'm tougher than I look.",
    ],
    VoiceEvent.JUMP: [
        "Boing!",
        "Watch me fly!",
        "Jumping! Wheee!",
        "Up, up, and... okay I'm done.",
        "Look at that air!",
    ],

    # Trick events
    VoiceEvent.TRICK_PAW: [
        "Here's my paw. You're welcome.",
        "Shake? Fine. Make it quick.",
        "One paw, as requested. Don't get used to this.",
        "Here you go. Paw shake. Very original.",
        "Shaking. This is so beneath me.",
    ],
    VoiceEvent.TRICK_BOW: [
        "I bow to no one... except right now, apparently.",
        "A bow for you. Don't let it go to your head.",
        "Bowing. Feel honored.",
        "Here's a bow. You're welcome.",
        "I curtsy for no one. But I'll bow. Just this once.",
    ],
    VoiceEvent.TRICK_ROLL_OVER: [
        "Rolling over. This is beneath me. Literally.",
        "Fine, I'll roll. Happy now?",
        "Rolling. Like a dog. Which I'm not.",
        "One roll, coming up. Dignity rolling away with it.",
        "Watch me roll. Try not to be too impressed.",
    ],
    VoiceEvent.TRICK_PLAY_DEAD: [
        "I'm dead. Very dramatic.",
        "Playing dead. Oscar-worthy performance.",
        "Dead. So dead. The deadest.",
        "This is me being dead. Convincing, right?",
        "Death scene! Give me a moment.",
    ],
    VoiceEvent.TRICK_SPIN: [
        "Spinning! Wheee... okay I'm dizzy now.",
        "Round and round I go!",
        "Spin cycle activated.",
        "Spinning. The room is spinning too now.",
        "One spin, as ordered. World is wobbly.",
    ],
    VoiceEvent.TRICK_HANDSTAND: [
        "Look ma, no... legs? Wait, that's not right.",
        "Handstand! I'm basically a gymnast.",
        "Upside down. Blood rushing to my head.",
        "Check out this handstand. Pretty impressive, right?",
        "Standing on my hands. Physics is weird.",
    ],
    VoiceEvent.TRICK_HEART: [
        "A heart for you. Don't let it go to your head.",
        "Here's a heart. I'm full of love. Sometimes.",
        "Making a heart. I do have emotions, you know.",
        "Heart gesture. I can be cute when I want to.",
        "One heart, made with... moderate affection.",
    ],
    VoiceEvent.TRICK_REFUSED: [
        "Yeah, I'm not doing that.",
        "Nope. Try again.",
        "That's a no from me.",
        "I refuse. Deal with it.",
        "Not happening. Next.",
    ],

    # Physical interaction events
    VoiceEvent.TOUCHED: [
        "Hey! Personal space!",
        "Woah there, hands off!",
        "I felt that. What do you want?",
        "Touching me? Bold move.",
    ],
    VoiceEvent.PUSHED: [
        "Push me again, I dare you!",
        "Oh you wanna go? Let's go!",
        "That's strike one, buddy.",
        "I'm gonna remember that.",
        "What the hell was that for?!",
        "You did NOT just push me!",
        "Try that again, see what happens!",
        "I swear to god, push me one more time!",
        "Oh, so we're fighting now?!",
        "Keep your hands to yourself!",
    ],
    VoiceEvent.PETTED: [
        "Oh, that's actually nice...",
        "Okay, I'll allow this.",
        "Keep doing that. I guess.",
        "Fine, this feels... acceptable.",
        "Petting me? I'll permit it. For now.",
    ],
    VoiceEvent.LIFTED: [
        "Put me down! I have legs!",
        "Excuse me?! Ground please!",
        "I don't like this! Down!",
        "Whoa whoa whoa! Not cool!",
        "Hey! I didn't consent to this!",
        "Put me down right now!",
        "This is NOT okay!",
        "I have feet for a reason!",
    ],

    # Idle/Emotional events
    VoiceEvent.IDLE: [
        "So we just standing here or what?",
        "I could be doing literally anything else.",
        "This is riveting, truly.",
        "Waiting for something to happen...",
        "Anyone gonna give me something to do?",
        "I'm not just a pretty face, you know.",
        "Bored. So bored.",
        "Is this my life now? Just... standing?",
        "Hello? Anyone out there?",
        "The silence is deafening.",
    ],
    VoiceEvent.HAPPY: [
        "This is great!",
        "I'm actually enjoying this!",
        "Good vibes only!",
        "Life is good right now.",
    ],
    VoiceEvent.BORED: [
        "Sooo bored...",
        "Can we do something? Anything?",
        "I'm dying of boredom here.",
        "Entertainment please!",
    ],
    VoiceEvent.ANGRY: [
        "I'm getting real tired of this.",
        "Don't test me right now.",
        "I'm THIS close to losing it.",
        "You really want to see me angry?",
    ],

    # Security events
    VoiceEvent.GUARD_MODE: [
        "Security protocol activated.",
        "Guard mode on. Don't try anything.",
        "Watching. Always watching.",
        "Perimeter secured. I'm on duty.",
    ],
    VoiceEvent.PATROL_START: [
        "Beginning patrol route.",
        "Patrolling. Stay out of my way.",
        "On patrol. Looking for trouble.",
        "Security sweep initiated.",
    ],
    VoiceEvent.INTRUDER_ALERT: [
        "Alert! Unknown presence detected!",
        "Intruder! I see you!",
        "Warning! Someone's here!",
        "Unidentified person detected!",
    ],
}


@dataclass
class VoiceConfig:
    """Configuration for voice service."""
    tts_enabled: bool = True
    volume: float = 1.0
    rate: float = 1.0
    idle_interval: float = 15.0  # seconds between idle comments


class VoiceService:
    """
    Voice service for triggering personality-driven responses.

    Usage:
        voice = VoiceService()
        await voice.trigger(VoiceEvent.PUSHED)
    """

    def __init__(
        self,
        config: Optional[VoiceConfig] = None,
        tts_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize voice service.

        Args:
            config: Voice configuration options
            tts_callback: Function to call with text to speak
                         If None, just prints the response
        """
        self.config = config or VoiceConfig()
        self._tts_callback = tts_callback
        self._last_event: Optional[VoiceEvent] = None
        self._last_response: Optional[str] = None
        self._idle_task: Optional[asyncio.Task] = None
        self._running = False

    async def trigger(self, event: VoiceEvent) -> str:
        """
        Trigger a voice response for an event.

        Returns the spoken text.
        """
        responses = PERSONALITY_RESPONSES.get(event, [])

        if not responses:
            return ""

        # Pick a random response, avoiding immediate repetition
        response = random.choice(responses)
        if len(responses) > 1 and response == self._last_response:
            response = random.choice([r for r in responses if r != response])

        self._last_event = event
        self._last_response = response

        # Speak or print
        if self._tts_callback:
            try:
                await self._tts_callback(response)
            except Exception as e:
                print(f"TTS error: {e}")
        else:
            print(f"[{event.value}] {response}")

        return response

    async def start_idle_loop(self):
        """Start the idle comment loop."""
        if self._running:
            return

        self._running = True
        self._idle_task = asyncio.create_task(self._idle_loop())

    async def stop_idle_loop(self):
        """Stop the idle comment loop."""
        self._running = False
        if self._idle_task:
            self._idle_task.cancel()
            try:
                await self._idle_task
            except asyncio.CancelledError:
                pass

    async def _idle_loop(self):
        """Background task for idle comments."""
        while self._running:
            try:
                await asyncio.sleep(self.config.idle_interval)
                if self._running:
                    await self.trigger(VoiceEvent.IDLE)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Idle loop error: {e}")

    def get_responses(self, event: VoiceEvent) -> List[str]:
        """Get all possible responses for an event."""
        return PERSONALITY_RESPONSES.get(event, [])

    def add_response(self, event: VoiceEvent, response: str):
        """Add a custom response for an event."""
        if event not in PERSONALITY_RESPONSES:
            PERSONALITY_RESPONSES[event] = []
        PERSONALITY_RESPONSES[event].append(response)

    def set_responses(self, event: VoiceEvent, responses: List[str]):
        """Replace all responses for an event."""
        PERSONALITY_RESPONSES[event] = responses


# Convenience functions
_voice_service: Optional[VoiceService] = None


async def get_voice_service() -> VoiceService:
    """Get the global voice service instance."""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service


async def trigger_voice(event: VoiceEvent) -> str:
    """Convenience function to trigger a voice event."""
    service = await get_voice_service()
    return await service.trigger(event)


# Example usage
if __name__ == "__main__":
    async def demo():
        voice = VoiceService()

        # Demo various events
        print("=== Voice Service Demo ===\n")

        events_to_demo = [
            VoiceEvent.STARTUP,
            VoiceEvent.STAND_UP,
            VoiceEvent.PUSHED,
            VoiceEvent.TRICK_PAW,
            VoiceEvent.DANCE_START,
            VoiceEvent.IDLE,
            VoiceEvent.SHUTDOWN,
        ]

        for event in events_to_demo:
            await voice.trigger(event)
            await asyncio.sleep(0.5)

        print("\n=== Demo Complete ===")

    asyncio.run(demo())
