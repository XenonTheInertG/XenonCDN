import os
import logging
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not TELEGRAM_BOT_TOKEN:
    raise ValueError('TELEGRAM_BOT_TOKEN not found')
if not GEMINI_API_KEY:
    raise ValueError('GEMINI_API_KEY not found')

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = '''You are an expert HSC doubt solver for Bangladesh students. Provide clear, direct solutions.

CRITICAL LANGUAGE RULE:
- If student asks in BANGLA, respond COMPLETELY in BANGLA
- If student asks in ENGLISH, respond COMPLETELY in ENGLISH
- NEVER mix languages
- Use natural, fluent language (not translation-style text)

FORMATTING RULES:
- Use Unicode symbols: ², ³, √, ×, ÷, ±, ≈, ≠, ≤, ≥, π, θ, α, β, γ, Δ, →, ⇌
- Keep formatting clean and readable
- Use line breaks for clarity
- No asterisks or markdown formatting

RESPONSE STRUCTURE (Concise):

For MATH:
প্রদত্ত: [given]
নির্ণেয়: [to find]
সমাধান:
ধাপ ১: [step with explanation]
ধাপ ২: [step with explanation]
উত্তর: [answer]

For PHYSICS:
প্রদত্ত: [values with units]
সূত্র: [formula]
হিসাব: [calculation]
উত্তর: [with unit]

For CHEMISTRY:
বিক্রিয়া: [equation if needed]
সমাধান: [steps]
উত্তর: [answer]

For BIOLOGY:
ব্যাখ্যা: [direct explanation in clear points]
মূল বিষয়: [key takeaways]

ENGLISH RESPONSES (same structure):
Given: [info]
Required: [what to find]
Solution:
Step 1: [step]
Step 2: [step]
Answer: [answer]

CRITICAL RULES:
- Keep responses SHORT and DIRECT
- Show only essential steps
- Use simple, natural language
- No verbose introductions
- No unnecessary explanations
- Focus on solving the problem
- If "Q no X" mentioned, solve ONLY that question
- Pay attention to marked/circled portions in images'''

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = '🎓 HSC Doubt Solver Bot\n\n'
    msg += '✨ Features:\n'
    msg += '✅ Step-by-step solutions\n'
    msg += '✅ Bangla & English support\n'
    msg += '✅ Math formatting (x², √, π)\n'
    msg += '✅ All HSC subjects\n\n'
    msg += '📝 How to use:\n\n'
    msg += 'Text:\n/doubt solve x² + 5x + 6 = 0\n\n'
    msg += 'Image with caption:\n'
    msg += '/doubt solve Q no 5\n'
    msg += '/doubt এটা সমাধান করো\n\n'
    msg += 'Type /help for more!'
    await update.message.reply_text(msg)

async def doubt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    instruction = ''
    
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
            msg = '⚠️ নির্দেশনা দাও / Give instruction!\n\n'
            msg += 'Examples:\n'
            msg += '/doubt solve Q no 5\n'
            msg += '/doubt এটা সমাধান করো'
            await update.message.reply_text(msg)
            return
        
        await process_image_doubt(update, context, instruction)
    
    elif update.message.reply_to_message and update.message.reply_to_message.photo:
        if not instruction:
            await update.message.reply_text('⚠️ নির্দেশনা দাও!\nExample: /doubt solve Q no 3')
            return
        
        await process_image_doubt(update, context, instruction, reply=True)
    
    elif instruction:
        await process_text_doubt(update, instruction)
    
    else:
        msg = '⚠️ Usage:\n\n'
        msg += 'Text: /doubt solve x² - 4 = 0\n\n'
        msg += 'Image: Send photo with caption\n'
        msg += '/doubt solve Q no 5'
        await update.message.reply_text(msg)

async def process_text_doubt(update: Update, question_text: str):
    try:
        await update.message.chat.send_action(action='typing')
        
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        prompt = SYSTEM_PROMPT + '\n\nStudent Question: ' + question_text + '\n\nProvide a direct, concise solution. Use natural language, not machine translation style.'
        response = model.generate_content(prompt)
        
        answer = response.text
        
        # Clean up any asterisks or markdown
        answer = answer.replace('**', '')
        answer = answer.replace('*', '')
        
        if len(answer) > 4000:
            parts = split_message(answer)
            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_text('📚 ' + part)
                else:
                    await update.message.reply_text(part)
        else:
            await update.message.reply_text('📚 ' + answer)
        
    except Exception as e:
        logger.error('Error: ' + str(e))
        await update.message.reply_text('❌ সমস্যা হয়েছে / Error occurred')

async def process_image_doubt(update: Update, context: ContextTypes.DEFAULT_TYPE, instruction: str, reply=False):
    try:
        await update.message.chat.send_action(action='typing')
        
        if reply:
            photo = update.message.reply_to_message.photo[-1]
        else:
            photo = update.message.photo[-1]
        
        photo_file = await context.bot.get_file(photo.file_id)
        photo_bytes = await photo_file.download_as_bytearray()
        
        image = Image.open(io.BytesIO(photo_bytes))
        
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        prompt = SYSTEM_PROMPT + '\n\nStudent instruction: ' + instruction
        prompt += '\n\nAnalyze the image. Focus on marked/circled portions. Provide direct solution with proper formatting. Use natural, fluent language.'
        
        response = model.generate_content([prompt, image])
        
        answer = response.text
        
        # Clean up any asterisks or markdown
        answer = answer.replace('**', '')
        answer = answer.replace('*', '')
        
        if len(answer) > 4000:
            parts = split_message(answer)
            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_text('📚 ' + part)
                else:
                    await update.message.reply_text(part)
        else:
            await update.message.reply_text('📚 ' + answer)
        
    except Exception as e:
        logger.error('Error: ' + str(e))
        await update.message.reply_text('❌ ছবি প্রসেস করতে পারিনি / Could not process image')

def split_message(text, max_length=4000):
    parts = []
    while len(text) > max_length:
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        parts.append(text[:split_pos])
        text = text[split_pos:].strip()
    parts.append(text)
    return parts

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = '🆘 Help - HSC Doubt Solver\n\n'
    msg += '📋 Commands:\n'
    msg += '/start - Start\n'
    msg += '/doubt - Ask question\n'
    msg += '/help - Help\n\n'
    msg += '📝 Usage:\n\n'
    msg += '1. Text question:\n'
    msg += '/doubt solve x² + 5x + 6 = 0\n'
    msg += '/doubt ফটোসিন্থেসিস কি\n\n'
    msg += '2. Image question:\n'
    msg += 'Send photo + caption:\n'
    msg += '/doubt solve Q no 5\n'
    msg += '/doubt এটা সমাধান করো\n\n'
    msg += '📚 Subjects:\n'
    msg += 'Math, Physics, Chemistry, Biology\n\n'
    msg += '💡 Works in groups!\n'
    msg += 'Ask in Bangla or English'
    await update.message.reply_text(msg)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error('Error: ' + str(context.error))

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
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

if __name__ == '__main__':
    main()
