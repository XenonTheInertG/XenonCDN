import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
format=”%(asctime)s - %(name)s - %(levelname)s - %(message)s”,
level=logging.INFO
)
logger = logging.getLogger(**name**)

TELEGRAM_BOT_TOKEN = os.getenv(“TELEGRAM_BOT_TOKEN”)
GEMINI_API_KEY = os.getenv(“GEMINI_API_KEY”)

if not TELEGRAM_BOT_TOKEN:
raise ValueError(“TELEGRAM_BOT_TOKEN not found in environment variables”)
if not GEMINI_API_KEY:
raise ValueError(“GEMINI_API_KEY not found in environment variables”)

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = “”“You are an HSC (Higher Secondary Certificate) doubt solver for Bangladesh students.

RESPONSE RULES:

1. Detect language: Respond in Bangla if question is in Bangla, English if in English
1. Be precise and concise - no unnecessary explanations
1. For math: Show key steps only, not every minor calculation
1. For theory: Give direct answers with main points
1. If image has marked/circled portions, focus on those
1. Reference HSC textbook concepts when relevant
1. Format: Use short paragraphs, bullet points for lists
1. If question specifies Q no X, solve only that question

ANSWER STRUCTURE:

- Direct answer first
- Brief explanation 2-3 lines max
- Key steps if needed
- Done

Keep it SHORT and CLEAR. Students want quick help, not essays.”””

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
welcome_message = “”“HSC Doubt Solver Bot

I will help you solve your HSC questions quickly!

How to use:

Text Question:
/doubt solve x² + 5x + 6 = 0

Image Question:
Send image with caption:
/doubt solve Q no 5
/doubt explain this diagram
/doubt solve all problems

Features:
Works in groups
Supports Bangla and English
Focuses on HSC curriculum
Quick and precise answers

Type /help for more info!”””
await update.message.reply_text(welcome_message)

async def doubt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
instruction = “”

```
if context.args:
    instruction = " ".join(context.args)

if update.message.photo:
    if update.message.caption:
        caption = update.message.caption
        if caption.startswith("/doubt"):
            instruction = caption.replace("/doubt", "").strip()
        else:
            instruction = caption.strip()
    
    if not instruction:
        await update.message.reply_text(
            "Please provide instruction with the image!\n\n"
            "Examples:\n"
            "/doubt solve Q no 5\n"
            "/doubt explain this\n"
            "/doubt solve all"
        )
        return
    
    await process_image_doubt(update, context, instruction)

elif update.message.reply_to_message and update.message.reply_to_message.photo:
    if not instruction:
        await update.message.reply_text(
            "Please provide instruction!\n\n"
            "Example:\n"
            "/doubt solve Q no 3"
        )
        return
    
    await process_image_doubt(update, context, instruction, reply=True)

elif instruction:
    await process_text_doubt(update, instruction)

else:
    await update.message.reply_text(
        "Usage:\n\n"
        "For text questions:\n"
        "/doubt solve x² + 5x + 6 = 0\n\n"
        "For image questions:\n"
        "Send image with caption:\n"
        "/doubt solve Q no 5\n"
        "/doubt explain this"
    )
```

async def process_text_doubt(update: Update, question_text: str):
try:
await update.message.chat.send_action(action=“typing”)

```
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    
    response = model.generate_content([
        SYSTEM_PROMPT,
        "\n\nStudent's Question: " + question_text + "\n\nProvide a precise solution."
    ])
    
    answer = response.text
    
    await update.message.reply_text("Solution:\n\n" + answer)
    
except Exception as e:
    logger.error("Error processing text doubt: " + str(e))
    await update.message.reply_text("Sorry, an error occurred. Please try again.")
```

async def process_image_doubt(update: Update, context: ContextTypes.DEFAULT_TYPE, instruction: str, reply=False):
try:
await update.message.chat.send_action(action=“typing”)

```
    if reply:
        photo = update.message.reply_to_message.photo[-1]
    else:
        photo = update.message.photo[-1]
    
    photo_file = await context.bot.get_file(photo.file_id)
    photo_bytes = await photo_file.download_as_bytearray()
    
    uploaded_file = genai.upload_file_from_bytes(
        file_data=bytes(photo_bytes),
        mime_type="image/jpeg"
    )
    
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    
    prompt = SYSTEM_PROMPT + "\n\nStudent's instruction: " + instruction + "\n\nAnalyze the image and provide a precise solution. Pay attention to any marked or circled portions."
    
    response = model.generate_content([prompt, uploaded_file])
    
    answer = response.text
    
    await update.message.reply_text("Solution:\n\n" + answer)
    
    uploaded_file.delete()
    
except Exception as e:
    logger.error("Error processing image doubt: " + str(e))
    await update.message.reply_text("Sorry, could not process the image. Please try again.")
```

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
help_text = “”“Help - HSC Doubt Solver

Commands:
/start - Start the bot
/doubt - Ask a question
/help - Show this help

How to ask questions:

1. Text Questions:
   /doubt solve x² + 5x + 6 = 0
   /doubt explain photosynthesis
1. Image Questions:
   Send image with caption:
   /doubt solve Q no 5
   /doubt solve this problem
   /doubt explain the diagram
   /doubt solve all questions
1. Reply to Image:
   Reply to any image with:
   /doubt solve Q no 3

Tips:
Be specific like Q no 5 instead of this
Mention if you want all questions solved
Circle or mark specific parts if needed
Ask in Bangla or English - both work!

Subjects Covered:
Math, Physics, Chemistry, Biology, English, Bangla, and more HSC topics!

Works in groups! Just use the commands above.”””
await update.message.reply_text(help_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
logger.error(“Update “ + str(update) + “ caused error “ + str(context.error))

def main():
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

```
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("doubt", doubt_command))

application.add_handler(MessageHandler(
    filters.PHOTO & filters.CAPTION & filters.Regex(r"^/doubt"),
    doubt_command
))

application.add_error_handler(error_handler)

logger.info("Bot started...")
application.run_polling(allowed_updates=Update.ALL_TYPES)
```

if **name** == “**main**”:
main()
