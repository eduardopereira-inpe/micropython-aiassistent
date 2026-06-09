import gc
import uasyncio as asyncio
import utime

from assistant.config import (
    API_KEY,
    SSID,
    PASSWORD
)

from assistant.network.wifi import (
    conectar_wifi
)

from udisplay.emotion_display import (
    EmotionDisplay
)

from udisplay.display_callback import (
    DisplayCallback
)

from ullmtools import (
    OpenAI
)

from ullmtools.core.apis.openaimtools import OpenAIMTools


from ubuzzer.player import (
    BuzzerPlayer, 
    
)



from assistant.ui.ui import (
    AssistantUI
)

from uvoiced.audio_service import (
    AudioService,
    AudioServiceUIState
)

from ullmtools import (
    ChatService
)

from ullmtools.tools import (
    # get_temperature,
    # GET_TEMPERATURE_SCHEMA,
    turn_onoff_led,
    TURN_ONOFF_LED_SCHEMA,
    get_local_time,
    GET_LOCAL_TIME_SCHEMA,
    get_local_datetime,
    GET_LOCAL_DATETIME_SCHEMA ,
    Scheduler,
    create_schedule_event_tool,
    SCHEDULE_EVENT_SCHEMA, 
    DisplayMessageTool, 
    SHOW_MESSAGE_SCHEMA, 
    get_lat_lon,
    GET_LAT_LON_SCHEMA,
    get_weather,
    GET_WEATHER_SCHEMA

    
)



# --------------------------------------------------
# Application
# --------------------------------------------------

class AssistantApplication:

    def __init__(self, verbose=True):

        self.verbose = verbose

        self.display = (
            EmotionDisplay()
        )

        self.sleep_time = 500

        self._state = "idle"

        self._current_time = (
            utime.time()
        )

        self.ui = AssistantUI(
            self.display
        )

        self.player = BuzzerPlayer(
            buzzer_pin=14,
            volume=600
        )

        self.llm = OpenAI(
            api_key=API_KEY
        )

        # self.llm = OpenAIMTools(
        #     api_key=API_KEY,
        #     verbose=True
        # )

        self.scheduler = Scheduler(
            tool_executor=
                self.llm.execute_tool
        )

        self.llm.set_scheduler(
            self.scheduler
        )

        schedule_event_tool = (
            create_schedule_event_tool(
                self.scheduler
            )
        )

        show_message = DisplayMessageTool(
            self.ui,
            self.player
        )

        # ------------------------------
        # Register Tools
        # ------------------------------

        self.llm.register_tool(
            name="schedule_event",
            func=schedule_event_tool,
            schema=SCHEDULE_EVENT_SCHEMA
        )

        # self.llm.register_tool(
        #     name="get_temperature",
        #     func=get_temperature,
        #     schema=GET_TEMPERATURE_SCHEMA
        # )
        
        self.llm.register_tool(
            name="turn_onoff_led",
            func=turn_onoff_led,
            schema=TURN_ONOFF_LED_SCHEMA
        )
        
        self.llm.register_tool(
            name="get_local_time",
            func=get_local_time,
            schema=GET_LOCAL_TIME_SCHEMA 
        )

        self.llm.register_tool(
            name="get_local_datetime",
            func=get_local_datetime,
            schema=GET_LOCAL_DATETIME_SCHEMA 
        )

        self.llm.register_tool(
            name="show_message",
            func=show_message,
            schema=SHOW_MESSAGE_SCHEMA
        )


        self.llm.register_tool(
            name="get_lat_lon",
            func=get_lat_lon,
            schema=GET_LAT_LON_SCHEMA
        )

        self.llm.register_tool(
            name="get_weather",
            func=get_weather,
            schema=GET_WEATHER_SCHEMA
         )

        # ------------------------------

        self.audio = AudioService(
            api_key=API_KEY,
        )

        self.callback = (
            DisplayCallback(self.display)
        )

        self.chat = ChatService(
            llm=self.llm,
            callback=self.callback
        )

        self._ui_current_state = None

    def _log(self, msg):
        if self.verbose:
            print(msg)

    async def initialize(self):

        await self.ui.start()

        self.ui.startup()

        await asyncio.sleep(1)

        self.ui.connecting_wifi()

        await asyncio.sleep(1)

        conectar_wifi(
            SSID,
            PASSWORD
        )

        self.ui.idle()
        self._ui_current_state = 1
        asyncio.create_task(
            self.scheduler.run()
        )

             
    async def audio_monitor(self):
        
        self._log(f"[AssistantApplication] _audio_state: {self.audio.audio_service_state}")
        
        if self.audio.audio_service_state == AudioServiceUIState.IDLE:

            if self._ui_current_state != 1:
                self._ui_current_state = 1
                self.ui.idle()
            await asyncio.sleep_ms(0)
        
            
        if self.audio.audio_service_state == AudioServiceUIState.LISTENING:
            self._ui_current_state = 2
            self.ui.listening()
            
            self._log(f"[AssistantApplication] _audio_state: {self.audio.audio_service_state}")

            await asyncio.sleep_ms(100)

        if self.audio.audio_service_state == AudioServiceUIState.TRANSCRIBING:
            self._ui_current_state = 3
            self.ui.transcribing()
            
            self._log(f"[AssistantApplication] _audio_state: {self.audio.audio_service_state}")

            await asyncio.sleep_ms(100)
            
        
        

    async def run(self):

        await self.initialize()

        while True:

            try:

                listener_task = asyncio.create_task(self.audio.listen())

                await  self.audio_monitor()

                is_recorded = await listener_task

                if not is_recorded:
                    continue

                question_task = asyncio.create_task(self.audio.transcribing())
                
                await  self.audio_monitor()
                
                question = await question_task

               
                await self.chat.ask(
                    question,
                    tools=self.llm.get_tools_schema()
                )


            except KeyboardInterrupt:

                print(
                    "\nEncerrando..."
                )

                break

            except Exception as error:

                print(
                    "Erro:",
                    error
                )

                self.ui.error(
                    "Erro na requisicao"
                )

                await asyncio.sleep(
                    2
                )

                gc.collect()
                
            if self.callback.started_response:

                play_response_task = asyncio.create_task(
                    self.player.play_async(
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
                )

                await play_response_task

                await self.ui.wait_message_cycle()
   

        self.shutdown()

    def shutdown(self):

        try:
            self.display.sleep()
        except:
            pass

        try:
            self.player.stop_song()
        except:
            pass

        try:
            self.ui.stop()
        except:
            pass