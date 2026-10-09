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
    text = question.lower().strip()
    text = re.sub(r"\s+", " ", text)

    # Friendly conversation
    greetings = [
        "hi", "hello", "hey", "hey bro",
        "hai", "good morning", "good evening"
    ]

    if text in greetings or text in {"hi bro", "hello bro"}:
        return (
            "Hey bro! 👋 Welcome to Turf Assistant. "
            "I can help you find turfs, compare hourly prices, "
            "check facilities, and understand how to book. "
            "What are you looking for today?"
        )

    if any(word in text for word in [
        "who are you", "your name", "what can you do",
        "help me", "help"
    ]):
        return (
            "I'm Turf Assistant ⚽. I can help you explore turf "
            "locations, hourly prices, facilities, availability, "
            "and booking steps. Ask me anything related to turf booking!"
        )

    if any(word in text for word in [
        "thank you", "thanks", "thanku", "thanks bro"
    ]):
        return "You're welcome bro! 😊 Need help finding a turf?"

    if any(word in text for word in [
        "how are you", "how r u"
    ]):
        return (
            "I'm doing great, bro! 😄 Ready to help you find a turf. "
            "Which location are you looking for?"
        )

    # Fetch real turf information from the database
    turfs = Turf.objects.filter(is_available=True)

    if not turfs.exists():
        return (
            "Bro, there are no available turfs listed right now. "
            "Please check again later."
        )

    if any(word in text for word in [
        "show turfs", "list turfs", "available turfs",
        "turf list", "find turf"
    ]):
        lines = ["Here are the currently listed available turfs, bro:"]
        for turf in turfs[:10]:
            lines.append(
                f"• {turf.name} — {turf.location} — "
                f"₹{turf.price_per_hour}/hour"
            )
        return "\n".join(lines)

    if any(word in text for word in [
        "price", "cost", "rate", "rent", "how much"
    ]):
        lines = ["Here are the turf hourly prices, bro:"]
        for turf in turfs[:10]:
            lines.append(
                f"• {turf.name}: ₹{turf.price_per_hour}/hour "
                f"({turf.location})"
            )
        return "\n".join(lines)

    if any(word in text for word in [
        "location", "where", "address", "place", "near"
    ]):
        lines = ["Here are the available turf locations:"]
        for turf in turfs[:10]:
            lines.append(f"• {turf.name}: {turf.location}")
        return "\n".join(lines)

    if any(word in text for word in [
        "facility", "facilities", "amenities", "parking",
        "changing room", "lights"
    ]):
        lines = ["Here are the listed turf facilities:"]
        for turf in turfs[:10]:
            facilities = turf.facilities.strip() or "Not specified"
            lines.append(f"• {turf.name}: {facilities}")
        return "\n".join(lines)

    if "booking" in text or "book a turf" in text or "reserve" in text:
        return (
            "Sure bro! ⚽ Open the available turfs page, choose a turf, "
            "check its price and timings, select your booking date and "
            "time slot, and submit the booking. Log in first if required. "
            "Only a confirmed booking is final."
        )

    if any(word in text for word in [
        "time", "timing", "opening", "closing", "hours"
    ]):
        lines = ["Here are the listed turf timings:"]
        for turf in turfs[:10]:
            lines.append(
                f"• {turf.name}: {turf.opening_time.strftime('%I:%M %p')} "
                f"to {turf.closing_time.strftime('%I:%M %p')}"
            )
        return "\n".join(lines)

    return (
        "I can help with turf-related questions, bro! 😊 "
        "Try asking: 'Show available turfs', 'What is the price?', "
        "'Where is the turf?', 'What facilities are available?', "
        "or 'How do I book a turf?'"
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


