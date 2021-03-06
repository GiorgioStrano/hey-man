import signal
import sys
import os
import speech_recognition as sr
import Levenshtein


from math import inf
from ..snowboylib import snowboydecoder
from ..rf import arduino
from ..config import assistant as cfg

SENSITIVITY = cfg["sensitivity"]
moder = cfg["model"]

class Assistant:

    def __init__(self, model):
        self.model = model
        self.interrupted = False
        self.detector = snowboydecoder.HotwordDetector(self.model, sensitivity = SENSITIVITY)
        self.programs = None

        signal.signal(signal.SIGINT, self.handle_signal)

    def listen(self):
        print("Listening... press Ctrl+C to exit")
        self.detector.start(detected_callback = self.callback,
                            interrupt_check = lambda: self.interrupted,
                            sleep_time = 0.03)

        self.detector.terminate()

    def callback(self):
        self.activate()

    def handle_signal(self, signal, frame):
        self.interrupted = True

    def say(self, s):
        os.system("say {0} -v samantha -r 210".format(s.replace("\'", "")))

    def activate(self):
        print("Hi! I am now listening")
        self.say("what's up man")

        self.detector.terminate()
        mic = sr.Microphone()
        rec = sr.Recognizer()

        with mic as source:
            audio = rec.listen(source=source)

        text = ''

        try:
            text = rec.recognize_google(audio)

        except sr.UnknownValueError:
            print("Google could not understand audio")

        except sr.RequestError as e:
            print("Could not request results from shpinx service; {0}".format(e))

        if text:
            self.interpret(text)

        self.listen()


    def interpret(self, text):
        if "open" in text or "launch" in text:
            words = text.split()
            i = words.index("open") if "open" in text else words.index("launch")
            self.openApp("".join(words[i+1:]))


        elif "nothing" in text:
            self.say("ok sorry")


        elif "turn" in text or "switch" in text or "light" in text or "lights" in text:

            if "on" in text:
                self.handleLight("on")
            elif "off" in text:
                self.handleLight("off")
            else:
                self.say("do you want to switch the lights on or off?")

        else:
            answer = "You said {0}, but you know I am not yet programmed to answer to that".format(text.replace("\'", ""))
            # os.system("say {0}".format(answer))
            self.say(answer)

    def openApp(self, name):

        def collect_computer_programs():
            programs = set()
            with os.scandir("/Applications/") as entries:
                for entry in entries:
                    programs.add(entry.name)
                return programs

        if self.programs == None:
            self.programs = collect_computer_programs()

        newname = ''.join(' ' + char if char.isupper() else char for char in name).strip() + ".app"

        print("I heard {0}".format(newname))

        best_score = inf
        candidate = None
        for program in self.programs:
            score = Levenshtein.distance(newname, program)
            if score < best_score:
                best_score = score
                candidate = program

        path = candidate.replace(" ", "\\ ")
        self.say("launching {0}".format(candidate))

        os.system("open /Applications/"+path)

    def handleLight(self, state):

        success = False

        if state == "on":
            success = arduino.turnOn()

        else:
            success = arduino.turnOff()

        if not success:
            self.say("I couldn't connect to arduino")
