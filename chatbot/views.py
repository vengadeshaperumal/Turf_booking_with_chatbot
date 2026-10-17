
import re
import logging

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from turfs.models import Turf
from .models import Conversation, ChatMessage


logger = logging.getLogger(__name__)


# --------------------------------------------------
# TURF CHATBOT ANSWER ENGINE
# --------------------------------------------------

def get_turf_answer(question):
    """
    Answers common turf-related questions using keywords
    and current data stored in the Turf database.
    """

    text = (question or "").lower().strip()

    # Normalize common English contractions.
    replacements = {
        "can't": "cannot",
        "won't": "will not",
        "what's": "what is",
        "where's": "where is",
        "i'm": "i am",
        "i've": "i have",
        "i'd": "i would",
        "you're": "you are",
        "it's": "it is",
        "don't": "do not",
        "doesn't": "does not",
        "how's": "how is",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return "Please type your question, bro! 😊 I can help with turf details and bookings."

    words = set(text.split())

    def has_any(*keywords):
        return any(keyword in text for keyword in keywords)

    def has_words(*keywords):
        return any(keyword in words for keyword in keywords)

    # Always get current turf details from the database.
    all_turfs = Turf.objects.all()
    turfs = all_turfs.filter(is_available=True)

    def turf_details(items):
        output = []

        for turf in items:
            output.append(
                f"🏟️ {turf.name}\n"
                f"📍 Location: {turf.location}\n"
                f"💰 Price: ₹{turf.price_per_hour} per hour\n"
                f"🕒 Timings: {turf.opening_time.strftime('%I:%M %p')} "
                f"to {turf.closing_time.strftime('%I:%M %p')}\n"
                f"⚽ Facilities: {turf.facilities or 'Not specified'}"
            )

        return "\n\n".join(output)

    # --------------------------------------------------
    # FIND A TURF BY ITS NAME OR LOCATION
    # --------------------------------------------------

    ignored_words = {
        "i", "me", "my", "we", "you", "your", "the", "a", "an",
        "is", "are", "am", "do", "does", "did", "can", "could",
        "would", "will", "please", "tell", "show", "want", "need",
        "like", "to", "for", "of", "in", "at", "on", "about",
        "what", "where", "which", "how", "much", "many", "there",
        "any", "available", "availability", "today", "tomorrow",
        "price", "pricing", "rate", "cost", "booking", "book",
        "booked", "reserve", "reservation", "turf", "turfs",
        "location", "address", "facility", "facilities", "timing",
        "timings", "open", "close", "details", "information",
        "bro", "and", "or", "find", "get", "give", "list", "all",
        "near", "cheap", "cheapest", "budget", "expensive",
        "lowest", "highest", "is", "it", "this", "that", "with",
        "have", "has", "there", "me", "please", "about", "from",
        "at", "per", "hour", "hours", "sports", "sport",
    }

    search_terms = [
        word for word in text.split()
        if word not in ignored_words and len(word) >= 3
    ]

    matching_turfs = Turf.objects.none()

    if search_terms:
        search_query = Q()

        for term in search_terms:
            search_query |= (
                Q(name__icontains=term)
                | Q(location__icontains=term)
            )

        matching_turfs = turfs.filter(search_query).distinct()

    # --------------------------------------------------
    # 1. GREETINGS
    # --------------------------------------------------

    if (
        words.intersection({
            "hi", "hii", "hello", "hey", "hai",
            "heyy", "greetings", "vanakkam"
        })
        and len(words) <= 6
    ) or has_any(
        "good morning", "good afternoon",
        "good evening", "how are you"
    ):
        return (
            "Hello bro! 😊 Welcome to Turf Assistant! 🏟️\n\n"
            "How can I help you today?\n\n"
            "You can ask me about:\n"
            "• Available turfs\n"
            "• Turf prices\n"
            "• Locations and facilities\n"
            "• Opening and closing times\n"
            "• Booking instructions\n\n"
            "Ask your question in your own words!"
        )

    # --------------------------------------------------
    # 2. THANK YOU
    # --------------------------------------------------

    if has_any(
        "thank you", "thanks", "thankyou", "thank u",
        "many thanks", "thanks a lot", "thank you so much",
        "much appreciated"
    ):
        return (
            "You're very welcome, bro! 😊\n"
            "Happy to help. Do you need anything else about turfs or bookings?"
        )

    # --------------------------------------------------
    # 3. OKAY / ACKNOWLEDGEMENT
    # --------------------------------------------------

    if text in {
        "ok", "okay", "okey", "ok bro", "okay bro",
        "alright", "got it", "understood", "i understand",
        "fine", "sure", "great", "cool", "super",
        "seri", "sari", "yes", "yes bro"
    }:
        return (
            "Great! 😊 Is there anything else I can help you with?\n"
            "You can ask about turf availability, prices, locations, "
            "facilities, timings, or bookings."
        )

    # --------------------------------------------------
    # 4. END CONVERSATION
    # --------------------------------------------------

    if text in {
        "bye", "goodbye", "bye bro", "thats all",
        "that is all", "nothing else", "no thanks",
        "no more questions", "i am done", "done",
        "see you", "see you later", "thats it",
        "that is it"
    }:
        return (
            "Thanks for chatting with Turf Assistant! 🏟️😊\n"
            "Have a great day and enjoy your game. See you again!"
        )

    if text in {"no", "no bro", "nothing", "nope", "not now"}:
        return (
            "No problem! 😊 I'm here whenever you need help "
            "with turf bookings. Have a great day!"
        )

    # --------------------------------------------------
    # 5. HELP
    # --------------------------------------------------

    if text == "help" or has_any(
        "what can you do", "what can i ask",
        "how can you help", "help me",
        "need help", "show help", "any help"
    ):
        return (
            "Of course! 😊 I can help you with:\n\n"
            "🏟️ Show available turfs\n"
            "💰 Prices and cheapest turfs\n"
            "📍 Turf locations\n"
            "⚽ Facilities and sports\n"
            "🕒 Opening and closing times\n"
            "📅 Booking instructions\n"
            "❌ Cancellation guidance\n"
            "📋 Booking status guidance\n\n"
            "Ask me anything related to turf booking!"
        )

    # --------------------------------------------------
    # 6. BOOKING QUESTIONS
    # --------------------------------------------------

    booking_words = {
        "book", "booking", "bookings", "reserve",
        "reservation", "reservations", "reserved"
    }

    booking_phrases = (
        "how to book", "how do i book", "how can i book",
        "how to booking", "how to book the turf",
        "i need book", "i need to book", "i want to book",
        "i want book", "want to book", "want book",
        "need to book", "need book", "book a turf",
        "book the turf", "book this turf", "book turf",
        "booking process", "booking procedure",
        "make a booking", "place a booking",
        "i would like to book", "help me book",
        "turf booking", "booking for turf",
        "reserve a turf", "reserve the turf",
        "reserve this turf", "how can i reserve",
        "how do i reserve", "i want reservation",
        "i need a reservation", "i want to reserve",
    )

    if (
        has_any(*booking_phrases)
        or bool(words.intersection(booking_words))
    ):
        return (
            "Sure, bro! 😊 I'll help you book a turf.\n\n"
            "Follow these simple steps:\n"
            "1. Log in to your user account.\n"
            "2. Open the Turfs page.\n"
            "3. Select the turf you want.\n"
            "4. Open its booking page.\n"
            "5. Select your preferred date and time slot.\n"
            "6. Follow the page instructions to submit the booking.\n\n"
            "Please check that your chosen slot is available. "
            "Your booking is confirmed only after you complete the "
            "booking process on the website."
        )

    # --------------------------------------------------
    # 7. BOOKING STATUS
    # --------------------------------------------------

    if has_any(
        "booking status", "my booking", "my bookings",
        "booking confirmed", "check my booking",
        "booking details", "did my booking",
        "is my booking confirmed", "booking history",
        "view my booking"
    ):
        return (
            "To check your booking status, bro 😊:\n\n"
            "1. Log in to your account.\n"
            "2. Open the My Bookings page.\n"
            "3. Find your booking and check its status and details."
        )

    # --------------------------------------------------
    # 8. CANCELLATION
    # --------------------------------------------------

    if has_any(
        "cancel", "cancellation", "cancelled",
        "canceling", "cancel my booking",
        "cancel the booking", "cancel reservation"
    ):
        return (
            "For booking cancellation 😊:\n"
            "1. Log in to your account.\n"
            "2. Open My Bookings.\n"
            "3. Check whether a cancellation option is available.\n\n"
            "Cancellation depends on your website's configured rules. "
            "Contact the vendor if you cannot find a cancellation option."
        )

    # --------------------------------------------------
    # 9. PAYMENT AND REFUND
    # --------------------------------------------------

    if has_any(
        "payment", "pay online", "how to pay",
        "upi", "refund", "money back", "payment failed",
        "paid money", "payment method", "payment methods",
        "online payment", "cash payment"
    ):
        return (
            "For payment help 😊:\n"
            "Please check your booking page for the payment methods "
            "supported by this website. Payment confirmation and refunds "
            "depend on the payment features and policies configured on the site."
        )

    # --------------------------------------------------
    # 10. AVAILABLE TURFS / AVAILABILITY
    # --------------------------------------------------

    if has_any(
        "available", "availability", "free slot",
        "vacant", "open slot", "any slot",
        "can i play", "is there a slot",
        "is the turf open", "is turf open",
        "free today", "available today", "available tomorrow",
        "is it free", "is it available", "which turf is free"
    ):
        if not turfs.exists():
            return (
                "Sorry! No turfs are currently marked as available. "
                "Please check again later."
            )

        return (
            "Here are the turfs currently marked as available! 😊\n\n"
            + turf_details(turfs)
            + "\n\nPlease select your date and time on the booking page "
            "to check actual slot availability. This list does not "
            "guarantee that a particular slot is free."
        )

    # --------------------------------------------------
    # 11. SHOW / LIST TURFS
    # --------------------------------------------------

    if has_any(
        "show turfs", "list turfs", "all turfs",
        "available turfs", "show available",
        "which turfs", "find a turf", "find turf",
        "turf list", "turf options", "what turfs",
        "any turf", "show me turfs", "display turfs",
        "list available turfs", "show all turfs"
    ):
        if not turfs.exists():
            return "There are no turfs currently marked as available. Please check again later."

        return "Here are the available turfs! 🏟️\n\n" + turf_details(turfs)

    # --------------------------------------------------
    # 12. CHEAPEST TURF
    # --------------------------------------------------

    if has_any(
        "cheapest", "cheaper", "lowest price",
        "low price", "budget turf", "cheap turf",
        "less expensive", "affordable turf"
    ):
        if not turfs.exists():
            return "There are no available turfs to compare right now."

        turf = turfs.order_by("price_per_hour").first()

        return (
            f"The lowest-priced available turf is {turf.name}! 💰\n"
            f"Price: ₹{turf.price_per_hour} per hour.\n"
            f"Location: {turf.location}"
        )

    # --------------------------------------------------
    # 13. MOST EXPENSIVE TURF
    # --------------------------------------------------

    if has_any(
        "most expensive", "highest price",
        "costliest", "highest rate", "expensive turf"
    ):
        if not turfs.exists():
            return "There are no available turfs to compare right now."

        turf = turfs.order_by("-price_per_hour").first()

        return (
            f"The highest-priced available turf is {turf.name}.\n"
            f"Price: ₹{turf.price_per_hour} per hour."
        )

    # --------------------------------------------------
    # 14. PRICE QUESTIONS
    # --------------------------------------------------

    if has_any(
        "price", "pricing", "cost", "rate", "charges",
        "how much", "how costly", "how expensive",
        "fee", "fees", "budget", "evlo", "evalo",
        "what is the amount", "price details", "rental price"
    ):
        if not turfs.exists():
            return "Sorry! No available turf prices were found."

        items = matching_turfs if matching_turfs.exists() else turfs

        return (
            "Here are the turf prices! 💰\n\n"
            + "\n".join(
                f"• {t.name}: ₹{t.price_per_hour} per hour"
                for t in items
            )
        )

    # --------------------------------------------------
    # 15. LOCATION QUESTIONS
    # --------------------------------------------------

    if has_any(
        "where", "location", "address", "located",
        "near me", "nearby", "which area",
        "whereabouts", "which place", "enga iruku",
        "where can i find", "turf address"
    ):
        items = matching_turfs if matching_turfs.exists() else turfs

        if not items.exists():
            return "Sorry! No available turf locations were found."

        return (
            "Here are the turf locations! 📍\n\n"
            + "\n".join(
                f"• {t.name}: {t.location}"
                for t in items
            )
        )

    # --------------------------------------------------
    # 16. FACILITIES
    # --------------------------------------------------

    if has_any(
        "facility", "facilities", "amenities",
        "parking", "car park", "bike park",
        "changing room", "washroom", "restroom",
        "toilet", "shower", "drinking water",
        "floodlight", "lights", "seating",
        "locker", "changing facilities"
    ):
        items = matching_turfs if matching_turfs.exists() else turfs

        if not items.exists():
            return "Sorry! No available turf facility details were found."

        return (
            "Here are the facilities listed for each turf! ⚽\n\n"
            + "\n".join(
                f"• {t.name}: {t.facilities or 'Facilities not specified'}"
                for t in items
            )
        )

    # --------------------------------------------------
    # 17. OPENING / CLOSING TIMES
    # --------------------------------------------------

    if has_any(
        "timing", "timings", "opening time",
        "closing time", "open when", "close when",
        "what time", "working hours", "opening hours",
        "closing hours", "when do you open",
        "when does it close", "operating hours",
        "open time", "close time"
    ):
        items = matching_turfs if matching_turfs.exists() else turfs

        if not items.exists():
            return "Sorry! No available turf timings were found."

        return (
            "Here are the turf timings! 🕒\n\n"
            + "\n".join(
                f"• {t.name}: {t.opening_time.strftime('%I:%M %p')} "
                f"to {t.closing_time.strftime('%I:%M %p')}"
                for t in items
            )
        )

    # --------------------------------------------------
    # 18. SPORTS / EQUIPMENT / PLAYERS
    # --------------------------------------------------

    if has_any(
        "sport", "sports", "football", "soccer",
        "cricket", "badminton", "futsal",
        "game", "games", "equipment", "ball",
        "bat", "player", "players", "team size",
        "how many people", "capacity"
    ):
        items = matching_turfs if matching_turfs.exists() else turfs

        if not items.exists():
            return (
                "Sports and equipment depend on the selected turf. "
                "No available turf details were found right now."
            )

        return (
            "Here are the available turf details! 😊\n\n"
            + turf_details(items)
            + "\n\nEquipment and player capacity may not be listed. "
            "Please contact the vendor to confirm those details."
        )

    # --------------------------------------------------
    # 19. WEATHER / HOLIDAYS / OPENING DAYS
    # --------------------------------------------------

    if has_any(
        "weather", "rain", "rainy", "rainfall",
        "holiday", "sunday", "monday", "weekend",
        "opening days", "which days", "public holiday"
    ):
        return (
            "Operating days and weather arrangements may vary by turf. 😊 "
            "Please check the turf details or contact the vendor to confirm "
            "whether the turf is open on your selected day or during rain."
        )

    # --------------------------------------------------
    # 20. ACCOUNT HELP
    # --------------------------------------------------

    if has_any(
        "register", "registration", "sign up",
        "create account", "login", "log in",
        "password", "forgot password", "account"
    ):
        return (
            "For account help 😊:\n\n"
            "• To create an account, open the Register page and enter the required details.\n"
            "• To log in, use your registered credentials.\n"
            "• If you cannot log in, check your details or use the password-reset "
            "option if your website provides one."
        )

    # --------------------------------------------------
    # 21. SEARCH FOR A TURF NAME / LOCATION
    # --------------------------------------------------

    if matching_turfs.exists():
        return (
            "I found these matching turfs! 😊\n\n"
            + turf_details(matching_turfs)
        )

    # --------------------------------------------------
    # 22. FRIENDLY FALLBACK
    # --------------------------------------------------

    return (
        "I'd be happy to help! 😊 I couldn't match your question "
        "to the turf information available in the system.\n\n"
        "Try asking in your own words, for example:\n"
        "• I need to book the turf.\n"
        "• I want to reserve a turf.\n"
        "• How much does the turf cost?\n"
        "• Where is the turf located?\n"
        "• Does the turf have parking?\n"
        "• What time does the turf open?\n"
        "• Show me available turfs.\n\n"
        "Type 'help' to see the topics I can assist with."
    )


# --------------------------------------------------
# DELETE CHAT CONVERSATION
# --------------------------------------------------

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


# --------------------------------------------------
# SEND MESSAGE TO CHATBOT
# --------------------------------------------------

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
        answer = get_turf_answer(question)

        with transaction.atomic():
            if chat_id:
                conversation = get_object_or_404(
                    Conversation.objects.select_for_update(),
                    id=chat_id,
                    user=request.user
                )
            else:
                conversation = Conversation.objects.create(
                    user=request.user,
                    title=question[:60] or "New Chat"
                )

            ChatMessage.objects.create(
                conversation=conversation,
                question=question,
                answer=answer
            )

            conversation.updated_at = timezone.now()
            conversation.save(update_fields=["updated_at"])

        return JsonResponse({
            "success": True,
            "answer": answer,
            "conversation_id": conversation.id,
            "title": conversation.title,
        })

    except Exception:
        logger.exception("Turf chatbot reply failed")

        return JsonResponse({
            "error": "Sorry bro, something went wrong. Please try again."
        }, status=500)


# --------------------------------------------------
# CHATBOT PAGE AND CHAT HISTORY
# --------------------------------------------------

@login_required
def chatbot_page(request):
    conversations = Conversation.objects.filter(
        user=request.user
    ).order_by("-updated_at")

    if request.GET.get("new") == "1":
        active_conversation = None
        messages = []

    else:
        chat_id = request.GET.get("chat_id")

        if chat_id:
            active_conversation = get_object_or_404(
                Conversation,
                id=chat_id,
                user=request.user
            )
        else:
            active_conversation = conversations.first()

        messages = (
            list(active_conversation.messages.all())
            if active_conversation
            else []
        )

    return render(
        request,
        "chatbot/chatbot.html",
        {
            "conversations": conversations,
            "active_conversation": active_conversation,
            "messages": messages,
        }
    )