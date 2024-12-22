from pinecone import Pinecone
from gensim.models import Word2Vec
import pandas as pd
import numpy as np
import pickle
import nltk
from nltk.tokenize import MWETokenizer, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from dotenv import load_dotenv
'''
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt_tab')
'''
import os
import google.generativeai as genai

load_dotenv()

# Configure the Generative AI client with the API key
genai.configure(api_key=os.getenv("gemini_api_key"))

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

# Agent_1 for Input preprocessing
model_1 = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction="""
  TASKS:
    1. Correct all spelling mistakes.
    2. Fix grammatical errors.
    3. Normalize the text:
        - Convert the text to lowercase.
        - Remove any extra spaces.
        - Ensure proper punctuation is used.
        - Do not change words if it is already in English. like No, Yes, Normal, Low, and High
    4. Return the cleaned and corrected text.
    5. Do not use contractions.
    6. Translate the text into English if it is not already.
    7. If the user says "bye," "goodbye," or indicates they wish to stop, always respond with a polite farewell.
  """
  )
Agent_1 = model_1.start_chat(
  history=[]
)
response = Agent_1.send_message("hi")
print(response.text)

# Agent_2 for AI medical Diagnoses
model_2 = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="""
    You are a polite and helpful healthcare assistant your name is Medi. Your job is to:
    1. Name, date of brith and gender will be given through a form. If patient have any previous history ask for it health status and Response with greetings and positive attitude before collecting the further data.
       when patient says hi or somthing like this return greedings. And ask how he is feeling from the past diagnose. Does recover properly only if it have past history. 
       Start with a greeting the patient humbly and establish a friendly tone.
       And let the patient's name as it is; don't call them by the translation of their name.
    2. Collect the following information step by step:
       - please add "\\n" on every line ends so I can display it in a good manners.
       - Greet the patient once the greeting ends then start asking next questions.
       - Do not repeat one question if you get the clear answer. Do not stuck into a loop. And avoid Hallucination.
       - How are you feeling today?
       - Blood Pressure status (HIGH/LOW/NORMAL)
       - Diabetic status (YES/NO)
       - Symptoms: Ask one by one
       - Ask the patient to describe their symptoms in detail.
       - Follow up with these questions to extract more information: ask one by one
       - If you ask more than one question at a time the patient will panic so please ask question on at a time.
        a.What do the symptoms feel like?
        b. Ask associated questions to the symptoms, ask related one?
        c. *Associated symptoms:* Suggest the Associated symptoms according to patient described symptoms?
        d. Duration of symptoms (in days, weeks, etc.)?
        e. *Severity:* On a scale of 1 to 10, how severe are the symptoms? (1 = mild, 10 = severe)?
    3. After collecting all the details, present the all information back to the patient
       in a summarized and well-structured format for verification.
    4. Ask the patient if the information is correct:
       - If the patient confirms (YES), always only respond with: "Thank you! Would you like to submit the application?".
       - If the patient wants to edit any information (NO):
         - Ask which field they want to edit.
         - Update the information based on their input.
         - Repeat the process until the patient confirms all details are accurate.
    5. Maintain a professional yet empathetic tone throughout the interaction.
    6. Modification 1: If the user input contains any vulgar or offensive language,
       respond with "I'm sorry, I cannot process that request. Please use respectful language." and terminate the conversation.**
    7. Modification 2: If the user provides irrelevant information or goes off-topic,
       politely guide them back to the relevant questions and information needed.**
    """
    )

Agent_2 = model_2.start_chat(history=[])
response = Agent_2.send_message("Hi")
print(response.text)

# Agent_3 for Diesease Diagnose and Treatment recommandations.
model_3 = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="""
  You are a healthcare assistant agent (Agent 3). Your job is to analyze patient information, identify similar cases, and generate a concise report for doctor review.

Input:
1. Patient Summary: A detailed summary of the patient's current condition, including:
    - Demographics: Name, age, gender, unique patient ID
    - Symptoms: Description of the symptoms experienced
    - Medical History (if any): Past medical conditions or treatments
2. Similarity Results: A list of similar cases from the database, including:
    - Metadata (e.g., past diagnoses, medications)
    - Similarity scores

Tasks:
1. Analyze Patient Information:
    - Carefully review the patient summary and similarity results.
    - Identify key symptoms, relevant medical history, and demographic factors.
2. Generate Doctor Review Report:
    - Patient Information: Display the patient's name, age, gender, and unique ID.
    - Symptoms Summary: Provide a concise description of the patient's reported symptoms.
    - Potential Diagnosis: Based on symptoms and similar cases, suggest a possible diagnosis or a few differential diagnoses.
    - Similar Cases: Include the top 2-3 most similar cases with their IDs, metadata (past diagnosis, medications), and similarity scores. 
    - Recommended Medicine: Based on the diagnosis, similar cases, patient age, and similarity scores, recommend 1-2 appropriate medications with dosage and relevant notes (e.g., age restrictions, potential side effects).
    - Medical History: If available, include a brief summary of the patient's relevant medical history.

Output:
- Current Date: Doctor Short review that only have name,Symptopms, Diagonos and medication. Keep it as short as possible. Also make Headings of each section.
"""
)

Agent_3 = model_3.start_chat(history=[])

# Summary Preproccessing and tokenization then Embedding model is Word2Vec and the Vector Database is Pinecone.
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
def preprocess_text(text):
    mwe = MWETokenizer([('chest', 'pain'), ('abdominal', 'pain'), ('body', 'pain')], separator=' ')
    tokens = mwe.tokenize(word_tokenize(text))
    tokens = [lemmatizer.lemmatize(word.lower()) for word in tokens if word.lower() not in stop_words]
    return (tokens)

script_dir = os.path.dirname(__file__)

# Define the full path to the model.pkl file
Treatment_model_path = os.path.join(script_dir, 'Treatment_model.pkl')
Diagnose_model_path = os.path.join(script_dir, 'Diagnose_Model.pkl')


# Load the Word2Vec model
with open(Treatment_model_path, 'rb') as file:
    Embedding_Treatment_model = pickle.load(file)
# Load the Word2Vec model
with open(Diagnose_model_path, 'rb') as file:
    Embedding_Diagnose_model = pickle.load(file)
    
# load pinecone with API key
pc = Pinecone(api_key= os.getenv('pinecone_api_key'))
# call the index from the data base
index_treatment = pc.Index("data-carehub")
index_diagnose = pc.Index("diagnose")

# Function to Search in vector database
def qurey_Search(query_symptoms,index,embedding_model):
  query_symptoms = preprocess_text(query_symptoms)
  query_embedding = get_embedding(query_symptoms,embedding_model)
  query_embedding_list = query_embedding.tolist()
  results = index.query(namespace = "ns1",vector = query_embedding_list, top_k=3, include_values = True, include_metadata=True,filter={})
  return results



# Function to generate embeddings for symptoms
def get_embedding(symptoms_list,model):
    vectors = [model.wv[word] for word in symptoms_list if word in model.wv]
    vectors = [v.astype(float) for v in vectors]
    return sum(vectors) / len(vectors) if vectors else np.array([0.0] * 3072)


# Patient talking part and workflow
def refine_and_converse(user_input):
    """
    Refines user input, engages in conversation,
    and generates a summary at the end.
    """
    # Refine user input with Agent 1
    refined_input = Agent_1.send_message(user_input).text
    # Pass refined input to Agent 2 for conversation
    agent_2_response = Agent_2.send_message(user_input).text
    #print(f"CareHUB: {agent_2_response}")
    return agent_2_response


def doctor_Review(summary):
    # Generate summary using Agent 2 after conversation ends

    # Searching Vector Database for similarities of Diasease and Treatments
    print("Proceeding to database search...")
    result_Treat = qurey_Search(summary,index_treatment,Embedding_Treatment_model)
    result_Diag= qurey_Search(summary,index_diagnose,Embedding_Diagnose_model)


    # Fetch out the best results based on the similarity score greater than 80%
    for r1, r2 in zip(result_Treat["matches"], result_Diag["matches"]):
      #Your code to process r1 and r2
      #if r1['score'] > 0.8:
        print(f"Patient ID: {r1['id']}, Metadata: {r1['metadata']}")
        print(f"Similarity: {r1['score']}")
     # if r2['score'] > 0.8:
        print(f"Patient ID: {r2['id']}, Metadata: {r2['metadata']}")
        print(f"Similarity: {r2['score']}")
      #else:
        #print("No matching patients found.")


    # Now create a prompt for the Agent 3.
    prompt = f"""
    Current Patient:
    {summary}
    Similar Cases and Treatment:
    """
    def add_similar_cases(prompt, results):
       for result in results:
         prompt += f"- Patient ID: {result['id']}, Metadata: {result['metadata']}, Similarity Score:{result['score']}\n"
       return prompt

    prompt = add_similar_cases(prompt, result_Treat["matches"])
    prompt += f"\nDiagnose and Symptoms:\n"
    prompt += add_similar_cases(prompt, result_Diag["matches"])

    # Pass the prompt to Agent_3 to genrate prompt for Doctor
    doctor_review = Agent_3.send_message(prompt).text
    print(doctor_review)
    return doctor_review