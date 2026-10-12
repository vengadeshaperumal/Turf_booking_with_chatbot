from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import transaction
import re
from django.shortcuts import render
from turfs.models import Turf
from .models import Conversation, ChatMessage

from django.http import JsonResponse


@login_required
@require_POST
def delete_conversation(request, chat_id):
    conversation = get_object_or_404(
        Conversation,
        id=chat_id,
        user=request.user
    )

    conversation.delete()

    return JsonResponse({
        "success": True,
        "message": "Conversation deleted successfully."
    })



def get_turf_answer(question):
    from django.db.models import Q
    from turfs.models import Turf

    question = question.strip().lower()
    text = question.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    words = set(text.split())

    if not text:
        return "Please type a question, bro 😊 I'm here to help!"

    def has_any(*keywords):
        return any(keyword in text for keyword in keywords)

    # Get the latest turf information from the database
    all_turfs = Turf.objects.all()
    turfs = all_turfs.filter(is_available=True)

    def turf_details(items):
        result = []
        for turf in items:
            result.append(
                f"🏟️ {turf.name}\n"
                f"📍 Location: {turf.location}\n"
                f"💰 Price: ₹{turf.price_per_hour} per hour\n"
                f"🕒 Time: {turf.opening_time.strftime('%I:%M %p')} "
                f"to {turf.closing_time.strftime('%I:%M %p')}\n"
                f"⚽ Facilities: {turf.facilities or 'Not specified'}"
            )
        return "\n\n".join(result)

    
    # Booking questions - English + Thanglish
    booking_keywords = [
        "how to book",
        "how to booking",
        "how to turf booking",
        "how to booking turf",
        "how to turf book",
        "turf booking",
        "booking turf",
        "book turf",
        "book a turf",
        "booking process",
        "booking procedure",
        "how can i book",
        "how do i book",
        "how to reserve",
        "reserve a turf",
        "want booking",
        "booking how",
        "how booking",
        "turf book",
        "turf ah book",
        "turf book pannanum",
        "booking epdi",
        "book panrathu",
        "book pannanum",
    ]

    if any(keyword in text for keyword in booking_keywords):
        return (
            "No worries, bro! 😊 Booking is simple:\n\n"
            "1. Log in to your account.\n"
            "2. Open the Turfs page.\n"
            "3. Select the turf you like.\n"
            "4. Choose your date and time slot.\n"
            "5. Check availability and confirm your booking.\n\n"
            "Need help with anything else, bro?"
        )


    # 1. Greetings
    if (
        words.intersection({
            "hi", "hii", "hello", "hey", "hai", "bro",
            "vanakkam", "welcome"
        })
        and len(words) <= 5
    ) or has_any("good morning", "good afternoon", "good evening"):
        return (
            "Hey bro! 😊 Welcome to Turf Assistant! 🏟️\n\n"
            "How can I help you today?\n"
            "You can ask me:\n"
            "• Which turfs are available?\n"
            "• What is the price?\n"
            "• Where is the turf?\n"
            "• How can I book a turf?"
        )

    # 2. Thanks
    if has_any(
        "thank you", "thankyou", "thanks", "thank u",
        "romba thanks", "nandri"
    ):
        return (
            "You're welcome, bro! 😊 Happy to help.\n"
            "Do you need anything else about turfs or bookings?"
        )

    # 3. Okay / acknowledgement
    if text in {
        "ok", "okay", "ok bro", "okay bro", "alright",
        "fine", "got it", "understood", "super", "seri",
        "sari", "seri bro"
    }:
        return (
            "Great bro! 😊 Is there anything else I can help you with?\n"
            "You can ask about turf prices, locations, timings, "
            "facilities, or bookings."
        )

    # 4. Conversation ending
    if text in {
        "bye", "goodbye", "bye bro", "thats all", "that is all",
        "nothing else", "no thanks", "no more questions",
        "done", "i am done", "im done"
    }:
        return (
            "Thanks for chatting with Turf Assistant, bro! 🏟️😊\n"
            "Have a great day and enjoy your game! See you again."
        )

    if text in {"no", "no bro", "nothing"}:
        return (
            "No problem, bro! 😊 If you need any turf help later, "
            "just ask me. Have a great day!"
        )

    # 5. Help / capabilities
    if has_any(
        "help me", "what can you do", "what can i ask",
        "how can you help", "any help", "help bro"
    ):
        return (
            "Of course, bro! 😊 I'll explain everything simply.\n\n"
            "1. Available turfs - ask 'show turfs'\n"
            "2. Price - ask 'rate enna' or 'price details'\n"
            "3. Location - ask 'where is the turf'\n"
            "4. Facilities - ask 'what facilities are there'\n"
            "5. Timings - ask 'when does the turf open'\n"
            "6. Booking - ask 'how to book a turf'\n"
            "7. Today's availability - ask 'is turf available today'\n\n"
            "What would you like to know, bro?"
        )

    # 6. Booking instructions
    if has_any(
        "how to book", "how can i book", "booking process",
        "book a turf", "book turf", "booking procedure",
        "how do i book", "reserve a turf", "how to reserve"
    ):
        return (
            "No worries, bro! 😊 Booking is simple:\n\n"
            "1. Log in to your account.\n"
            "2. Open the Turfs page.\n"
            "3. Select the turf you like.\n"
            "4. Choose your date and time slot.\n"
            "5. Check availability and confirm your booking.\n\n"
            "Follow the options shown on your booking page."
        )

    # 7. Today's availability
    if has_any(
        "today", "tomorrow", "right now", "currently",
        "available now", "availability today"
    ) and has_any(
        "turf", "slot", "booking", "available", "free", "vacant"
    ):
        if not turfs.exists():
            return (
                "Sorry, bro. There are no turfs currently marked as "
                "available. Please check again later."
            )

        return (
            "Sure, bro! 😊 These turfs are currently marked as available:\n\n"
            + turf_details(turfs)
            + "\n\nNote: This does not confirm a free slot for today. "
            "Please select a date and time on the booking page to "
            "check the actual slot availability."
        )

    # 8. Available turf list
    if has_any(
        "show turfs", "list turfs", "available turfs",
        "show available", "which turfs", "any turf",
        "turf iruka", "turfs iruka", "turf venum",
        "available turf", "turf list", "all turfs"
    ):
        if not turfs.exists():
            return "Sorry, bro! No turfs are currently marked as available."

        return "Here are the available turfs, bro! 😊\n\n" + turf_details(turfs)

    # 9. Price questions
    if has_any(
        "price", "pricing", "cost", "rate", "charges",
        "how much", "evlo", "evalo", "amount", "budget",
        "cheap", "cheapest", "lowest price"
    ):
        if not turfs.exists():
            return "Sorry, bro! No available turf prices were found."

        if has_any("cheap", "cheapest", "lowest price", "budget"):
            turf = turfs.order_by("price_per_hour").first()
            return (
                f"The lowest-priced available turf is {turf.name}, bro! 😊\n"
                f"Price: ₹{turf.price_per_hour} per hour.\n"
                "Please check the turf page for the latest details."
            )

        return (
            "Here are the turf prices, bro! 💰\n\n"
            + "\n".join(
                f"• {t.name}: ₹{t.price_per_hour} per hour"
                for t in turfs
            )
        )

    # 10. Location questions
    if has_any(
        "where", "location", "address", "located",
        "near me", "nearby", "enga iruku", "place"
    ):
        if not turfs.exists():
            return "Sorry, bro! No available turf locations were found."

        return (
            "Here are the available turf locations, bro! 📍\n\n"
            + "\n".join(f"• {t.name}: {t.location}" for t in turfs)
        )

    # 11. Facilities
    if has_any(
        "facility", "facilities", "amenities", "parking",
        "changing room", "washroom", "restroom", "floodlight",
        "drinking water", "shower"
    ):
        if not turfs.exists():
            return "Sorry, bro! No available turf details were found."

        return (
            "Here are the facilities listed by each turf, bro! 😊\n\n"
            + "\n".join(
                f"• {t.name}: {t.facilities or 'Facilities not specified'}"
                for t in turfs
            )
        )

    # 12. Opening and closing times
    if has_any(
        "timing", "timings", "opening time", "closing time",
        "open when", "close when", "what time", "working hours"
    ):
        if not turfs.exists():
            return "Sorry, bro! No available turf timings were found."

        return (
            "Here are the listed turf timings, bro! 🕒\n\n"
            + "\n".join(
                f"• {t.name}: {t.opening_time.strftime('%I:%M %p')} "
                f"to {t.closing_time.strftime('%I:%M %p')}"
                for t in turfs
            )
        )

    # 13. Booking status
    if has_any(
        "booking status", "my booking", "my bookings",
        "booking confirmed", "check booking", "booking details"
    ):
        return (
            "Bro, log in to your account and open your bookings page "
            "to check your booking status and details."
        )

    # 14. Cancellation
    if has_any(
        "cancel", "cancellation", "cancel booking",
        "cancel my booking"
    ):
        return (
            "Bro, check your booking page for a cancellation option. 😊\n"
            "Cancellation depends on the rules configured by the website "
            "or turf vendor. Contact the vendor if you cannot find the option."
        )

    # 15. Payment and refund
    if has_any("payment", "pay online", "refund", "money back", "upi"):
        return (
            "Bro, please check the booking page for supported payment "
            "methods. Refunds depend on your website's payment and "
            "cancellation policies."
        )

    # 16. Equipment and players
    if has_any(
        "equipment", "football", "cricket bat", "ball available",
        "number of players", "how many players", "team size"
    ):
        return (
            "Bro, equipment and player capacity depend on the selected "
            "turf. 😊 Please check its description or contact the vendor "
            "for exact details."
        )

    # 17. Search by turf name or location
    search_terms = [
        word for word in text.split()
        if word not in {
            "the", "is", "a", "an", "in", "at", "where",
            "what", "price", "location", "turf", "show",
            "please", "bro", "tell", "me", "about"
        }
    ]

    if search_terms:
        matching = Turf.objects.filter(is_available=True)
        query = Q()
        for term in search_terms:
            if len(term) >= 3:
                query |= Q(name__icontains=term) | Q(location__icontains=term)

        if query:
            matching = matching.filter(query)

        if matching.exists():
            return "I found these matching turfs, bro! 😊\n\n" + turf_details(matching)

    # 18. Friendly fallback
    return (
        "Sorry bro, I didn't fully understand that question. 😊\n\n"
        "No problem! You can ask me in simple words, like:\n"
        "• Is any turf available today?\n"
        "• Rate enna bro?\n"
        "• Where is the turf?\n"
        "• What facilities are available?\n"
        "• How to book a turf?\n\n"
        "Type 'help' to see what I can do."
    )

    
    # Sports types
    if any(word in question for word in [
        "sport", "sports", "football", "cricket",
        "futsal", "badminton", "game", "games"
    ]):
        return (
            "You can check the sports type supported by each turf "
            "on its details page. Available sports depend on the "
            "facilities and information provided by the vendor."
        )

    # Turf booking process
    if any(word in question for word in [
        "how to book", "booking process", "book a turf",
        "reserve a turf", "how can i book"
    ]):
        return (
            "Booking steps:\n"
            "1. Log in to your user account.\n"
            "2. Open the Turfs page.\n"
            "3. Select a turf.\n"
            "4. Choose your date and available time slot.\n"
            "5. Confirm the booking.\n"
            "Check the booking page for the current booking status."
        )

    # Booking status
    if any(word in question for word in [
        "booking status", "my booking", "booking confirmed",
        "check booking", "booking details"
    ]):
        return (
            "Log in to your account and open your bookings or profile "
            "page to check your booking details and status, if that "
            "feature is available in your account."
        )

    # Cancellation
    if any(word in question for word in [
        "cancel booking", "cancel my booking",
        "booking cancellation", "cancel reservation"
    ]):
        return (
            "Please check your booking details page for a cancellation "
            "option. Cancellation rules depend on the policy configured "
            "by the turf provider. Contact the vendor if no cancellation "
            "option is available."
        )

    # Payment
    if any(word in question for word in [
        "payment", "pay online", "online payment",
        "upi", "refund", "money back"
    ]):
        return (
            "Please check the booking page for the payment methods "
            "supported by this website. Payment confirmation and refunds "
            "depend on the payment features and policies configured "
            "by the website administrator."
        )

    # Advance booking
    if any(word in question for word in [
        "advance booking", "book in advance",
        "future date", "next week", "tomorrow"
    ]):
        return (
            "You can check the booking page to see which future dates "
            "are selectable. Booking depends on the dates and slots "
            "enabled by the system."
        )

    # Number of players
    if any(word in question for word in [
        "number of players", "how many players",
        "players allowed", "team size"
    ]):
        return (
            "The number of players depends on the turf size and the "
            "sports facility. Check the selected turf's description "
            "or contact its vendor for the exact capacity."
        )

    # Equipment
    if any(word in question for word in [
        "equipment", "football available", "ball available",
        "cricket bat", "sports items", "rent equipment"
    ]):
        return (
            "Equipment availability depends on the selected turf. "
            "Check its facilities description or contact the vendor "
            "to confirm whether balls, bats, or other equipment are provided."
        )

    # Parking
    if any(word in question for word in [
        "parking", "car parking", "bike parking",
        "vehicle parking"
    ]):
        parking_turfs = turfs.filter(facilities__icontains="parking")
        if parking_turfs.exists():
            return "Parking is mentioned for:\n" + "\n".join(
                f"{t.name}: {t.facilities}" for t in parking_turfs
            )
        return (
            "Parking details are not listed for the available turfs. "
            "Please contact the vendor to confirm parking availability."
        )

    # Weather and rain
    if any(word in question for word in [
        "rain", "rainy", "weather", "bad weather"
    ]):
        return (
            "For outdoor turfs, playing conditions may depend on the "
            "weather. Please contact the vendor to confirm whether "
            "the turf is open during rain."
        )

    # Opening days and holidays
    if any(word in question for word in [
        "holiday", "sunday", "monday", "weekend",
        "opening days", "which days"
    ]):
        return (
            "Please check the turf details or contact the vendor for "
            "operating days and holiday schedules. The listed opening "
            "and closing times may not specify every day's schedule."
        )

    # Vendor contact
    if any(word in question for word in [
        "vendor", "owner contact", "contact owner",
        "phone number", "contact details"
    ]):
        return (
            "Open the selected turf's details page to check whether "
            "vendor contact information is provided. If not, contact "
            "the website administrator."
        )

    # Account and registration
    if any(word in question for word in [
        "register", "create account", "sign up",
        "forgot password", "login problem", "log in problem"
    ]):
        return (
            "For registration, open the Register page and enter the "
            "required details. For login issues, verify your credentials "
            "or use the password-reset option if your website provides one."
        )

    # Turf price comparison
    if any(word in question for word in [
        "cheapest turf", "lowest price", "compare prices",
        "cheap turf", "budget turf"
    ]):
        if turfs.exists():
            cheapest = turfs.order_by("price_per_hour").first()
            return (
                f"The lowest-priced currently available turf is "
                f"{cheapest.name}, at ₹{cheapest.price_per_hour} per hour. "
                "Prices may change when vendors update their details."
            )
        return "There are no available turfs to compare right now."

    # Most expensive turf
    if any(word in question for word in [
        "most expensive", "highest price", "costliest turf"
    ]):
        if turfs.exists():
            expensive = turfs.order_by("-price_per_hour").first()
            return (
                f"The highest-priced currently available turf is "
                f"{expensive.name}, at ₹{expensive.price_per_hour} per hour."
            )
        return "There are no available turfs to compare right now."

    # Search by a city or area
    if any(word in question for word in [
        "near me", "nearby", "in my area", "in coimbatore"
    ]):
        area = question.replace("in coimbatore", "coimbatore")
        area = area.replace("nearby", "").replace("near me", "").strip()
        area = area.replace("in my area", "").strip()

        if area and area != question:
            area_turfs = turfs.filter(location__icontains=area)
        else:
            area_turfs = turfs

        if area_turfs.exists():
            return "Matching available turfs:\n" + "\n".join(
                f"{t.name} - {t.location} - ₹{t.price_per_hour}/hour"
                for t in area_turfs
            )
        return "No matching available turfs were found in the listed locations."


    # Greeting
    greetings = ["hi", "hii", "hello", "hey", "good morning", "good evening"]
    if question.strip().lower() in greetings:
        return (
            "Hello! 😊 Welcome to Turf Assistant! "
            "How can I help you today? You can ask me about "
            "available turfs, prices, locations, facilities, "
            "timings, or bookings."
        )

    # User says okay / alright
    if question.strip().lower() in [
        "ok", "okay", "okey", "alright", "fine",
        "got it", "understood", "sure"
    ]:
        return (
            "Great! 😊 Is there anything else I can help you with? "
            "You can ask me about turf availability, prices, facilities, "
            "timings, or booking."
        )

    # User says thank you
    if question.strip().lower() in [
        "thanks", "thank you", "thankyou",
        "thanks a lot", "thank you so much"
    ]:
        return (
            "You're very welcome! 😊 I'm happy to help. "
            "Do you have any other turf-related questions?"
        )

    # User finishes the conversation
    if question.strip().lower() in [
        "bye", "goodbye", "that's all", "thats all",
        "no", "no thanks", "nothing else", "no more questions",
        "i am done", "im done", "done"
    ]:
        return (
            "Thank you for using Turf Assistant! 🏟️😊 "
            "Have a great day, and enjoy your game! "
            "I'm here whenever you need help with turf bookings."
        )

    # User asks whether the bot can help
    if question.strip().lower() in [
        "can you help me", "help me", "any help",
        "what can you do", "what can i ask"
    ]:
        return (
            "Of course! 😊 I can help you with:\n"
            "🏟️ Available turfs\n"
            "💰 Turf prices\n"
            "📍 Locations\n"
            "⚽ Facilities and sports\n"
            "🕒 Opening and closing timings\n"
            "📅 Booking guidance\n\n"
            "What would you like to know?"
        )
    if question in greetings:
        return (
            "Hello! 😊 Welcome to Turf Assistant. "
            "You can ask me about available turfs, prices, locations, "
            "facilities, timings, and booking."
        )

    # Fetch current turf details from the database
    turfs = Turf.objects.filter(is_available=True)

    # Search for a particular turf name or location
    matching_turfs = turfs.filter(
        Q(name__icontains=question) |
        Q(location__icontains=question)
    )

    # Available turfs
    if any(word in question for word in [
        "available turf", "available turfs", "show turfs",
        "list turfs", "all turfs", "show available"
    ]):
        if not turfs.exists():
            return "Currently, no turfs are available. Please check again later."

        answer = "Here are the currently available turfs:\n\n"
        for turf in turfs:
            answer += (
                f"🏟️ {turf.name}\n"
                f"📍 Location: {turf.location}\n"
                f"💰 Price: ₹{turf.price_per_hour} per hour\n"
                f"🕒 Timings: {turf.opening_time.strftime('%I:%M %p')} "
                f"to {turf.closing_time.strftime('%I:%M %p')}\n\n"
            )
        return answer

    # Price questions
    if any(word in question for word in ["price", "cost", "rate", "charge"]):
        if matching_turfs.exists():
            return "\n\n".join(
                f"{t.name}: ₹{t.price_per_hour} per hour"
                for t in matching_turfs
            )

        if turfs.exists():
            return "Turf prices per hour:\n" + "\n".join(
                f"{t.name}: ₹{t.price_per_hour}"
                for t in turfs
            )

        return "No available turf prices found in the database."

    # Location questions
    if any(word in question for word in [
        "where", "location", "address", "located"
    ]):
        if matching_turfs.exists():
            return "\n\n".join(
                f"{t.name} is located at {t.location}."
                for t in matching_turfs
            )

        if turfs.exists():
            return "Available turf locations:\n" + "\n".join(
                f"{t.name}: {t.location}"
                for t in turfs
            )

        return "No available turf locations found."

    # Facilities questions
    if any(word in question for word in [
        "facilities", "facility", "amenities", "parking",
        "changing room", "floodlight"
    ]):
        if matching_turfs.exists():
            return "\n\n".join(
                f"{t.name} facilities: {t.facilities or 'No facilities added yet.'}"
                for t in matching_turfs
            )

        if turfs.exists():
            return "Turf facilities:\n" + "\n".join(
                f"{t.name}: {t.facilities or 'No facilities added yet.'}"
                for t in turfs
            )

        return "No available turf facilities found."

    # Opening and closing timings
    if any(word in question for word in [
        "timing", "timings", "opening", "closing", "open", "close"
    ]):
        if matching_turfs.exists():
            return "\n\n".join(
                f"{t.name}: {t.opening_time.strftime('%I:%M %p')} "
                f"to {t.closing_time.strftime('%I:%M %p')}."
                for t in matching_turfs
            )

        if turfs.exists():
            return "Available turf timings:\n" + "\n".join(
                f"{t.name}: {t.opening_time.strftime('%I:%M %p')} "
                f"to {t.closing_time.strftime('%I:%M %p')}"
                for t in turfs
            )

        return "No available turf timings found."

    # Booking guidance
    if any(word in question for word in [
        "book", "booking", "reserve", "reservation"
    ]):
        return (
            "To book a turf:\n"
            "1. Open the Turfs page.\n"
            "2. Select your preferred turf.\n"
            "3. Choose an available date and time slot.\n"
            "4. Confirm your booking.\n"
            "Please make sure the selected slot is available."
        )

    # Search by turf name or location
    if matching_turfs.exists():
        return "\n\n".join(
            f"{t.name}\n"
            f"Location: {t.location}\n"
            f"Price: ₹{t.price_per_hour} per hour\n"
            f"Facilities: {t.facilities or 'Not specified'}"
            for t in matching_turfs
        )

    return (
        "Sorry, I couldn't understand that question. 😊 "
        "Please ask about available turfs, prices, locations, "
        "facilities, timings, or booking."
    )


@login_required
@require_POST
def chatbot_reply(request):
    question = request.POST.get("message", "").strip()
    chat_id = request.POST.get("conversation_id", "").strip()

    if not question:
        return JsonResponse(
            {"error": "Please type a message first."},
            status=400
        )

    try:
        # Use your existing turf-answer function
        answer = get_turf_answer(question)

        with transaction.atomic():
            if chat_id:
                conversation = get_object_or_404(
                    Conversation,
                    id=chat_id,
                    user=request.user
                )
            else:
                conversation = Conversation.objects.create(
                    user=request.user,
                    title=question[:60]
                )

            ChatMessage.objects.create(
                conversation=conversation,
                question=question,
                answer=answer
            )

            conversation.updated_at = (
                __import__("django.utils.timezone", fromlist=["now"]).now()
            )
            conversation.save(update_fields=["updated_at"])

        return JsonResponse({
            "success": True,
            "answer": answer,
            "conversation_id": conversation.id,
            "title": conversation.title,
        })

    except Exception:
        # Keep technical details in the Django terminal, not in the chat.
        import logging
        logging.exception("Turf chatbot reply failed")

        return JsonResponse({
            "error": "Sorry bro, something went wrong. Please try again."
        }, status=500)

@login_required
def chatbot_page(request):
    conversations = Conversation.objects.filter(
        user=request.user
    ).order_by("-updated_at")

    # New Chat button clicked
    if request.GET.get("new") == "1":
        active_conversation = None
        messages = []
    else:
        chat_id = request.GET.get("chat_id")

        if chat_id:
            active_conversation = get_object_or_404(
                Conversation,
                id=chat_id,
                user=request.user,
            )
        else:
            active_conversation = conversations.first()

        messages = (
            list(active_conversation.messages.all())
            if active_conversation
            else []
        )

    return render(request,"chatbot/chatbot.html",{"conversations": conversations,"active_conversation": active_conversation,"messages": messages,})


