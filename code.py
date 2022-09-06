import time
import math
import gc
from digitalio import DigitalInOut, Direction, Pull
import audioio
import audiocore
import audiomixer
import busio
import board
import neopixel
import adafruit_lis3dh
from rainbowio import colorwheel
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.color import RED
import adafruit_fancyled.adafruit_fancyled as fancy


# SENSITIVITY
HIT = 400
SWING = 200

NUM_PIXELS = 144
NEOPIXEL_PIN = board.D5
POWER_PIN = board.D10
SWITCH_PIN = board.D9
SWITCH2_PIN = board.D13

enable = DigitalInOut(POWER_PIN)
enable.direction = Direction.OUTPUT
enable.value = False

red_led = DigitalInOut(board.D11)
red_led.direction = Direction.OUTPUT

speaker = audioio.AudioOut(board.A0, right_channel=board.A1)
mode = 0

strip = neopixel.NeoPixel(NEOPIXEL_PIN, NUM_PIXELS, brightness=0.75, auto_write=False)
chase = Chase(strip, speed=0.1, color=RED, size=75, spacing=1)

strip.fill(0)
strip.show()

switch = DigitalInOut(SWITCH_PIN)
switch.direction = Direction.INPUT
switch.pull = Pull.UP

switch2 = DigitalInOut(SWITCH2_PIN)
switch2.direction = Direction.INPUT
switch2.pull = Pull.UP

time.sleep(0.1)

# Set up accelerometer on I2C bus, 4G range:
i2c = busio.I2C(board.SCL, board.SDA)
accel = adafruit_lis3dh.LIS3DH_I2C(i2c)
accel.range = adafruit_lis3dh.RANGE_4_G

# "Idle" color is 1/4 brightness, "swinging" color is full brightness...
COLOR_IDLE = colorwheel(85)
COLOR_HIT = (255, 255, 255)  # "hit" color is white

index = 0

#    [0],  # red
#    [10],  # orange
#    [30],  # yellow
#    [85],  # green
#    [137],  # cyan
#    [170],  # blue
#    [213],  # purple

counter = 85

idleWav = audiocore.WaveFile(open("sounds/idle.wav", "rb"))
hitWav = audiocore.WaveFile(open("sounds/hit.wav", "rb"))
swingWav = audiocore.WaveFile(open("sounds/swing.wav", "rb"))
marchWav = audiocore.WaveFile(open("sounds/march.wav", "rb"))


mixer = audiomixer.Mixer(
    voice_count=3,
    sample_rate=11025,
    channel_count=1,
    bits_per_sample=16,
    samples_signed=True,
)


def play_wav(name, loop=False):
    """
    Play a WAV file in the 'sounds' directory.
    @param name: partial file name string, complete name will be built around
                 this, e.g. passing 'foo' will play file 'sounds/foo.wav'.
    @param loop: if True, sound will repeat indefinitely (until interrupted
                 by another sound).
    """
    print("playing", name)
    try:
        wave_file = open("sounds/" + name + ".wav", "rb")
        wave = audiocore.WaveFile(wave_file)
        speaker.play(wave, loop=loop)
    except:
        return


def power(sound, duration, reverse):
    """
    Animate NeoPixels with accompanying sound effect for power on / off.
    @param sound:    sound name (similar format to play_wav() above)
    @param duration: estimated duration of sound, in seconds (>0.0)
    @param reverse:  if True, do power-off effect (reverses animation)
    """

    color = colorwheel(counter)
    if reverse:
        prev = NUM_PIXELS
    else:
        prev = 0
    gc.collect()  # Tidy up RAM now so animation's smoother
    start_time = time.monotonic()  # Save audio start time
    play_wav(sound)
    while True:
        elapsed = time.monotonic() - start_time  # Time spent playing sound
        if elapsed > duration:  # Past sound duration?
            break  # Stop animating
        fraction = elapsed / duration  # Animation time, 0.0 to 1.0
        if reverse:
            fraction = 1.0 - fraction  # 1.0 to 0.0 if reverse
        fraction = math.pow(fraction, 0.5)  # Apply nonlinear curve
        threshold = int(NUM_PIXELS * fraction + 0.5)
        num = threshold - prev  # Number of pixels to light on this pass
        if num != 0:
            if reverse:
                strip[threshold:prev] = [0] * -num
            else:
                strip[prev:threshold] = [COLOR_IDLE] * num
            strip.show()
            # NeoPixel writes throw off time.monotonic() ever so slightly
            # because interrupts are disabled during the transfer.
            # We can compensate somewhat by adjusting the start time
            # back by 30 microseconds per pixel.
            start_time -= NUM_PIXELS * 0.00003
            prev = threshold

    if reverse:
        strip.fill(0)  # At end, ensure strip is off
    else:
        strip.fill(COLOR_IDLE)  # or all pixels set on
    strip.show()
    while speaker.playing:  # Wait until audio done
        pass


def rainbow_cycle(wait):
    for j in range(255):
        for i in range(NUM_PIXELS):
            rc_index = (i * 256 // NUM_PIXELS) - j
            strip[i] = colorwheel(rc_index & 255)
        strip.show()
        time.sleep(wait)


def phaser_glow(color, wait):
    for j in range(255):
        for i in range(NUM_PIXELS):
            rc_index = (i * 256 // NUM_PIXELS) - j
            strip[i] = colorwheel(rc_index & 255)
        strip.show()
        time.sleep(wait)


def color_chase(color, wait):
    for i in range(NUM_PIXELS):
        strip[i] = color
        time.sleep(wait)
        strip.show()
    time.sleep(0.5)


def load(color, duration, reverse):
    """
    Animate NeoPixels with accompanying sound effect for power on / off.
    @param sound:    sound name (similar format to play_wav() above)
    @param duration: estimated duration of sound, in seconds (>0.0)
    @param reverse:  if True, do power-off effect (reverses animation)
    """

    if reverse:
        prev = NUM_PIXELS
    else:
        prev = 0
    gc.collect()  # Tidy up RAM now so animation's smoother
    start_time = time.monotonic()  # Save audio start time
    while True:
        elapsed = time.monotonic() - start_time  # Time spent playing sound
        if elapsed > duration:  # Past sound duration?
            break  # Stop animating
        fraction = elapsed / duration  # Animation time, 0.0 to 1.0
        if reverse:
            fraction = 1.0 - fraction  # 1.0 to 0.0 if reverse
        fraction = math.pow(fraction, 0.5)  # Apply nonlinear curve
        threshold = int(NUM_PIXELS * fraction + 0.5)
        num = threshold - prev  # Number of pixels to light on this pass
        if num != 0:
            if reverse:
                strip[threshold:prev] = [0] * -num
            else:
                strip[prev:threshold] = [color] * num
            strip.show()
            # NeoPixel writes throw off time.monotonic() ever so slightly
            # because interrupts are disabled during the transfer.
            # We can compensate somewhat by adjusting the start time
            # back by 30 microseconds per pixel.
            start_time -= NUM_PIXELS * 0.00003
            prev = threshold


# Main program loop, repeats indefinitely

while True:
    red_led.value = False
    color = colorwheel(counter)

    COLOR_IDLE = color
    if not switch.value:  # button pressed?
        if mode == 0:  # If currently off...
            enable.value = True
            power("on2", 0.2, False)  # Power up!
            speaker.play(mixer)
            mixer.voice[0].level = 0.2
            mixer.voice[0].play(idleWav, loop=True)
            # play_wav('idle', loop=True)     # Play background hum sound
            mode = 1  # ON (idle) mode now
        else:  # else is currently on...
            power("off", 1.15, True)  # Power down
            mode = 0  # OFF mode now
            enable.value = False
        while not switch.value:  # Wait for button release
            time.sleep(0.2)  # to avoid repeated triggering

    elif mode >= 1:  # If not OFF mode...
        x, y, z = accel.acceleration  # Read accelerometer
        accel_total = x * x + z * z + y * y
        # (Y axis isn't needed for this, assuming Hallowing is mounted
        # sideways to stick.  Also, square root isn't needed, since we're
        # just comparing thresholds...use squared values instead, save math.)
        color = colorwheel(counter)

        if not switch2.value:
            counter = counter + 1
            if counter >= 255:
                counter = 1
            color = colorwheel(counter)
            COLOR = color
            strip.fill(COLOR)  # Set to idle color
            strip.show()
            #mixer.voice[1].play(marchWav, loop=False)
            print("changing color")

        else:
            color = colorwheel(counter)
            if accel_total > HIT:  # Large acceleration = HIT
                TRIGGER_TIME = time.monotonic()  # Save initial time of hit
                print("hit")
                # play_wav('hit')                 # Start playing 'hit' sound
                strip.fill(COLOR_HIT)
                strip.show()
                time.sleep(0.2)
                strip.fill(color)
                strip.show()
                mode = 1
                mixer.voice[1].play(hitWav, loop=False)
                time.sleep(1)
                strip.fill(color)

            elif mode == 1 and accel_total > SWING:  # Mild = SWING
                TRIGGER_TIME = time.monotonic()  # Save initial time of swing
                print("swing")
                # play_wav('swing', loop=False)               # Start playing 'swing' sound
                mixer.voice[1].play(swingWav, loop=False)
                time.sleep(1)
                strip.fill(color)
                strip.show()

            else:
                print("idle")
                #phaser_glow(colorwheel(23),0)
                #time.sleep(0.5)
                #chase.animate()
                # strip.show()
                # try flicker here
