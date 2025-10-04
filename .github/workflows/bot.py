import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from PIL import Image
import io
from dotenv import load_dotenv

# Load environment variables

load_dotenv()

# Configure logging

logging.basicConfig(
format=’%(asctime)s - %(name)s - %(levelname)s - %(message)s’,
level=logging.INFO
)
logger = logging.getLogger(**name**)

# Configuration from environment variables

TELEGRAM_BOT_TOKEN = os.getenv(“TELEGRAM_BOT_TOKEN”)
GEMINI_API_KEY = os.getenv(“GEMINI_API_KEY”)

# Validate environment variables

if not TELEGRAM_BOT_TOKEN:
raise ValueError(“TELEGRAM_BOT_TOKEN not found in environment variables”)
if not GEMINI_API_KEY:
raise ValueError(“GEMINI_API_KEY not found in environment variables”)

# Configure Gemini

genai.configure(api_key=GEMINI_API_KEY)

# System prompt for the bot

SYSTEM_PROMPT = “”“You are an expert HSC (Higher Secondary Certificate) doubt solver assistant for Bangladesh students.

Key Instructions:

1. Respond in the same language the user asks (Bangla or English)
1. Focus on HSC level textbooks and curriculum concepts
1. If the question has marked/highlighted answers or specific parts circled, pay special attention to those
1. Provide clear, step-by-step explanations
1. Reference HSC textbook concepts when relevant
1. For math problems, show detailed working
1. For theory questions, provide comprehensive explanations
1. Be patient and educational in your approach
1. If you see highlighted/marked portions in images, address those specifically

Remember: You’re helping HSC students understand concepts deeply, not just giving answers.”””

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Send a message when the command /start is issued.”””
welcome_message = “””
🎓 **HSC Doubt Solver Bot**

আমি তোমার HSC পড়াশোনায় সাহায্য করব!
I’ll help you with your HSC studies!

**কীভাবে ব্যবহার করবে / How to use:**

1. `/doubt` কমান্ড লিখে তোমার প্রশ্ন লিখো
   Write `/doubt` followed by your question
1. অথবা `/doubt` লিখে ছবি পাঠাও
   Or write `/doubt` and send an image

**উদাহরণ / Examples:**

- `/doubt x² + 5x + 6 = 0 সমাধান করো`
- `/doubt Explain photosynthesis process`
- `/doubt` [then send image of question]

গ্রুপে কাজ করে! Works in groups!
“””
await update.message.reply_text(welcome_message, parse_mode=‘Markdown’)

async def doubt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Handle the /doubt command with text or image”””

```
# Check if there's text after the command
if context.args:
    question_text = ' '.join(context.args)
    await process_text_doubt(update, question_text)

# Check if message has a photo
elif update.message.photo:
    await process_image_doubt(update, context)

# Check if replying to a message with photo
elif update.message.reply_to_message and update.message.reply_to_message.photo:
    await process_image_doubt(update, context, reply=True)

else:
    await update.message.reply_text(
        "প্রশ্ন লিখো বা ছবি পাঠাও!\nPlease write your question or send an image!\n\n"
        "উদাহরণ/Example:\n"
        "`/doubt x² + 5x + 6 = 0 solve koro`\n"
        "Or send `/doubt` with an image",
        parse_mode='Markdown'
    )
```

async def process_text_doubt(update: Update, question_text: str):
“”“Process text-based doubt”””
try:
# Send typing action
await update.message.chat.send_action(action=“typing”)

```
    # Create model
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    # Generate response
    response = model.generate_content([
        SYSTEM_PROMPT,
        f"\n\nStudent's Question: {question_text}"
    ])
    
    answer = response.text
    
    # Send response
    await update.message.reply_text(
        f"📚 **সমাধান / Solution:**\n\n{answer}",
        parse_mode='Markdown'
    )
    
except Exception as e:
    logger.error(f"Error processing text doubt: {e}")
    await update.message.reply_text(
        "দুঃখিত, একটি সমস্যা হয়েছে। আবার চেষ্টা করো।\n"
        "Sorry, an error occurred. Please try again."
    )
```

async def process_image_doubt(update: Update, context: ContextTypes.DEFAULT_TYPE, reply=False):
“”“Process image-based doubt”””
try:
# Send typing action
await update.message.chat.send_action(action=“typing”)

```
    # Get the photo
    if reply:
        photo = update.message.reply_to_message.photo[-1]
    else:
        photo = update.message.photo[-1]
    
    # Download the photo
    photo_file = await context.bot.get_file(photo.file_id)
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Open image
    image = Image.open(io.BytesIO(photo_bytes))
    
    # Create model
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    # Check if there's caption text
    caption = ""
    if reply and update.message.text:
        caption = update.message.text.replace('/doubt', '').strip()
    elif update.message.caption:
        caption = update.message.caption.replace('/doubt', '').strip()
    
    # Generate response
    prompt_parts = [
        SYSTEM_PROMPT,
        "\n\nThe student has sent an image of their question."
    ]
    
    if caption:
        prompt_parts.append(f"\n\nAdditional context from student: {caption}")
    
    prompt_parts.append("\n\nPlease analyze the image carefully, especially any marked, highlighted, or circled portions, and provide a detailed solution.")
    prompt_parts.append(image)
    
    response = model.generate_content(prompt_parts)
    
    answer = response.text
    
    # Send response
    await update.message.reply_text(
        f"📚 **সমাধান / Solution:**\n\n{answer}",
        parse_mode='Markdown'
    )
    
except Exception as e:
    logger.error(f"Error processing image doubt: {e}")
    await update.message.reply_text(
        "দুঃখিত, ছবি প্রসেস করতে সমস্যা হয়েছে। আবার চেষ্টা করো।\n"
        "Sorry, couldn't process the image. Please try again."
    )
```

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Send help message”””
help_text = “””
🆘 **সাহায্য / Help**

**কমান্ড / Commands:**
/start - বট শুরু করো / Start the bot
/doubt - প্রশ্ন জিজ্ঞাসা করো / Ask a question
/help - সাহায্য দেখো / Show this help

**প্রশ্ন করার উপায় / Ways to ask:**

1️⃣ **টেক্সট প্রশ্ন / Text Question:**
`/doubt তোমার প্রশ্ন এখানে লিখো`

2️⃣ **ছবি সহ প্রশ্ন / Question with Image:**

- `/doubt` লিখে ছবি পাঠাও
- ছবির ক্যাপশনে `/doubt` লিখো
- ছবিতে রিপ্লাই করে `/doubt` লিখো

**বিষয় / Subjects:**

- গণিত / Mathematics
- পদার্থবিজ্ঞান / Physics
- রসায়ন / Chemistry
- জীববিজ্ঞান / Biology
- ইংরেজি / English
- বাংলা / Bangla
- এবং আরও / And more!

গ্রুপে ব্যবহার করতে পারবে! Can use in groups!
“””
await update.message.reply_text(help_text, parse_mode=‘Markdown’)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Log errors”””
logger.error(f”Update {update} caused error {context.error}”)

def main():
“”“Start the bot”””
# Create application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

```
# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("doubt", doubt_command))

# Handle photos sent with /doubt command
application.add_handler(MessageHandler(
    filters.PHOTO & filters.CAPTION & filters.Regex(r'^/doubt'),
    doubt_command
))

# Error handler
application.add_error_handler(error_handler)

# Start bot
logger.info("Bot started...")
application.run_polling(allowed_updates=Update.ALL_TYPES)
```

if **name** == ‘**main**’:
main()