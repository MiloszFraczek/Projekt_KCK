import speech_recognition as sr
import pyttsx3
from enum import Enum
class VoiceMod:
    def __init__(self):
        pass
    class Mode(Enum):
        start = 1
        stop = 2

    def speak(self,tekst):
        silnik = pyttsx3.init()
        silnik.say(tekst)
        silnik.runAndWait()

    def get_voice(self):
        recognizer = sr.Recognizer()

        with sr.Microphone() as zrodlo:
            print("Nasłuchuję... (powiedz coś)")
            recognizer.adjust_for_ambient_noise(zrodlo)
            audio = recognizer.listen(zrodlo)

            try:
                tekst = recognizer.recognize_google(audio, language="pl-PL")
                print(f"Rozpoznano: {tekst}")
                return tekst
            except sr.UnknownValueError:
                print("Przepraszam, nie zrozumiałem co powiedziałeś.")
                return None
            except sr.RequestError as e:
                print(f"Błąd połączenia z serwisem Google: {e}")
                return None
    def change_state(self):
        voice = self.get_voice()
        if voice == "rozpocznij trening":
            return VoiceMod.Mode.start
    def mistake_tell(self, mistake):
        match mistake:
            case legs_width:
                self.speak("Nogi za wąsko")
            case straight_back:
                self.speak("Wyprostuj plecy")
            case delts_asymetry:
                self.speak("Popraw barki")
            case too_fast:
                self.speak("Za szybko opuszczasz ciężar")
