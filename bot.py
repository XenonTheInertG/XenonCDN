import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
format=’%(asctime)s - %(name)s - %(levelname)s - %(message)s’,
level=logging.INFO
)
logger = logging.getLogger(**name**)

TELEGRAM_BOT_TOKEN = os.getenv(‘TELEGRAM_BOT_TOKEN’)
GEMINI_API_KEY = os.getenv(‘GEMINI_API_KEY’)

if not TELEGRAM_BOT_TOKEN:
raise ValueError(‘TELEGRAM_BOT_TOKEN not found’)
if not GEMINI_API_KEY:
raise ValueError(‘GEMINI_API_KEY not found’)

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = ‘’’You are an HSC doubt solver for Bangladesh students.

RESPONSE RULES:

1. Detect language: Respond in Bangla if question is in Bangla, English if in English
1. Be precise and concise
1. For math: Show key steps only
1. For theory: Give direct answers with main points
1. If image has marked portions, focus on those
1. Reference HSC textbook concepts when relevant
1. If question specifies Q no X, solve only that question

ANSWER STRUCTURE:

- Direct answer first
- Brief explanation 2-3 lines max
- Key steps if needed

Keep it SHORT and CLEAR.’’’

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
msg = ‘HSC Doubt Solver Bot\n\n’
msg += ‘I will help you solve your HSC questions quickly!\n\n’
msg += ‘How to use:\n\n’
msg += ‘Text Question:\n’
msg += ‘/doubt solve x² + 5x + 6 = 0\n\n’
msg += ‘Image Question:\n’
msg += ‘Send image with caption:\n’
msg += ‘/doubt solve Q no 5\n’
msg += ‘/doubt explain this diagram\n\n’
msg += ‘Type /help for more info!’
await update.message.reply_text(msg)

async def doubt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
instruction = ‘’

```
if context.args:
    instruction = ' '.join(context.args)

if update.message.photo:
    if update.message.caption:
        caption = update.message.caption
        if caption.startswith('/doubt'):
            instruction = caption.replace('/doubt', '').strip()
        else:
            instruction = caption.strip()
    
    if not instruction:
        msg = 'Please provide instruction with the image!\n\n'
        msg += 'Examples:\n'
        msg += '/doubt solve Q no 5\n'
        msg += '/doubt explain this'
        await update.message.reply_text(msg)
        return
    
    await process_image_doubt(update, context, instruction)

elif update.message.reply_to_message and update.message.reply_to_message.photo:
    if not instruction:
        await update.message.reply_text('Please provide instruction!\n\nExample:\n/doubt solve Q no 3')
        return
    
    await process_image_doubt(update, context, instruction, reply=True)

elif instruction:
    await process_text_doubt(update, instruction)

else:
    msg = 'Usage:\n\n'
    msg += 'For text questions:\n'
    msg += '/doubt solve x² + 5x + 6 = 0\n\n'
    msg += 'For image questions:\n'
    msg += 'Send image with caption:\n'
    msg += '/doubt solve Q no 5'
    await update.message.reply_text(msg)
```

async def process_text_doubt(update: Update, question_text: str):
try:
await update.message.chat.send_action(action=‘typing’)

```
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    prompt = SYSTEM_PROMPT + '\n\nStudent Question: ' + question_text + '\n\nProvide a precise solution.'
    response = model.generate_content(prompt)
    
    answer = response.text
    await update.message.reply_text('Solution:\n\n' + answer)
    
except Exception as e:
    logger.error('Error: ' + str(e))
    await update.message.reply_text('Sorry, an error occurred. Please try again.')
```

async def process_image_doubt(update: Update, context: ContextTypes.DEFAULT_TYPE, instruction: str, reply=False):
try:
await update.message.chat.send_action(action=‘typing’)

```
    if reply:
        photo = update.message.reply_to_message.photo[-1]
    else:
        photo = update.message.photo[-1]
    
    photo_file = await context.bot.get_file(photo.file_id)
    photo_bytes = await photo_file.download_as_bytearray()
    
    uploaded_file = genai.upload_file_from_bytes(
        file_data=bytes(photo_bytes),
        mime_type='image/jpeg'
    )
    
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    prompt = SYSTEM_PROMPT + '\n\nStudent instruction: ' + instruction
    prompt += '\n\nAnalyze the image and provide a precise solution. Pay attention to any marked or circled portions.'
    
    response = model.generate_content([prompt, uploaded_file])
    
    answer = response.text
    await update.message.reply_text('Solution:\n\n' + answer)
    
    uploaded_file.delete()
    
except Exception as e:
    logger.error('Error: ' + str(e))
    await update.message.reply_text('Sorry, could not process the image. Please try again.')
```

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
msg = ‘Help - HSC Doubt Solver\n\n’
msg += ‘Commands:\n’
msg += ‘/start - Start the bot\n’
msg += ‘/doubt - Ask a question\n’
msg += ‘/help - Show this help\n\n’
msg += ‘How to ask questions:\n\n’
msg += ‘1. Text Questions:\n’
msg += ‘/doubt solve x² + 5x + 6 = 0\n\n’
msg += ‘2. Image Questions:\n’
msg += ‘Send image with caption:\n’
msg += ‘/doubt solve Q no 5\n’
msg += ‘/doubt explain the diagram\n\n’
msg += ‘3. Reply to Image:\n’
msg += ‘Reply to any image with:\n’
msg += ‘/doubt solve Q no 3\n\n’
msg += ‘Works in groups!’
await update.message.reply_text(msg)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
logger.error(’Update caused error: ’ + str(context.error))

def main():
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

```
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('help', help_command))
application.add_handler(CommandHandler('doubt', doubt_command))

application.add_handler(MessageHandler(
    filters.PHOTO & filters.CAPTION & filters.Regex(r'^/doubt'),
    doubt_command
))

application.add_error_handler(error_handler)

logger.info('Bot started...')
application.run_polling(allowed_updates=Update.ALL_TYPES)
```

if **name** == ‘**main**’:
main()
