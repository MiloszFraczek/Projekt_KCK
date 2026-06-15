import speech_recognition as sr
import pyttsx3

class VoiceMod:
    def __init__(self):
        pass
    def speak(self,text):
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
        if voice == "rozpocznij trening":
            return VoiceMod.Mode.start
    def mistake_tell(self, mistake):
        match mistake:
            case "legs_width":
                self.speak("Nogi za wąsko")
            case "straight_back":
                self.speak("Wyprostuj plecy")
            case "delts_asymetry":
                self.speak("Popraw barki")
            case "bent_arms":
                self.speak("Wyprostuj łokcie")
            case "hips_too_low":
                self.speak("Biodra za nisko")
            case "hips_too_high":
                self.speak("Biodra za wysoko")
