import requests
import urllib

SPEECH_DB_BASE_URL = "https://speech-db.altlab.app"

def get_sound(query):
    '''
    '''
    response = requests.get(SPEECH_DB_BASE_URL + "/maskwacis/api/bulk_search" + "?" + "q=" + query)
    
    jsonized_response = response.json()
    
    audio_url = None
    
    if len(jsonized_response["matched_recordings"]) > 0:
        audio_url = jsonized_response["matched_recordings"][0]["recording_url"]
        
        # Write sound to a local file in the same directory
        sound_file = open("sound.m4a", "wb")
        
        with urllib.request.urlopen(audio_url) as f:
            sound_bytes = f.read()
            sound_file.write(sound_bytes)
        
        sound_file.close()
    
    return True
        
         
    