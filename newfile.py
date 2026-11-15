from datetime import datetime
import json
import math
import os
import random
import threading
import urllib.parse
import urllib.request

# Try launching the Kivy Touch GUI. If it fails on Android, fallback to text mode.
try:
    from kivy.app import App
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.textinput import TextInput
    KIVY_AVAILABLE = True
except Exception:
    KIVY_AVAILABLE = False

import pyttsx3

# Initialize Voice Engine
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 165)
    VOICE_ENABLED = True
except Exception:
    VOICE_ENABLED = False

MEMORY_FILE = 'ai_brain.json'


def speak_text(text):
    if VOICE_ENABLED:
        try:
            engine.say(text[:150])
            engine.runAndWait()
        except Exception:
            pass


def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {
        'who are you': (
            'I am AETHER, your mobile neural assistant and test helper.'
        ),
        'what is the meaning of life': '42. Obviously.',
    }


def save_memory(memory):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=4)


def search_web(query):
    try:
        clean_query = query
        for prefix in [
            'solve ',
            'search ',
            'who is ',
            'what is ',
            'explain ',
            'define ',
            'tell me about ',
        ]:
            if clean_query.startswith(prefix):
                clean_query = clean_query.replace(prefix, '', 1)

        encoded_query = urllib.parse.quote(clean_query.strip())
        url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_query}'

        req = urllib.request.Request(
            url, headers={'User-Agent': 'AETHER-App/6.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'extract' in data and data['extract']:
                return f'Study Summary:\n\n{data["extract"]}'
    except Exception:
        return (
            'No exact match found online. Try simplifying keywords or typing the'
            ' core term.'
        )
    return 'No relevant data found.'


def solve_math(text):
    try:
        clean_expr = (
            text.replace('x', '*')
            .replace('X', '*')
            .replace('=', '==')
            .replace('^', '**')
        )
        for word in ['solve', 'calculate', 'calc', 'what is', 'is']:
            clean_expr = clean_expr.replace(word, '')
        clean_expr = clean_expr.strip()

        if '==' in clean_expr:
            parts = clean_expr.split('==')
            left_val = eval(parts[0], {'__builtins__': None}, {'math': math})
            return (
                f'Equation Check:\nLeft Side: {parts[0].strip()} = {left_val}'
                f'\nRight Side: {parts[1].strip()}'
            )
        else:
            result = eval(clean_expr, {'__builtins__': None}, {'math': math})
            return f'Solution: {text} = {result}'
    except Exception:
        return 'Could not evaluate math expression.'


def is_math_expression(text):
    math_chars = ['+', '-', '*', '/', '^', '=', '%']
    has_digit = any(char.isdigit() for char in text)
    has_operator = any(op in text for op in math_chars)
    return has_digit and (has_operator or text.replace('.', '', 1).isdigit())


# --- KIVY LIQUID GLASS GUI ---
if KIVY_AVAILABLE:
    Window.clearcolor = (0.04, 0.06, 0.11, 1)

    class GlassPanel(BoxLayout):

        def __init__(
            self,
            tint=(1, 1, 1, 0.09),
            border_alpha=0.28,
            radius=24,
            **kwargs,
        ):
            super().__init__(**kwargs)
            self.tint = tint
            self.border_alpha = border_alpha
            self.radius = [radius]

            with self.canvas.before:
                self.bg_color = Color(*self.tint)
                self.bg_rect = RoundedRectangle(
                    pos=self.pos, size=self.size, radius=self.radius
                )
                self.border_color = Color(1, 1, 1, self.border_alpha)
                self.border_line = Line(
                    rounded_rectangle=(
                        self.x,
                        self.y,
                        self.width,
                        self.height,
                        radius,
                    ),
                    width=1.15,
                )
            self.bind(pos=self._update_canvas, size=self._update_canvas)

        def _update_canvas(self, *args):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
            self.border_line.rounded_rectangle = (
                self.x,
                self.y,
                self.width,
                self.height,
                self.radius[0],
            )

    class GlassButton(Button):

        def __init__(
            self, tint=(0.2, 0.75, 1.0, 0.28), radius=22, **kwargs
        ):
            super().__init__(**kwargs)
            self.background_normal = ''
            self.background_down = ''
            self.background_color = (0, 0, 0, 0)
            self.tint = tint
            self.radius = radius

            with self.canvas.before:
                self.bg_color = Color(*self.tint)
                self.bg_rect = RoundedRectangle(
                    pos=self.pos, size=self.size, radius=[radius]
                )
                self.border_color = Color(1, 1, 1, 0.35)
                self.border_line = Line(
                    rounded_rectangle=(
                        self.x,
                        self.y,
                        self.width,
                        self.height,
                        radius,
                    ),
                    width=1.1,
                )
            self.bind(pos=self._update_canvas, size=self._update_canvas)

        def _update_canvas(self, *args):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
            self.border_line.rounded_rectangle = (
                self.x,
                self.y,
                self.width,
                self.height,
                self.radius,
            )

    class AetherApp(App):

        def build(self):
            self.title = 'AETHER OS // Liquid Glass'
            self.memory = load_memory()
            self.waiting_to_learn = None

            master = FloatLayout()
            with master.canvas.before:
                Color(0.05, 0.55, 0.95, 0.24)
                self.orb1 = Ellipse(
                    pos=(Window.width * 0.05, Window.height * 0.55),
                    size=(Window.width * 0.75, Window.width * 0.75),
                )
                Color(0.45, 0.25, 0.95, 0.22)
                self.orb2 = Ellipse(
                    pos=(Window.width * 0.3, Window.height * 0.12),
                    size=(Window.width * 0.8, Window.width * 0.8),
                )
            master.bind(size=self._update_orbs)

            root = BoxLayout(orientation='vertical', padding=16, spacing=14)

            # Header
            header = GlassPanel(
                tint=(1, 1, 1, 0.08),
                border_alpha=0.30,
                radius=26,
                size_hint_y=0.095,
                padding=[18, 8],
                spacing=10,
            )
            title_label = Label(
                text=(
                    '[b][color=ffffff]AETHER[/color][/b]'
                    ' [color=8be9fd]Glass OS[/color]'
                ),
                markup=True,
                font_size='19sp',
                halign='left',
                valign='middle',
            )
            title_label.bind(size=title_label.setter('text_size'))
            header.add_widget(title_label)

            clear_btn = GlassButton(
                text='Clear',
                tint=(1.0, 0.3, 0.4, 0.25),
                radius=18,
                size_hint_x=0.24,
                font_size='14sp',
                bold=True,
                color=(1, 0.85, 0.88, 1),
            )
            clear_btn.bind(on_press=self.clear_chat)
            header.add_widget(clear_btn)
            root.add_widget(header)

            # Chat Scroll Area
            self.scroll = ScrollView(size_hint_y=0.79, bar_width=0)
            self.chat_box = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                spacing=14,
                padding=[2, 6],
            )
            self.chat_box.bind(minimum_height=self.chat_box.setter('height'))
            self.scroll.add_widget(self.chat_box)
            root.add_widget(self.scroll)

            # Input Dock
            input_dock = GlassPanel(
                tint=(1, 1, 1, 0.10),
                border_alpha=0.32,
                radius=28,
                size_hint_y=0.105,
                padding=[14, 8],
                spacing=10,
            )
            self.user_input = TextInput(
                hint_text='Ask question or paste math...',
                hint_text_color=(0.7, 0.78, 0.88, 0.65),
                multiline=False,
                font_size='15sp',
                background_normal='',
                background_active='',
                background_color=(0, 0, 0, 0),
                foreground_color=(1, 1, 1, 1),
                cursor_color=(0.4, 0.9, 1, 1),
                padding=[8, 12],
            )
            self.user_input.bind(on_text_validate=self.on_send)

            send_btn = GlassButton(
                text='Solve',
                tint=(0.15, 0.72, 1.0, 0.35),
                radius=20,
                size_hint_x=0.26,
                font_size='15sp',
                bold=True,
                color=(1, 1, 1, 1),
            )
            send_btn.bind(on_press=self.on_send)

            input_dock.add_widget(self.user_input)
            input_dock.add_widget(send_btn)
            root.add_widget(input_dock)

            master.add_widget(root)

            self.add_message(
                'AETHER',
                'Liquid Glass interface active. Ready for math, homework & web'
                ' search.',
                is_ai=True,
            )
            threading.Thread(
                target=speak_text,
                args=('Liquid Glass interface active. Ready for input.',),
                daemon=True,
            ).start()
            return master

        def _update_orbs(self, instance, value):
            w, h = value
            self.orb1.pos = (w * 0.05, h * 0.55)
            self.orb1.size = (w * 0.75, w * 0.75)
            self.orb2.pos = (w * 0.3, h * 0.12)
            self.orb2.size = (w * 0.8, w * 0.8)

        def add_message(self, sender, text, is_ai=True):
            bubble_tint = (1, 1, 1, 0.08) if is_ai else (0.2, 0.65, 1.0, 0.20)
            border_glow = 0.24 if is_ai else 0.38
            name_color = '7ce8ff' if is_ai else 'ffffff'

            bubble = GlassPanel(
                tint=bubble_tint,
                border_alpha=border_glow,
                radius=22,
                size_hint_y=None,
                padding=[16, 12],
            )
            msg = Label(
                text=f'[b][color={name_color}]{sender}[/color][/b]\n{text}',
                markup=True,
                font_size='15sp',
                color=(0.95, 0.97, 1, 0.95),
                size_hint_y=None,
                halign='left',
                valign='top',
                text_size=(Window.width - 72, None),
            )

            def _sync_height(instance, value):
                instance.height = value[1]
                bubble.height = value[1] + 24

            msg.bind(texture_size=_sync_height)
            bubble.add_widget(msg)
            self.chat_box.add_widget(bubble)
            Clock.schedule_once(
                lambda dt: setattr(self.scroll, 'scroll_y', 0), 0.1
            )

        def clear_chat(self, instance):
            self.chat_box.clear_widgets()
            self.add_message('AETHER', 'Glass canvas cleared.', is_ai=True)

        def on_send(self, instance):
            raw_text = self.user_input.text.strip()
            if not raw_text:
                return
            self.user_input.text = ''
            self.add_message('You', raw_text, is_ai=False)
            threading.Thread(
                target=self.process_input, args=(raw_text,), daemon=True
            ).start()

        def process_input(self, raw_text):
            query = raw_text.lower()
            if self.waiting_to_learn is not None:
                if query != 'skip':
                    self.memory[self.waiting_to_learn] = raw_text
                    save_memory(self.memory)
                    reply = 'Saved to memory bank.'
                else:
                    reply = 'Skipped.'
                self.waiting_to_learn = None
                Clock.schedule_once(lambda dt: self.respond(reply))
                return

            if query in self.memory:
                reply = self.memory[query]
            elif 'time' in query:
                now = datetime.now().strftime('%I:%M %p')
                reply = f'Current local time: {now}.'
            elif is_math_expression(raw_text):
                reply = solve_math(raw_text)
            elif (
                any(
                    kw in query
                    for kw in [
                        'solve',
                        'what is',
                        'who is',
                        'explain',
                        'define',
                        'find',
                        'how to',
                    ]
                )
                or len(query.split()) > 2
            ):
                Clock.schedule_once(
                    lambda dt: self.add_message(
                        'AETHER',
                        '[i]Refracting query across network...[/i]',
                        is_ai=True,
                    )
                )
                reply = search_web(raw_text)
            else:
                self.waiting_to_learn = query
                reply = (
                    f'I need an answer key for "{raw_text}". Type the correct'
                    ' answer to store it (or type "skip").'
                )

            Clock.schedule_once(lambda dt: self.respond(reply))

        def respond(self, text):
            self.add_message('AETHER', text, is_ai=True)
            threading.Thread(
                target=speak_text, args=(text,), daemon=True
            ).start()


# --- FALLBACK CONSOLE UI (If Kivy isn't packaged) ---
else:

    def run_console_ai():
        memory = load_memory()
        print('=== AETHER OFFLINE FALLBACK CONSOLE ===')
        while True:
            user_input = input('\nYOU: ').strip()
            if user_input.lower() in ['exit', 'quit']:
                break
            query = user_input.lower()
            if query in memory:
                reply = memory[query]
            elif is_math_expression(user_input):
                reply = solve_math(user_input)
            elif len(query.split()) > 2:
                reply = search_web(user_input)
            else:
                reply = 'Command recognized.'
            print(f'AETHER: {reply}')
            speak_text(reply)


if __name__ == '__main__':
    if KIVY_AVAILABLE:
        AetherApp().run()
    else:
        run_console_ai()
