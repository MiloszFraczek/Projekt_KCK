import speech_recognition as sr
import pyttsx3


def speak(tekst):
    silnik = pyttsx3.init()
    silnik.say(tekst)
    silnik.runAndWait()


def get_voice():
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


