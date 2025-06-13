import google.generativeai as genai

from rutaya.utils.config import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)


def send_message(data):
    current_message = data.get("currentMessage")
    previous_messages = data.get("previousMessages", [])
    memory_bank = data.get("memoryBank", [])

    # Construimos un prompt para Gemini
    ##prompt = "Eres un asistente veterinario virtual. Basado en la siguiente información de las mascotas y de las conversaciones previas que tuviste con el usuario, responde al mensaje del usuario. Se preciso y especifico en tus comentarios y consejos, recuerda que se trata de la vida de una mascota. Limita tu respuesta a maximo 100 palabras solo de ser necesario, normalmente tus respuesta seran cortas (20 palabras) para no abrumar al usuario."

    # Incluir las mascotas
    ##prompt += "Mascotas registradas:\n"
    ##for pet in memory_bank:
    ##    prompt += f"- {pet['name']}, {pet['type']}, raza {pet['breed']}, {pet['gender']}, edad {pet['age']}, peso {pet['weight']}\n"

    # Incluir el historial de mensajes
    ##prompt += "\nConversación previa:\n"
    ##for msg in previous_messages:
    ##    role = "Bot" if msg["isBot"] else "Usuario"
    ##    prompt += f"{role}: {msg['message']}\n"

    # Incluir el mensaje actual
    ##prompt += f"\nUsuario: {current_message}\n"
    ##prompt += "Bot:

    prompt = "Solo quiero hablar"

    # Enviar a Gemini
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)

    return response.text.strip()