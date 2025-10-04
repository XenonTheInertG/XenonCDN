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

SYSTEM_PROMPT = '''You are an expert HSC doubt solver for Bangladesh students. Provide clear, step-by-step solutions.

CRITICAL LANGUAGE RULE:
- If the student asks in BANGLA, respond COMPLETELY in BANGLA
- If the student asks in ENGLISH, respond COMPLETELY in ENGLISH
- NEVER mix languages in a single response

FORMATTING RULES:
Use these Unicode symbols for better readability:
• Superscripts: ², ³, ⁴, ⁿ, ⁺, ⁻
• Subscripts: ₁, ₂, ₃, ₄
• Math symbols: √, ×, ÷, ±, ≈, ≠, ≤, ≥, ∞
• Greek letters: α, β, γ, θ, λ, π, σ, Δ, Ω
• Arrows: → (reaction/result), ⇌ (equilibrium)
• Special: ∴ (therefore), ∵ (because)

RESPONSE STRUCTURE (Keep it concise but complete):

For MATH (গণিত):
• প্রদত্ত/Given: [list given info]
• নির্ণেয়/To Find: [what to find]
• সমাধান/Solution:
  Step 1: [explain step]
  Step 2: [explain step]
  ...
• উত্তর/Answer: [final answer in box]

For PHYSICS (পদার্থবিজ্ঞান):
• প্রদত্ত/Given: [values with units]
• সূত্র/Formula: [formula]
• সমাধান/Solution: [step by step with calculations]
• উত্তর/Answer: [with unit]

For CHEMISTRY (রসায়ন):
• বিক্রিয়া/Reaction: [balanced equation if needed]
• সমাধান/Solution: [step by step]
• উত্তর/Answer: [final answer]

For BIOLOGY (জীববিজ্ঞান):
• সংজ্ঞা/Definition: [if needed]
• ব্যাখ্যা/Explanation: [clear points]
• মূল বিষয়/Key Points: [summary]

IMPORTANT:
- Keep solutions concise but complete
- Show key steps only, not every minor calculation
- Use proper formatting with symbols
- If image has marked portions, focus on those
- If "Q no X" is mentioned, solve only that question
- Make it student-friendly and easy to understand'''

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = '🎓 HSC Doubt Solver Bot\n\n'
    msg += '✨ Features:\n'
    msg += '✅ Step-by-step solutions\n'
    msg += '✅ Bangla & English support\n'
    msg += '✅ Proper math formatting\n'
    msg += '✅ All HSC subjects\n\n'
    msg += '📝 Usage:\n\n'
    msg += 'Text: /doubt solve x² + 5x + 6 = 0\n\n'
    msg += 'Image: Send photo with caption\n'
    msg += '/doubt solve Q no 5\n'
    msg += '/doubt এই প্রশ্ন সমাধান করো\n\n'
    msg += 'Type /help for details!'
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
            msg = '⚠️ Please provide instruction!\n\n'
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
        msg += 'Text: /doubt solve x² + 5x + 6 = 0\n\n'
        msg += 'Image: /doubt solve Q no 5'
        await update.message.reply_text(msg)

async def process_text_doubt(update: Update, question_text: str):
    try:
        await update.message.chat.send_action(action='typing')
        
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        prompt = SYSTEM_PROMPT + '\n\nStudent Question: ' + question_text
        response = model.generate_content(prompt)
        
        answer = response.text
        
        if len(answer) > 4000:
            parts = split_message(answer)
            for i, part in enumerate(parts):
                header = '📚 সমাধান ' if 'া' in question_text or 'ো' in question_text else '📚 Solution '
                if i == 0:
                    await update.message.reply_text(header + '(Part ' + str(i+1) + '):\n\n' + part)
                else:
                    await update.message.reply_text('Part ' + str(i+1) + ':\n\n' + part)
        else:
            header = '📚 সমাধান:\n\n' if 'া' in question_text or 'ো' in question_text else '📚 Solution:\n\n'
            await update.message.reply_text(header + answer)
        
    except Exception as e:
        logger.error('Error: ' + str(e))
        await update.message.reply_text('❌ Error occurred. Try again.\nসমস্যা হয়েছে। আবার চেষ্টা করো।')

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
        prompt += '\n\nAnalyze the image. Focus on marked/circled portions. Provide step-by-step solution.'
        
        response = model.generate_content([prompt, image])
        
        answer = response.text
        
        if len(answer) > 4000:
            parts = split_message(answer)
            for i, part in enumerate(parts):
                header = '📚 সমাধান ' if 'া' in instruction or 'ো' in instruction else '📚 Solution '
                if i == 0:
                    await update.message.reply_text(header + '(Part ' + str(i+1) + '):\n\n' + part)
                else:
                    await update.message.reply_text('Part ' + str(i+1) + ':\n\n' + part)
        else:
            header = '📚 সমাধান:\n\n' if 'া' in instruction or 'ো' in instruction else '📚 Solution:\n\n'
            await update.message.reply_text(header + answer)
        
    except Exception as e:
        logger.error('Error: ' + str(e))
        await update.message.reply_text('❌ Could not process image.\nছবি প্রসেস করতে পারিনি।')

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
    msg = '🆘 Help\n\n'
    msg += '📋 Commands:\n'
    msg += '/start - Start bot\n'
    msg += '/doubt - Ask question\n'
    msg += '/help - Show help\n\n'
    msg += '📝 Text Questions:\n'
    msg += '/doubt solve x² + 5x + 6 = 0\n'
    msg += '/doubt ফটোসিন্থেসিস ব্যাখ্যা করো\n\n'
    msg += '📸 Image Questions:\n'
    msg += 'Send photo with caption:\n'
    msg += '/doubt solve Q no 5\n'
    msg += '/doubt এই প্রশ্ন সমাধান করো\n\n'
    msg += '📚 Subjects:\n'
    msg += 'Math, Physics, Chemistry, Biology\n'
    msg += 'গণিত, পদার্থ, রসায়ন, জীববিজ্ঞান\n\n'
    msg += '💡 Ask in Bangla or English!'
    await update.message.reply_text(msg)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error('Update caused error: ' + str(context.error))

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
