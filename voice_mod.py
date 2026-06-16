import speech_recognition as sr
import pyttsx3
import json

class VoiceMod:
    def __init__(self):
        with open('config/voice_config.json', 'r', encoding='utf-8') as file:
            self.config = json.load(file)

    def speak(self, text):
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    def get_voice(self):
        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            print("Nasłuchuję... (powiedz coś)")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

            try:
                text = recognizer.recognize_google(audio, language="pl-PL")
                print(f"Rozpoznano: {text}")
                return text
            except sr.UnknownValueError:
                print("Przepraszam, nie zrozumiałem co powiedziałeś.")
                return None
            except sr.RequestError as e:
                print(f"Błąd połączenia z serwisem Google: {e}")
                return None
    def change_state(self):
        voice = self.get_voice()
        if voice == self.config["commands"]["start_training"]:
            return VoiceMod.Mode.start
    def mistake_tell(self, mistake):
        message = self.config["mistakes"].get(mistake)
        if message:
            self.speak(message)