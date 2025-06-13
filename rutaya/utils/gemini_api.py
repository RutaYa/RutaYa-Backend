import google.generativeai as genai
from rutaya.models import Favorite, TravelAvailability, Destination, User

from rutaya.utils.config import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)


import google.generativeai as genai
from rutaya.utils.config import GOOGLE_API_KEY

genai.configure(api_key=GOOGLE_API_KEY)

def send_message(data):
    user_id = data.get("userId")
    current_message = data.get("currentMessage")
    previous_messages = data.get("previousMessages", [])
    memory_bank = data.get("memoryBank", {})

    # Obtener usuario
    user = User.objects.get(id=user_id)

    # Obtener favoritos
    favorite_destinations = Favorite.objects.filter(user=user).select_related('destination')
    favorite_names = [f"{fav.destination.name} - {fav.destination.location}" for fav in favorite_destinations]

    # Obtener disponibilidad
    availability_dates = TravelAvailability.objects.filter(user=user).values_list('date', flat=True)

    # Construir el prompt
    prompt = (
        "Eres un asistente virtual de la aplicación RutasYa!, especializada en recomendar paquetes turísticos dentro del Perú. "
        "Utiliza las preferencias del usuario, sus destinos favoritos y sus fechas disponibles para sugerir rutas personalizadas. "
        "No le ofrescas los paquetes a menos que el usuario te lo pida, no lo presiones, dejalo preguntar, no digas directamente sus datos o preferencias amenos que el te lo pida."
        "Tus respuestas deben ser útiles, breves y atractivas. Evita párrafos largos (máximo 100 palabras cuando sea necesario, normalmente 20 palabras)."
    )

    # Agregar preferencias del usuario
    if memory_bank:
        prompt += "\n\n🧠 *Preferencias del usuario:*\n"
        for key, value in memory_bank.items():
            if value:
                formatted_key = key.replace("_", " ").capitalize()
                prompt += f"- {formatted_key}: {value}\n"
    else:
        prompt += "\n\n🧠 *Preferencias del usuario:* No registradas.\n"

    # Agregar favoritos
    if favorite_names:
        prompt += "\n🌟 *Destinos favoritos del usuario:*\n"
        for fav in favorite_names:
            prompt += f"- {fav}\n"
    else:
        prompt += "\n🌟 *Destinos favoritos del usuario:* Ninguno aún.\n"

    # Agregar disponibilidad
    if availability_dates:
        prompt += "\n📅 *Fechas disponibles para viajar:*\n"
        for date in availability_dates:
            prompt += f"- {date}\n"
    else:
        prompt += "\n📅 *Fechas disponibles para viajar:* No registradas.\n"

    # Conversación previa
    if previous_messages:
        prompt += "\n💬 *Conversación previa:*\n"
        for msg in previous_messages:
            role = "Bot" if msg.get("isBot") else "Usuario"
            prompt += f"{role}: {msg.get('message')}\n"

    # Mensaje actual
    prompt += f"\n🧍 Usuario: {current_message}\n🤖 Bot:"

    # Enviar a Gemini
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)

    return response.text.strip()
