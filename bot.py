import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
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

SYSTEM_PROMPT = “”“You are an HSC (Higher Secondary Certificate) doubt solver for Bangladesh students.

RESPONSE RULES:

1. Detect language: Respond in Bangla if question is in Bangla, English if in English
1. Be precise and concise - no unnecessary explanations
1. For math: Show key steps only, not every minor calculation
1. For theory: Give direct answers with main points
1. If image has marked/circled portions, focus on those
1. Reference HSC textbook concepts when relevant
1. Format: Use short paragraphs, bullet points for lists
1. If question specifies “Q no X”, solve only that question

ANSWER STRUCTURE:

- Direct answer first
- Brief explanation (2-3 lines max)
- Key steps if needed
- Done

Keep it SHORT and CLEAR. Students want quick help, not essays.”””

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Send a message when the command /start is issued.”””
welcome_message = “””
🎓 **HSC Doubt Solver Bot**

I’ll help you solve your HSC questions quickly!

**How to use:**

📝 **Text Question:**
`/doubt solve x² + 5x + 6 = 0`

📸 **Image Question:**
Send image with caption:
`/doubt solve Q no 5`
`/doubt explain this diagram`
`/doubt solve all problems`

**Features:**
✅ Works in groups
✅ Supports Bangla & English
✅ Focuses on HSC curriculum
✅ Quick and precise answers

Type /help for more info!
“””
await update.message.reply_text(welcome_message, parse_mode=‘Markdown’)

async def doubt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Handle the /doubt command with text or image”””

```
# Get instruction from command arguments or caption
instruction = ""

if context.args:
    instruction = ' '.join(context.args)

# Check if message has a photo with caption
if update.message.photo:
    if update.message.caption:
        # Extract instruction from caption
        caption = update.message.caption
        if caption.startswith('/doubt'):
            instruction = caption.replace('/doubt', '').strip()
        else:
            instruction = caption.strip()
    
    if not instruction:
        await update.message.reply_text(
            "⚠️ Please provide instruction with the image!\n\n"
            "**Examples:**\n"
            "`/doubt solve Q no 5`\n"
            "`/doubt explain this`\n"
            "`/doubt solve all`"
        )
        return
    
    await process_image_doubt(update, context, instruction)

# Check if replying to a message with photo
elif update.message.reply_to_message and update.message.reply_to_message.photo:
    if not instruction:
        await update.message.reply_text(
            "⚠️ Please provide instruction!\n\n"
            "**Example:**\n"
            "`/doubt solve Q no 3`"
        )
        return
    
    await process_image_doubt(update, context, instruction, reply=True)

# Text-only question
elif instruction:
    await process_text_doubt(update, instruction)

else:
    await update.message.reply_text(
        "⚠️ **Usage:**\n\n"
        "**For text questions:**\n"
        "`/doubt solve x² + 5x + 6 = 0`\n\n"
        "**For image questions:**\n"
        "Send image with caption:\n"
        "`/doubt solve Q no 5`\n"
        "`/doubt explain this`"
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
        f"\n\nStudent's Question: {question_text}\n\nProvide a precise solution."
    ])
    
    answer = response.text
    
    # Send response
    await update.message.reply_text(
        f"📚 **Solution:**\n\n{answer}",
        parse_mode='Markdown'
    )
    
except Exception as e:
    logger.error(f"Error processing text doubt: {e}")
    await update.message.reply_text(
        "❌ Sorry, an error occurred. Please try again."
    )
```

async def process_image_doubt(update: Update, context: ContextTypes.DEFAULT_TYPE, instruction: str, reply=False):
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
    
    # Upload to Gemini
    uploaded_file = genai.upload_file_from_bytes(
        file_data=bytes(photo_bytes),
        mime_type="image/jpeg"
    )
    
    # Create model
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    # Generate response with image
    prompt = f"{SYSTEM_PROMPT}\n\nStudent's instruction: {instruction}\n\nAnalyze the image and provide a precise solution. Pay attention to any marked or circled portions."
    
    response = model.generate_content([prompt, uploaded_file])
    
    answer = response.text
    
    # Send response
    await update.message.reply_text(
        f"📚 **Solution:**\n\n{answer}",
        parse_mode='Markdown'
    )
    
    # Clean up uploaded file
    uploaded_file.delete()
    
except Exception as e:
    logger.error(f"Error processing image doubt: {e}")
    await update.message.reply_text(
        "❌ Sorry, couldn't process the image. Please try again."
    )
```

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
“”“Send help message”””
help_text = “””
🆘 **Help - HSC Doubt Solver**

**Commands:**
/start - Start the bot
/doubt - Ask a question
/help - Show this help

**How to ask questions:**

**1. Text Questions:**
`/doubt solve x² + 5x + 6 = 0`
`/doubt explain photosynthesis`

**2. Image Questions:**
Send image with caption:
`/doubt solve Q no 5`
`/doubt solve this problem`
`/doubt explain the diagram`
`/doubt solve all questions`

**3. Reply to Image:**
Reply to any image with:
`/doubt solve Q no 3`

**Tips:**
• Be specific (e.g., “Q no 5” instead of “this”)
• Mention if you want all questions solved
• Circle or mark specific parts if needed
• Ask in Bangla or English - both work!

**Subjects Covered:**
Math, Physics, Chemistry, Biology, English, Bangla, and more HSC topics!

**Works in groups!** Just use the commands above.
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
