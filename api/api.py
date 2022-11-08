import requests
from shared.generalData import SOUND_FILE_NAME
from pydub import AudioSegment
from shared.generalFunctions import SoundAPIResponse

SPEECH_DB_BASE_URL = "https://speech-db.altlab.app"

def get_sound(query):
    '''
    Fetches the sound from the speech-db api
    
    Returns status. 
    (1 = Successful. 2 = Connection Error, 
    3 = No audio available, 4 = Audio currently unavailable due to server problems)
    '''
    try:
        response = requests.get(SPEECH_DB_BASE_URL + "/maskwacis/api/bulk_search" + "?" + "q=" + query)
        if not response.ok:
            # Audio not available as speech-db is probably down/bad request.
            return SoundAPIResponse.API_NO_HIT
    except:
        return SoundAPIResponse.CONNECTION_ERROR # Connection error
    
    jsonized_response = response.json()
    
    audio_url = None
    
    if len(jsonized_response["matched_recordings"]) > 0:
        audio_url = jsonized_response["matched_recordings"][0]["recording_url"]
        
        # Write sound to a local file in the same directory
        sound_file = open("sound.m4a", "wb")
        
        with requests.get(audio_url) as f:
            sound_bytes = f.content
            sound_file.write(sound_bytes)
        
        # Convert to .wav
        wav_sound = AudioSegment.from_file("sound.m4a", format="m4a")
        
        wav_sound.export(SOUND_FILE_NAME, format="wav")
        
        sound_file.close()
    else:
        # Make a call to the moswacihk api to get the recording.
        try:
            response = requests.get(SPEECH_DB_BASE_URL + "/moswacihk/api/bulk_search" + "?" + "q=" + query)
            if not response.ok:
            # Audio not available as speech-db is probably down/bad request.
                return SoundAPIResponse.API_NO_HIT
        except:
            print("Connection error!")
            return SoundAPIResponse.CONNECTION_ERROR # Connection error
        jsonized_response = response.json()
    
        audio_url = None
        
        if len(jsonized_response["matched_recordings"]) > 0:
            audio_url = jsonized_response["matched_recordings"][0]["recording_url"]
            
            # Write sound to a local file in the same directory
            sound_file = open("sound.m4a", "wb")
            
            with requests.get(audio_url) as f:
                sound_bytes = f.content
                sound_file.write(sound_bytes)
            
            # Convert to .wav
            wav_sound = AudioSegment.from_file("sound.m4a", format="m4a")
            
            wav_sound.export(SOUND_FILE_NAME, format="wav")
            
            sound_file.close()
        else:
            # No results found
            return SoundAPIResponse.NO_AUDIO_AVAILABLE
    
    return SoundAPIResponse.SUCCESSFUL
        
         
    