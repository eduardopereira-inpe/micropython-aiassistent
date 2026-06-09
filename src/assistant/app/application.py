import gc
import uasyncio as asyncio
import utime

from assistant.config import (
    API_KEY,
    SSID,
    PASSWORD
)

from connectivity.wifi import (
    connect_to_wifi
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
    # GetTemperatureTool,
    TurnOnOffLedTool,
    LocalTimeTool,
    LocalDateTimeTool,
    Scheduler,
    ScheduleEventTool,
    DisplayMessageTool, 
    GetLatLonTool,
    GetWeatherTool

    
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

        schedule_event_tool = ScheduleEventTool(
            self.scheduler
        )

        turn_onoff_led = TurnOnOffLedTool()
        get_local_time = LocalTimeTool()
        get_local_datetime = LocalDateTimeTool()
        get_lat_lon = GetLatLonTool()
        get_weather = GetWeatherTool()

        show_message = DisplayMessageTool(
            self.ui,
            self.player
        )

        # ------------------------------
        # Register Tools
        # ------------------------------

        self.llm.register_tool(tool=schedule_event_tool)

        # self.llm.register_tool(
        #     tool=GetTemperatureTool()
        # )
        
        self.llm.register_tool(tool=turn_onoff_led)
        
        self.llm.register_tool(tool=get_local_time)

        self.llm.register_tool(tool=get_local_datetime)

        self.llm.register_tool(tool=show_message)


        self.llm.register_tool(tool=get_lat_lon)

        self.llm.register_tool(tool=get_weather)

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

        connect_to_wifi(
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