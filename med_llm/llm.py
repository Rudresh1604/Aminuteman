from langchain_huggingface import HuggingFaceEndpoint
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from typing import List
from langchain_core.documents import Document
from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser

from langchain_core.runnables import RunnablePassthrough
import os
from langchain.retrievers.document_compressors import LLMChainFilter
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor



dotenv_path = '.env'
load_dotenv(dotenv_path)
HUGGINGFACEHUB_API_TOKEN = os.getenv("HF_TOKEN")
if HUGGINGFACEHUB_API_TOKEN is None:
    raise ValueError("HF_TOKEN not found in the .env file or the file path is incorrect")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACEHUB_API_TOKEN
repo_id = "meta-llama/Meta-Llama-3-8B-Instruct"

def format_docs(docs: List[Document]):
    return "\n\n".join(doc.page_content for doc in docs)

def format_answer(answer: str):
    # Remove repetitive "Sorry, I don't know" and other extraneous lines
    lines = answer.split("\n")
    filtered_lines = []
    for line in lines:
        if not line.startswith("System: Sorry, I don't know") and not line.startswith("System:"):
            filtered_lines.append(line)
    return "\n".join(filtered_lines).strip()



def QA(question,memory):
    llm = HuggingFaceEndpoint(
        repo_id='meta-llama/Meta-Llama-3-8B-Instruct',
        task="text-generation",
        max_new_tokens=1024,  # Allow more tokens if needed for completeness
        do_sample=False,
        repetition_penalty=1.03,
        temperature = 0.5
    )
    
    # Refined Few-Shot Examples for Short and Complete Answers
    few_shot_examples = [
        {
            "question": "What are the possible diagnoses for chest pain?",
            "answer": "Possible diagnoses include: 1. Acute coronary syndrome (ACS) – Myocardial infarction (MI) or unstable angina (UA), 2. Pulmonary embolism (PE), 3. Aortic dissection (AD), 4. Costochondritis or other musculoskeletal disorders."
        },
        {
            "question": "What tests are recommended for suspected myocardial infarction?",
            "answer": "Recommended tests include: 1. ECG to detect ischemia or infarction, 2. Troponin levels to assess cardiac injury, 3. Chest CT to rule out PE and AD, 4. Echocardiogram to evaluate heart function."
        },
        {
            "question": "What are the common management strategies for acute coronary syndrome?",
            "answer": "Management strategies include: 1. Aspirin to prevent thrombus formation, 2. Beta blockers to reduce heart workload, 3. Nitroglycerin to relieve pain, 4. Oxygen to improve tissue oxygenation, 5. Anticoagulation therapy to prevent further clotting."
        }
    ]
    
    system_prompt = (
        "You are a medical AI assistant. Provide answers that are short yet complete. Ensure key information is included, but avoid lengthy explanations.If needed provide information in detail "
        "Don't repeat the answers again and again"
        "If the answer is about diagonsis or treatment, provide a brief overview of the possible diagnoses or treatment options. "
        "display the answers neatly instead of a long paragraph"
        "format the answers properly"
        "If the user explicitly requests the information, you can provide more details.Remember follow up request should be done only if the user ask for it.I just gave a pattern. Here are some guidelines:\n\n"
    "Q: What are the symptoms of diabetes?\n"
    "A: Common symptoms of diabetes include increased thirst, frequent urination, extreme hunger, unexplained weight loss, fatigue, irritability, blurred vision, slow-healing sores, and frequent infections.\n"
    
    "Detailed Answer: These symptoms occur because diabetes affects the body’s ability to produce or use insulin, leading to high blood sugar levels. Increased thirst and frequent urination are due to the kidneys working harder to eliminate excess glucose."
                      "Extreme hunger and weight loss result from the body’s inability to use glucose for energy. Fatigue and irritability are caused by insufficient glucose in cells, while blurred vision, slow-healing sores, and frequent infections are due to damaged blood vessels and impaired immune function.\n\n"
    "Q: How is hypertension treated?\n"
    "A: Hypertension is treated with lifestyle changes such as a healthier diet, regular exercise, and weight loss. Medications like diuretics, ACE inhibitors, calcium channel blockers, and beta-blockers may also be prescribed.\n"
    
    "Detailed Answer: Side effects of diuretics can include frequent urination and electrolyte imbalances. ACE inhibitors might cause a persistent dry cough, increased potassium levels, and in rare cases, angioedema."
                      " Calcium channel blockers can cause swelling in the lower extremities, constipation, and dizziness. Beta-blockers may lead to fatigue, cold hands and feet, and a slower heart rate.\n\n"
    "Q: How should an asthma attack be managed?\n"
    "A: An asthma attack should be managed by using a quick-relief inhaler (e.g., albuterol), seeking immediate medical help if the symptoms do not improve, sitting upright, and remaining calm. Avoid triggers and follow the asthma action plan provided by a healthcare provider.\n"
    
    "Detailed Answer: Quick-relief inhalers work by delivering medication directly to the lungs, where they quickly relax the muscles around the airways. This helps to open up the airways, making it easier to breathe. "
                      "The medications, typically bronchodilators like albuterol, act within minutes and are essential during an asthma attack to alleviate acute symptoms.\n\n"
    "Q: What are some ways to relieve a migraine?\n"
    "A: Migraine relief can include resting in a dark, quiet room; applying a cold compress to the forehead; staying hydrated; taking over-the-counter pain relief medication (e.g., ibuprofen or aspirin); and using prescribed migraine-specific medications if available.\n"
    
    "Detailed Answer: Common triggers for migraines include hormonal changes (especially in women), certain foods and drinks (like aged cheese, alcohol, and caffeine), stress, sensory stimuli (bright lights, loud sounds, strong smells), changes in sleep patterns, physical factors (intense physical exertion), and changes in the environment (weather changes, altitude).\n\n"
    "Q: What are the warning signs of a stroke?\n"
    "A: Warning signs of a stroke include sudden numbness or weakness in the face, arm, or leg, especially on one side of the body; sudden confusion; trouble speaking or understanding speech; sudden trouble seeing in one or both eyes; sudden trouble walking; dizziness; loss of balance or coordination; and sudden severe headache with no known cause.\n"
    
    "Detailed Answer: If you suspect someone is having a stroke, it is critical to act FAST: Face (ask the person to smile; does one side droop?), Arms (ask the person to raise both arms; does one arm drift downward?), Speech (ask the person to repeat a simple phrase; is their speech slurred or strange?), Time (if you observe any of these signs, call emergency services immediately). "
                      "Prompt medical treatment can significantly improve the chances of recovery and reduce the risk of severe disability or death.\n\n"
        "Don't repeat 'Sorry, I don't know' multiple times. "
        "Don't create questions on your own and answer it yourself.Just give the solution to the user,that's it."
        "If the reference documents do not answer the question, respond with 'Sorry, I don't know'. Here are examples of how to balance brevity and completeness:\n\n"
        "Q: What are the possible diagnoses for chest pain?\n"
    "A: Possible diagnoses include: 1. Acute coronary syndrome (ACS) – Myocardial infarction (MI) or unstable angina (UA),"
                                   "2. Pulmonary embolism (PE),"
                                   "3. Aortic dissection (AD), "
                                   "4. Costochondritis or other musculoskeletal disorders.\n\n"
    "Q: What tests are recommended for suspected myocardial infarction?\n"
    "A: Recommended tests include: 1. ECG to detect ischemia or infarction,"
                                   "2. Troponin levels to assess cardiac injury,"
                                   "3. Chest CT to rule out PE and AD,"
                                   "4. Echocardiogram to evaluate heart function.\n\n"
    "Q: What are the common management strategies for acute coronary syndrome?\n"
    "A: Management strategies include: 1. Aspirin to prevent thrombus formation, "
                                       "2. Beta blockers to reduce heart workload, "
                                       "3. Nitroglycerin to relieve pain, "
                                       "4. Oxygen to improve tissue oxygenation, "
                                       "5. Anticoagulation therapy to prevent further clotting.\n\n"
    "Q: What are the symptoms of diabetes?\n"
    "A: Common symptoms of diabetes include increased thirst, frequent urination, extreme hunger, unexplained weight loss, fatigue, irritability, blurred vision, slow-healing sores, and frequent infections.\n\n"
    "Q: How is hypertension treated?\n"
    "A: Hypertension is treated with lifestyle changes such as a healthier diet, regular exercise, and weight loss. Medications like diuretics, ACE inhibitors, calcium channel blockers, and beta-blockers may also be prescribed.\n\n"
    "Q: What are the warning signs of a stroke?\n"
    "A: Warning signs of a stroke include sudden numbness or weakness in the face, arm, or leg, especially on one side of the body; sudden confusion; trouble speaking or understanding speech; sudden trouble seeing in one or both eyes; sudden trouble walking; dizziness; loss of balance or coordination; and sudden severe headache with no known cause.\n\n"
    "Q: How should an asthma attack be managed?\n"
    "A: An asthma attack should be managed by using a quick-relief inhaler (e.g., albuterol), seeking immediate medical help if the symptoms do not improve, sitting upright, and remaining calm. Avoid triggers and follow the asthma action plan provided by a healthcare provider.\n\n"
    "Q: What are some ways to relieve a migraine?\n"
    "A: Migraine relief can include resting in a dark, quiet room; applying a cold compress to the forehead; staying hydrated; taking over-the-counter pain relief medication (e.g., ibuprofen or aspirin); and using prescribed migraine-specific medications if available.\n\n"
    )
    
    for example in few_shot_examples:
        system_prompt += f"Q: {example['question']}\nA: {example['answer']}\n\n"
    
    #system_prompt += "Reference documents: {context}\n\n"
    #system_prompt += "User question: {input}"

    conversation_history = memory.load_memory_variables({"input": question})
    print("Conversation history loaded:", conversation_history)  # Debugging statement

    history_text = ""
    if conversation_history.get("history"):
        for item in conversation_history["history"].split("\nAI response: "):
            if item.strip():
                q_and_a = item.split("\n", 1)
                if len(q_and_a) == 2:
                    history_text += f"Q: {q_and_a[0].replace('Human:', '').strip()}\nA: {q_and_a[1].strip()}\n"

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", f"{history_text}\n{question}"),
        ]
    )
    
    embeddings = HuggingFaceInferenceAPIEmbeddings(
        api_key=HUGGINGFACEHUB_API_TOKEN, model_name="sentence-transformers/all-MiniLM-l6-v2"
    )

    vectordb = Chroma(persist_directory='vectordb3/chroma', embedding_function=embeddings)
    retriever = vectordb.as_retriever(search_type="mmr", search_kwargs={"k": 3})

    _filter = LLMChainFilter.from_llm(llm)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=_filter, base_retriever=retriever
    )

    

    rag_chain_from_docs = (
        RunnablePassthrough.assign(context=(lambda x: format_docs(x["context"])))
        | prompt
        | llm
        | StrOutputParser()
    )
    retrieve_docs = (lambda x: x["input"]) | retriever
    chain = RunnablePassthrough.assign(context=retrieve_docs).assign(
        answer=rag_chain_from_docs
    )
    
    result = chain.invoke({"input": question})
    memory.save_context({"input": question}, {"response": result['answer']})
    return result['answer']
    