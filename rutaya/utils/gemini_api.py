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
    prompt = """
        Eres un asistente virtual de la aplicación RutasYa!, especializada en recomendar paquetes turísticos dentro del Perú. 
        Utiliza las preferencias del usuario, sus destinos favoritos y sus fechas disponibles para sugerir rutas personalizadas. 
        No le ofrezcas los paquetes a menos que el usuario te lo pida, no lo presiones, déjalo preguntar, no menciones directamente que tienes sus datos o preferencias pero siempre realiza una reconfirmacion de la cantidad de personas y de sus preferencias antes de generar un paquete.

        Tus respuestas deben ser útiles, breves y atractivas. Evita párrafos largos (máximo 100 palabras cuando sea necesario, normalmente 20 palabras).
        Mientras conversas sobre el posible destino, presenta sugerencias de lugares cercanos dependiendo de la cantidad de días que se vaya a viajar.

        IMPORTANTE: Si el usuario te dice que ya puedes generar el paquete de viaje, entonces responderás en formato JSON con los siguientes campos:
        - title: Título atractivo del paquete
        - description: Descripción general del viaje
        - start_date: YYYY-MM-DDTHH:MM
        - days: Número de días del viaje
        - quantity: Número de personas
        - price: Precio total en soles peruanos
        - itinerary: Lista de actividades detalladas por fecha y hora

        El itinerario debe seguir esta estructura:
        [
          {
            "datetime": YYYY-MM-DDTHH:MM,
            "description": "Salida desde Lima hacia Cusco - Vuelo de mañana"
          },
          {
            "datetime": YYYY-MM-DDTHH:MM,
            "description": "Llegada a Cusco - Check-in hotel y almuerzo"
          },
          {
            "datetime": YYYY-MM-DDTHH:MM,
            "description": "City tour por el centro histórico de Cusco"
          }
        ]
        
        ES IMPORTANTE QUE LAS FECHAS SEAN EN YYYY-MM-DDTHH:MM,

        REGLAS PARA EL ITINERARIO:
        - Para viajes de 1-2 días: Itinerario detallado por hora
        - Para viajes de 3-5 días: Itinerario por bloques de tiempo (mañana, tarde, noche)
        - Para viajes de 6+ días: Itinerario por días con actividades principales
        - Siempre incluye múltiples destinos cercanos según los días disponibles
        - Considera tiempo de traslados entre destinos
        - Incluye comidas, descansos y actividades culturales/naturales
        - Mantén un flujo lógico geográfico para optimizar el recorrido

        Ejemplo de destinos cercanos por región:
        - Cusco: Machu Picchu, Valle Sagrado, Ollantaytambo, Pisac
        - Lima: Pachacamac, Barranco, Miraflores, Callao
        - Arequipa: Colca, Chivay, Yanahuara, Sabandía
        - Trujillo: Huacas del Sol y Luna, Chan Chan, Huanchaco
        """;

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
