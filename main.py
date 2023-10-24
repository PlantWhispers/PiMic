from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Ellipse, Rectangle, Color
from kivy.core.window import Window
from audio_recorder import AudioRecorder

class CustomButton(Widget):
    def redraw(self, recording, *args):
        self.canvas.clear()
        # Makes sure the size of the square or circle (representing reccord and stop respectively) fits the screen.
        min_dim = min(self.width, self.height) * 0.8
        # Centers the shape
        x = self.x + (self.width - min_dim) / 2
        y = self.y + (self.height - min_dim) / 2
        pos = (x, y)
        size = (min_dim, min_dim)
        
        with self.canvas:
            Color(1, 0, 0) # sets color to red
            # draws a sqare if recording, if not, a circle
            if recording:
                Rectangle(pos=pos, size=size)
            else:
                Ellipse(pos=pos, size=size)

class TimerHandler:
    def __init__(self, label):
        self.label = label
        self.seconds = 0

    def update_timer(self, *args):
        self.seconds += 1
        # BUG: not showing hours
        mins, sec = divmod(self.seconds, 60)
        self.label.text = f"{mins:02d}:{sec:02d}"

class FileListHandler:
    def __init__(self, box):
        self.box = box

    def add_file(self, filename):
        file_label = Label(text=filename, size_hint_y=None, height=30)
        self.box.add_widget(file_label)

class RecorderApp(App):
    def build(self):
        self.recording = False
        self.box = BoxLayout(orientation='vertical')
        self.file_box = BoxLayout(orientation='vertical')
        
        self.timer_label = Label(text="00:00")
        self.custom_button = CustomButton()
        self.custom_button.bind(on_touch_down=self.toggle_recording)
        self.custom_button.bind(size=lambda instance, value: self.custom_button.redraw(self.recording))
        
        
        self.box.add_widget(self.timer_label)
        self.box.add_widget(self.custom_button)
        self.box.add_widget(self.file_box)
        
        self.audio_recorder = AudioRecorder(fs=384000, channels=1)
        
        self.timer_handler = TimerHandler(self.timer_label)
        self.file_list_handler = FileListHandler(self.file_box)
        
        Window.bind(size=self.on_window_resize)

        self.on_window_resize(Window, Window.size)


        self.custom_button.redraw(self.recording)

        return self.box

    def on_window_resize(self, window, size):
        self.timer_label.font_size = size[1] * 0.1
        self.custom_button.size = (size[0] * 0.5, size[1] * 0.5)

    def toggle_recording(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.recording = not self.recording
            self.custom_button.redraw(self.recording)
            if self.recording:
                try:
                    self.audio_recorder.start()
                    self.timer_event = Clock.schedule_interval(self.timer_handler.update_timer, 1)
                except Exception as e:
                    print(f"Error starting: {e}")
            else:
                try:
                    filename = self.audio_recorder.stop()
                    if filename:
                        self.file_list_handler.add_file(filename)
                    Clock.unschedule(self.timer_event)
                    self.timer_handler.seconds = 0
                    self.timer_label.text = "00:00"
                except Exception as e:
                    print(f"Error stopping: {e}")

if __name__ == "__main__":
    RecorderApp().run()
