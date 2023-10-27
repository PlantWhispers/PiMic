from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Ellipse, Rectangle, Color
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import BooleanProperty
from kivy.uix.spinner import Button
from kivy.uix.scrollview import ScrollView
from audio_recorder import AudioRecorder

SAMPLERATE_FILTER = 300_000

class NoMicrophoneException(Exception):
    pass

class CustomButton(Widget):
    def redraw(self, isRecording, *args):
        self.canvas.clear()
        # Calculate the minimum dimension based on the width and height of the canvas
        min_dim = min(self.width, self.height) * 0.8
        # Calculate the x and y coordinates of the top-left corner of the shape
        x = self.x + (self.width - min_dim) / 2
        y = self.y + (self.height - min_dim) / 2
        # Set the position and size of the shape
        pos = (x, y)
        size = (min_dim, min_dim)
        
        # Draw the shape based on the value of isRecording
        with self.canvas:
            Color(1, 0, 0)  # Set the color to red
            if isRecording:
                Rectangle(pos=pos, size=size)  # Draw a rectangle if isRecording is True
            else:
                Ellipse(pos=pos, size=size)  # Draw an ellipse if isRecording is False

class TimerHandler:
    def __init__(self, label):
        self.label = label
        self.seconds = 0

    def update_timer(self, *args):
        # Increase the timer by 1 second
        self.seconds += 1
        # Calculate minutes and hours
        mins, sec = divmod(self.seconds, 60)
        hours, mins = divmod(mins, 60)
        
        # Update label
        if hours == 0:
            # If there are no hours, display the minutes and seconds
            self.label.text = f"{mins:02d}:{sec:02d}"
        else:
            # If there are hours, display the hours, minutes, and seconds
            self.label.text = f"{hours:02d}:{mins:02d}:{sec:02d}"

class FileListHandler:
    def __init__(self, box):
        self.box = box

    def add_file(self, filename):
        file_label = Label(text=filename, size_hint_y=None, height=30)
        self.box.add_widget(file_label)


BUTTON_HEIGHT = 50

class SplashScreen(Screen):
    def on_enter(self):
        self.setup_mic_list()

    def setup_mic_list(self):
        label_text, mic_list = self.get_filtered_mic_list()
        if len(mic_list) == 1:
            self.select_mic(mic_index=mic_list[0]['index'])
            return
        self.populate_mic_buttons(label_text, mic_list)

    def get_filtered_mic_list(self):
        mic_list = App.get_running_app().audio_recorder.get_mic_list()
        filtered_mic_list = [mic for mic in mic_list if mic['default_samplerate'] >= SAMPLERATE_FILTER]
        if len(filtered_mic_list) == 0:
            return (f"No microphone with samplerate above {SAMPLERATE_FILTER}.\nPlease choose one of these microphones:", mic_list)
        return (f"Here are all microphones with samplerate above {SAMPLERATE_FILTER}.\nPlease choose one of these microphones:", filtered_mic_list)

    def populate_mic_buttons(self, label_text, mic_list):
        box = BoxLayout(orientation='vertical', size_hint_y=None)
        box.bind(minimum_height=box.setter('height'))

        label = Label(text=label_text, size_hint_y=None, height=BUTTON_HEIGHT*2)
        box.add_widget(label)

        mic_options = [(mic['name'], mic['index']) for mic in mic_list]
        for name, index in mic_options:
            btn = Button(text=str(name), size_hint_y=None, height=BUTTON_HEIGHT)
            btn.bind(on_press=lambda instance, index=index: self.select_mic(mic_index=index))
            box.add_widget(btn)

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(box)
        self.add_widget(scroll)

    def select_mic(self, mic_index):
        App.get_running_app().audio_recorder.set_mic(mic_index)
        print(mic_index)
        self.try_switch_to_main()

    def try_switch_to_main(self, *args):
        try:
            self.manager.current = 'main'
        except Exception as e:
            Clock.schedule_once(self.try_switch_to_main, 0.1)


class MainScreen(Screen):
    def on_enter(self):
        self.audio_recorder = AudioRecorder(samplerate=384000, channels=1)
        self.isRecording = False
        self.box = BoxLayout(orientation='vertical')
        self.file_box = BoxLayout(orientation='vertical')
        
        self.timer_label = Label(text="00:00")
        self.custom_button = CustomButton()
        self.custom_button.bind(on_touch_down=self.toggle_recording)
        self.custom_button.bind(size=lambda instance, value: self.custom_button.redraw(App.get_running_app().isRecording))
        
        Window.bind(size=self.on_window_resize)
        self.on_window_resize(Window, Window.size)
        
        self.box.add_widget(self.timer_label)
        self.box.add_widget(self.custom_button)
        self.box.add_widget(self.file_box)

        self.timer_handler = TimerHandler(self.timer_label)
        self.file_list_handler = FileListHandler(self.file_box)

        self.custom_button.redraw(App.get_running_app().isRecording)

        self.add_widget(self.box)

    def toggle_recording(self, instance, touch):
        if instance.collide_point(*touch.pos):
            app = App.get_running_app()
            app.isRecording = not app.isRecording
            self.custom_button.redraw(app.isRecording)
            
            if app.isRecording:
                try:
                    app.audio_recorder.start()
                    self.timer_event = Clock.schedule_interval(self.timer_handler.update_timer, 1)
                except Exception as e:
                    print(f"Error starting recording: {e}")
            else:
                try:
                    filename = app.audio_recorder.stop()
                    if filename:
                        self.file_list_handler.add_file(filename)
                    Clock.unschedule(self.timer_event)
                    self.timer_handler.seconds = 0
                    self.timer_label.text = "00:00"
                except Exception as e:
                    print(f"Error stopping recording: {e}")
 

    def on_window_resize(self, window, size):
        self.timer_label.font_size = size[1] * 0.1
        self.custom_button.size = (size[0] * 0.5, size[1] * 0.5)

class RecorderApp(App):
    isRecording = BooleanProperty(False)
    
    def build(self):
        self.audio_recorder = AudioRecorder(samplerate=384000, channels=1)
        
        sm = ScreenManager()
        sm.add_widget(SplashScreen(name='splash'))
        sm.add_widget(MainScreen(name='main'))
        sm.current = 'splash'
        
        return sm

if __name__ == "__main__":
    RecorderApp().run()
