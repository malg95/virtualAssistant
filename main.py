import os
import struct
import pyaudio
import pvporcupine
import speech_recognition as sr
from gtts import gTTS # Import the required module for text to speech conversion
from io import BytesIO
from pygame import mixer #Library to play .wav files
import wolframalpha
import wikipedia
import pyjokes
import datetime
import subprocess
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import requests
import json
import math
from google.cloud import texttospeech
from google.oauth2 import service_account
import time
import geocoder
import sys

#Sound Playing Initialization Section
mixer.init() #Initialize Object for playing sounds
musicDirPath = "./Sounds" + "/" #New Relative path

#Virtual Assistant Initialization Section
r = sr.Recognizer()
r.dynamic_energy_threshold = False #Dynamically change background noise threshold
r.energy_threshold = 500 #Background Noise Threshold. Tune this for final product.
microphones = sr.Microphone.list_microphone_names()
# mic = sr.Microphone(device_index=microphones.index('hdmi'))
mic = sr.Microphone()

#Setting up Google Cloud Text to Speech
credentials = service_account.Credentials.from_service_account_file('./Credentials/GCTTS.json')
client = texttospeech.TextToSpeechClient(credentials=credentials) # Instantiates a client
voice = texttospeech.VoiceSelectionParams(language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL) # Build the voice request, select the language code ("en-US") and the ssml. Voice gender ("neutral")
audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3) # Select the type of audio file you want returned

def readAPIKeys(txtFileName):
    file1 = open('./Credentials/{}.txt'.format(txtFileName), 'r')
    line = file1.readline()
    file1.close()
    return str(line)

#Reading and setting all API Keys in attributes of a Class
class apiKeysDef:
    def __init__(self):
        self.openWeatherMap = readAPIKeys('openWeatherMapAPI')
        self.pvporcupine = readAPIKeys('pvporcupine')
        self.serpAPI = readAPIKeys('serpAPI')
        self.wolfram = readAPIKeys('wolfram')

apiKeys = apiKeysDef()

firstLoop = True

def playVASound(sound):
    mixer.music.load(sound)
    mixer.music.play()
    while mixer.music.get_busy():
        pass

def speak(results):
    try:
        synthesis_input = texttospeech.SynthesisInput(text=results) # Set the text input to be synthesized
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config) # Perform the text-to-speech request on the text input with the selected. Voice parameters and audio file type
    except Exception as e:
        print(e)
        return
    # The response's audio_content is binary.
    GCTTSPath = 'GCTTSTemporaryFiles'
    with open(GCTTSPath + '/output.mp3', "wb") as out:
        out.write(response.audio_content) # Write the response to the output file.
    playVASound(GCTTSPath + '/output.mp3')
    for sound in os.listdir(GCTTSPath):
        os.remove(GCTTSPath + '/' + str(sound))

def search(query):
    if 'wikipedia' in query:
        try:
            speak('Searching Wikipedia...')
            query = query.replace("wikipedia", "")
            results = wikipedia.summary(query, chars = 200)
            speak("According to Wikipedia " +results)
            speak("For more information, please browse using another device")

        except Exception as e:
            print(e)
            speak("Sorry, I ran into an error, please try again")
    elif 'the time' in query and not "in" in query:
        strTime = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {strTime}")
    elif "calculate" in query or "convert" in query or "time in" in query:
        try:
            app_id = apiKeys.wolfram
            client = wolframalpha.Client(app_id)
            if "calculate" in query:
                indx = query.lower().split().index('calculate')
                query = query.split()[indx + 1:]
            elif "convert" in query:
                indx = query.lower().split().index('convert')
                query = query.split()[indx + 1:]
            elif "time in" in query:
                indx = query.lower().split().index('time')
                query = query.split()[indx:]
            res = client.query(' '.join(query))
            answer = next(res.results).text
            speak("The answer is " + answer)
        except Exception as e:
            print(e)
            speak("Sorry, I ran into an error, please try again")
    elif 'joke' in query:
        speak(pyjokes.get_joke())

    elif 'shut down' in query:
        speak("Shutting Down Computer")
        subprocess.call("sudo shutdown now", shell=True)
    elif 'restart' in query or "reboot" in query:
        speak("Restarting Computer")
        subprocess.call('sudo reboot', shell=True)

    elif 'google' in query:
        try:
            query = query.replace("google", "")
            #Google Search Parameters
            params = {
            "engine": "google",
            "q": query,
            "api_key": apiKeys.serpAPI,
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            summary = results["knowledge_graph"]['description']
            speak(summary)
        except Exception as e:
            print(e)
            speak("Sorry, I ran into an error, please try again")
    elif 'weather' in query:
        g = geocoder.ip('me') #Getting current location
        latitude, longitude = g.latlng
        if not math.isnan(latitude) and not math.isnan(longitude):
            URL = ("http://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&appid={}&cnt=1&units=metric".format(str(latitude),str(longitude),apiKeys.openWeatherMap))
            # HTTP request
            print("URL is: " + URL)
            response =  requests.get(URL)  # gets json output
            # checking the status code of the request
            if response.status_code == 200:
                # getting data in the json format
                data = response.json()
                # getting the main dict block
                main = data["list"][0]['main']
                temperature = main['temp']
                sensation = main['feels_like']
                minTemp = main['temp_min']
                maxTemp = main['temp_max']
                humidity = main['humidity']
                report = data['list'][0]['weather'][0]['description']
                pop = data['list'][0]['pop'] #current probability of precipitation
                city = data['city']['name']
                speak("""The weather report for the city of {} is as follows: in degrees celsius, current temperature, {}, minimum temperature, {}, maximum temperature, {}, humidity,
                 {}%, probability of precipitation within the next 3 hours, {}%, the reported description of the weather is: {}""".format(str(city),str(round(temperature)),str(round(minTemp))
                 ,str(round(maxTemp)),str(round(humidity)),str(round(pop*100)),str(report)))
        else:
            # showing the error message
            speak("I couldn't retrieve the weather conditions. Make sure I'm receiving coordinates from the GNSS")
    elif 'exit' in query:
        speak('See you soon!')
        sys.exit()
    else:
        speak("I heard: " +str(query) + ", but I didn't find any action for this request. Please try again.")

#Try Except for Virtual Assistant
def virtualAssistant():
    global fp, porcupine, pa, audio_stream, firstLoop
    print("I'm ready")

    if firstLoop:
        speak("Hello, I'm your Virtual Assistant.")
        firstLoop = False


    porcupine = pvporcupine.create(access_key = apiKeys.pvporcupine,keywords=['picovoice'])

    pa = pyaudio.PyAudio()

    audio_stream = pa.open(
                    rate=porcupine.sample_rate,
                    channels=1,
                    format=pyaudio.paInt16,
                    input=True,
                    frames_per_buffer=porcupine.frame_length)
    playVASound(musicDirPath + "readyBeep.wav")
    try:
        while not mixer.music.get_busy():
            pcm = audio_stream.read(porcupine.frame_length,exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0: #If Wake Word is Triggered
                print("Hotword Detected, Talk Now!!!")
                playVASound(musicDirPath + "virtualAssistantConfirmationTone.wav")
                while mixer.music.get_busy():
                    pass
                shutdownRoutine()
                with mic as source:
                    try:
                        audio = r.listen(source, timeout=5, phrase_time_limit=5)
                        playVASound(musicDirPath + "virtualAssistantExit.wav")
                    except Exception as e:
                        print(e)
                        speak("I couldn't hear any commands, please try again.")
                        break
                    try:
                        query = r.recognize_google(audio)
                    except Exception as e:
                        print(e)
                        speak("I couldn't recognize the audio. Please make sure that there's an internet connection and you're speaking clearly.")
                        break
                    print("Google Thinks you Said: " + query.lower())
                    search(query.lower())
                    break
    except Exception as e:
        print(e)
    virtualAssistant()

def shutdownRoutine():
    global porcupine, pa, audio_stream

    if porcupine is not None:
            porcupine.delete()

    if audio_stream is not None:
        audio_stream.close()

    if pa is not None:
        pa.terminate()

if __name__ == '__main__':
    try:
        virtualAssistant()
    except Exception as e:
        print(e)