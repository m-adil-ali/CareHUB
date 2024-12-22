from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from support.Supporting_functions import generate_id, doctor_ToDo_CSV, manage_patient_history, load_patient_history
from support.care import refine_and_converse, doctor_Review, Agent_2
import pandas as pd
import os
app = Flask(__name__)
app.secret_key = os.getenv("secret_key")  # Make sure to set a secret key for sessions

DOCTOR_CREDENTIALS = {"username": "doctor", "password": "password"}
tasks = ["Review Patient X report", "Approve medication for Patient Y", "Respond to Patient Z queries"]
patient_data = []


@app.route('/')
def home():
    return render_template('base.html')


@app.route('/doctor-login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == DOCTOR_CREDENTIALS["username"] and password == DOCTOR_CREDENTIALS["password"]:
            return render_template('doctor.html', tasks=tasks)
        else:
            error = "Invalid username or password!"
            return render_template('login.html', error=error)
    return render_template('login.html')





@app.route('/patient-form', methods=['POST'])
def patient_form():
    name = request.form['name']
    dob = request.form['dob']
    gender = request.form['gender']
    patient_id = generate_id(name, dob)  # Generate a random ID

    # Store patient data in the session
    session['patient_id'] = patient_id
    session['name'] = name
    session['dob'] = dob
    session['gender'] = gender
    with open(CHAT_HISTORY_FILE, "w") as file:
        file.truncate(0)  # Clears the file content

    print(f"My name is {name}, my Date of birth is {dob}, and I am {gender}")
    history = load_patient_history(patient_id)

    first_query = (f" My Patient ID is {patient_id} "
                   f"My name is {name}. "
                   f"My date of birth is {dob}. "
                   f"My gender is {gender}." 
                   f"This is patient history{history}")
    bot_response = refine_and_converse(first_query)

    print(bot_response)

    # Call the chatbot with the stored data

    return render_template('chatbot.html', patient_id=patient_id, name=name, bot_response = bot_response)




# Define the file path where chat history will be stored
CHAT_HISTORY_FILE = 'chat_history.txt'
@app.route('/chatbot', methods=['POST'])
def chatbot():



    user_message = request.form['message']
    bot_response = refine_and_converse(user_message)

    # Save the chat history to the file
    save_chat_history_to_file(user_message, bot_response)

    print(bot_response)
    if bot_response == "Thank you! Would you like to submit the application?" or user_message.lower() == "goodbye":
        # Summarize the conversation
        #summary = summarize_chat_history()

        #print("Conversation Summary:", summary)
        print("stopped")

        # Save the conversation summary to the file
        #save_chat_history_to_file("Summary", summary)

        return jsonify({
            "bot_response": "The conversation has ended. Doctor will review your application.",
            "show_popup": True
        })

    return jsonify({"bot_response": bot_response, "show_popup": False})

def summarize_chat_history():
    # Read the chat history from the file
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r') as file:
            chat_history = file.read()

        # Pass the conversation to the summary function
        summary = Agent_2.send_message(f"Summazrize the entire chat extract important information including symptoms. Also extract the summary provided in the chat: {chat_history}").text
        #print("This is check point: ",summary)
        return summary
    else:
        return "No chat history found."

def save_chat_history_to_file(user_message, bot_response):
    # Prepare the content to write to the file
    content = f"Patient: {user_message}\nMedi: {bot_response}\n\n"

    # Write the content to the file (append mode)
    with open(CHAT_HISTORY_FILE, 'a') as file:
        file.write(content)

    print(f"Chat history has been saved to {CHAT_HISTORY_FILE}")

@app.route('/success')
def success_page():
    # Retrieve patient data from the session
    summary = summarize_chat_history()
    patient_id = session.get('patient_id')
    name = session.get('name')
    dob = session.get('dob')
    gender = session.get('gender')
    print(summary)
    if not all([patient_id, name, dob, gender]):
        return redirect(url_for('home'))  # Redirect to home if patient data is not found

    # Process doctor to-do list and save to CSV
    doctor_to_do = doctor_Review(summary)
    doctor_ToDo_CSV(patient_id, name, dob, gender, doctor_to_do)
    with open(CHAT_HISTORY_FILE, "w") as file:
        file.truncate(0)  # Clears the file content

    print("Agent 3 complete his work.")
    return render_template('Application_Submitted.html')




CSV_FILE = 'doctor_to_do.csv'
@app.route('/get_patients', methods=['GET'])
def get_patients():
    """
    Fetch all Patient_IDs from the CSV file and return them as a JSON response.
    This populates the sidebar in the doctor's to-do list HTML file.
    """
    try:
        # Reload the CSV to ensure the latest data
        df = pd.read_csv(CSV_FILE)
        patients = df[['Patient_ID']].to_dict(orient='records')  # Fetch only Patient_ID column
        return jsonify(patients)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_patient_todo/<patient_id>', methods=['GET'])
def get_patient_todo(patient_id):
    """
    Fetch the 'Doctor's_To-Do_List' for a specific patient based on their Patient_ID.
    """
    try:
        # Reload the CSV to ensure the latest data
        df = pd.read_csv(CSV_FILE)
        patient = df[df['Patient_ID'] == patient_id].to_dict(orient='records')  # Filter for the specific Patient_ID
        if patient:
            return jsonify(patient[0])  # Return the first matching record
        return jsonify({'error': 'Patient not found'}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/update_todo/<patient_id>', methods=['POST'])
def update_todo(patient_id):
    """
    Add the updated or unchanged to-do list as 'prescribed_medication' to 'approval.csv'.
    Leave 'doctors_to_do.csv' unchanged.
    """
    try:
        # Get the updated to-do list from the request
        updated_todo = request.json.get('todo')
        if not updated_todo:
            return jsonify({'error': 'No to-do data provided'}), 400

        # Load the approval.csv or create a new DataFrame if it doesn't exist
        try:
            approval_df = pd.read_csv('approval.csv')
        except FileNotFoundError:
            # If the file doesn't exist, create an empty DataFrame with appropriate columns
            approval_df = pd.DataFrame(columns=['Patient_ID', 'Prescribed_Medication'])

        # Check if the patient already exists in the approval.csv
        if patient_id in approval_df['Patient_ID'].values:
            # Update the 'Prescribed_Medication' for the existing patient
            approval_df.loc[approval_df['Patient_ID'] == patient_id, 'Prescribed_Medication'] = updated_todo
        else:
            # Append the new patient and their prescribed medication
            new_row = {'Patient_ID': patient_id, 'Prescribed_Medication': updated_todo}
            approval_df = pd.concat([approval_df, pd.DataFrame([new_row])], ignore_index=True)

        # Save the updated approval DataFrame back to the CSV
        approval_df.to_csv('approval.csv', index=False)


        return jsonify({'success': True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500







@app.route('/application-status', methods=['GET', 'POST'])
def application_status():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        dob = request.form['dob']
        #gender = request.form['gender']
        patient_id = generate_id(name, dob)  # Generate a random ID or calculate ID
        print(f"Id {patient_id}")
        # Read approval.csv and search for patient_id
        data = pd.read_csv("approval.csv")
        patient_info = data[data["Patient_ID"] == patient_id]

        # Check if patient exists in the approval list
        if not patient_info.empty:
            # Extract prescribed medication
            prescribed_medication = patient_info["Prescribed_Medication"].iloc[0]
            # Create a dictionary for rendering on the page
            application_stat = {
                "status": "Reviewed",
                "prescribed_medication": prescribed_medication
            }
            manage_patient_history(patient_id,name,dob,prescribed_medication)

        else:
            # If patient is not found
            application_stat = {
                "status": "Not Reviewed",
                "prescribed_medication": "No prescribed medication available."
            }

        # After form submission, show application status and medication
        return render_template('application_status.html', application_status=application_stat)

    # For GET request, render the page with the form (if applicable)
    return render_template('base.html')





if __name__ == '__main__':
    app.run(debug=True)
