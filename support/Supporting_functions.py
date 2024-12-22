import hashlib
import os
import requests
import csv

from support.care import doctor_Review


def generate_id(name, date_of_birth):

  combined_string = f"{name}{date_of_birth}"
  encoded_string = combined_string.encode('utf-8')
  hashed_string = hashlib.sha256(encoded_string).hexdigest()
  numeric_id = int(hashed_string, 16) % 100000  
  formatted_id = f"P.ID-{numeric_id:05}"
  return formatted_id


ELEVENLABS_API_KEY = os.getenv("eleven_labs_api_key")  # Replace with your ElevenLabs API Key
ELEVENLABS_VOICE_ID = os.getenv("voice_id")  # Replace with the desired ElevenLabs voice ID
AUDIO_OUTPUT_DIR = 'static/audio'  # Directory to save generated audio files

if not os.path.exists(AUDIO_OUTPUT_DIR):
    os.makedirs(AUDIO_OUTPUT_DIR)

def generate_voice_with_elevenlabs(text):
    """Generate speech using ElevenLabs TTS API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.85
        }
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        # Save the audio file locally
        audio_file = os.path.join(AUDIO_OUTPUT_DIR, "response.mp3")
        with open(audio_file, "wb") as f:
            f.write(response.content)
        return audio_file
    else:
        print(f"Error: {response.json()}")
        return None




def doctor_ToDo_CSV(id,name,bod,gender, to_do, csv_file_name="doctor_to_do.csv"):
    """
    Appends patient details and doctor's to-do list to a CSV file. If the file does not exist,
    it will create the file and add the header.

    Parameters:
        patient_data (dict): Dictionary containing patient details.
                             The dictionary should have keys: 'patient_id', 'name', 'dob', 'gender', 'todo'.
        csv_file_name (str): Name of the CSV file to append to. Default is 'doctor_to_do.csv'.

    Returns:
        None
    """
    # Check if the CSV file exists
    file_exists = os.path.isfile(csv_file_name)

    # Open the file in append mode
    with open(csv_file_name, mode="a", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)

        # If the file doesn't exist, write the header
        if not file_exists:
            csv_writer.writerow(["Patient_ID", "Name", "Date_of_Birth", "Gender", "Doctor's_To-Do_List"])

        # Write the new patient and to-do data
        csv_writer.writerow([
            id,
            name,
            bod,
            gender,
            to_do
        ])

    print(f"Data for patient {name} appended to {csv_file_name} successfully.")

p = {"Patient_ID":"1991",
      "Name":"Umair",
      "Date_of_Birth": "1997-10-10",
      "Gender": "Male",
      "Doctor's_To-Do_List":"hi"
 }
#doctor_ToDo_CSV(p)


# File path for the patient history
HISTORY_FILE = 'patient_history.csv'

# Combined function: initialize and update/append patient history
def manage_patient_history(patient_id, name, dob, update_details):
    """
    Initialize the history file if not exists, then update or append patient history.

    Args:
        patient_id (str): Unique Patient ID
        name (str): Patient's Name
        dob (str): Date of Birth
        update_details (str): Diagnosis and Medications combined as a single string
    """
    # Ensure history file exists with headers
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Patient ID", "Name", "DOB", "History"])

    history_exists = False
    history_rows = []

    # Read and check existing history
    with open(HISTORY_FILE, 'r', newline='') as f:
        reader = csv.reader(f)
        history_rows = list(reader)

    for row in history_rows:
        if row[0] == patient_id:  # Match on Patient ID
            row[3] += f"; {update_details}"  # Append new history
            history_exists = True
            break

    # Append a new record if the patient ID does not exist
    if not history_exists:
        history_rows.append([patient_id, name, dob, update_details])

    # Write back the updated history
    with open(HISTORY_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(history_rows)

    print("Patient history updated successfully.")

def load_patient_history(patient_id):
    """
    Load the history of a patient from the patient_history.csv file.

    Args:
        patient_id (str): Unique Patient ID

    Returns:
        str: A string containing the patient's previous history or a message if no history exists.
    """
    # Check if the history file exists
    if not os.path.exists(HISTORY_FILE):
        return "No previous history found. Let's start a new conversation."

    # Read the history file and search for the patient_id
    history = ""
    with open(HISTORY_FILE, 'r', newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == patient_id:
                history = row[3]  # Get the patient's history
                break

    if not history:
        return "No previous history found. Let's start a new conversation."
    return history


