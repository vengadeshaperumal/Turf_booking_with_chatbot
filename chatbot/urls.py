from django.urls import path
from . import views

app_name = "chatbot"

urlpatterns = [
    path("", views.chatbot_page, name="chatbot"),
    path("reply/", views.chatbot_reply, name="chatbot_reply"),
    path(
        "delete/<int:chat_id>/",
        views.delete_conversation,
        name="delete_conversation"
    ),
]