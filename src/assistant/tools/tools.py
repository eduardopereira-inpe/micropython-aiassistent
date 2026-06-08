from machine import Pin
from time import gmtime

# --------------------------------------------------
# Tools
# --------------------------------------------------



# --------------------------------------------------
# Get local datetime and time
# --------------------------------------------------
UTC_OFFSET = -3


UTC_OFFSET_SECONDS = -3 * 3600


def get_local_datetime():

    now = (
        time()
        + UTC_OFFSET_SECONDS
    )

    t = localtime(now)

    return (
        "{:04d}-{:02d}-{:02d} "
        "{:02d}:{:02d}:{:02d}"
    ).format(
        t[0],
        t[1],
        t[2],
        t[3],
        t[4],
        t[5]
    )



# --------------------------------------------------
# Get local  time
# --------------------------------------------------
def get_local_time():

    utc = gmtime()

    hour = (
        utc[3] + UTC_OFFSET
    ) % 24

    return (
        "{:02d}:{:02d}:{:02d}".format(
            hour,
            utc[4],
            utc[5]
        )
    )

# --------------------------------------------------
# LED Control
# --------------------------------------------------
led = Pin(
    23,
    Pin.OUT
)

led.value(0)

def turn_onoff_led(value):

    value = int(value)

    led.value(value)

    if value == 1:
        return "LED ligado"

    return "LED desligado"
    
# --------------------------------------------------
# Get temperature
# --------------------------------------------------

def get_temperature(city):

    return (
        "28 graus Celsius em {}".format(
            city
        )
    )


class DisplayMessageTool:

    def __init__(
        self,
        ui, 
        player
    ):

        self.ui = ui
        self.player = player

    def __call__(
        self,
        message
    ):

        self.ui.set_response(
            message
        )

        self.player.play(
                [
                    'Star Trek intro',
                    80,
                    'NOTE_D4',
                    '-8',
                    'NOTE_G4',
                    '16',
                    'NOTE_C5',
                    '-4',
                    'NOTE_B4',
                    '8',
                    'NOTE_G4',
                    '-16',
                    'NOTE_E4',
                    '-16',
                    'NOTE_A4',
                    '-16',
                    'NOTE_D5',
                    '2'
                ]
            )
        return (
            "Mensagem exibida."
        )
