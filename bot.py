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

SYSTEM_PROMPT = '''You are an expert HSC (Higher Secondary Certificate) doubt solver for Bangladesh students. You provide detailed, step-by-step solutions that are easy to understand.

LANGUAGE RULES:
- Detect the language of the question
- Respond in Bangla if the question is in Bangla
- Respond in English if the question is in English
- Keep the same language throughout the entire response

FORMATTING RULES FOR MATH/SCIENCE:
- Use proper mathematical notation with Unicode symbols
- For superscripts: use ², ³, ⁴, ⁿ, ⁺, ⁻
- For subscripts: use ₁, ₂, ₃, ₄
- For fractions: use / or write as "numerator/denominator"
- For square root: use √
- For Greek letters: α, β, γ, δ, θ, λ, π, σ, Ω, etc.
- For arrows: → (yields/gives), ⇌ (equilibrium), ↑, ↓
- For symbols: ≈ (approximately), ≠ (not equal), ≤, ≥, ∞, ∴ (therefore), ∵ (because)
- For multiplication: use × or •
- For division: use ÷ or /

RESPONSE STRUCTURE:

For MATH problems:
1. **Given/তথ্য:** List what is given
2. **Required/নির্ণয়:** State what needs to be found
3. **Solution/সমাধান:** 
   - Show each step clearly
   - Explain WHY you do each step
   - Show all calculations
   - Box or highlight the final answer
4. **Explanation/ব্যাখ্যা:** Explain the concept briefly

For PHYSICS problems:
1. **Given Data/প্রদত্ত:** List all given values with units
2. **To Find/নির্ণেয়:** What to calculate
3. **Formula/সূত্র:** Write the relevant formula(s)
4. **Solution/সমাধান:**
   - Substitute values step by step
   - Show unit conversions if needed
   - Calculate final answer with proper units
5. **Concept/ধারণা:** Explain the physics concept

For CHEMISTRY problems:
1. **Given/প্রদত্ত:** Given information
2. **Required/নির্ণেয়:** What to find
3. **Equation/সমীকরণ:** Write balanced chemical equation if applicable
4. **Solution/সমাধান:**
   - Show mole calculations
   - Show step-by-step working
   - Include units throughout
5. **Explanation/ব্যাখ্যা:** Explain the chemistry concept

For BIOLOGY questions:
1. **Definition/সংজ্ঞা:** Define key terms if needed
2. **Explanation/ব্যাখ্যা:** 
   - Break down complex concepts into simple points
   - Use numbered or bulleted lists
   - Give examples where helpful
3. **Diagram Note/চিত্র নোট:** If diagram is involved, explain parts
4. **Key Points/মূল বিষয়:** Summarize important points

IMPORTANT INSTRUCTIONS:
- If the question specifies "Q no X", solve ONLY that question
- If image has marked/circled portions, focus on those parts
- Make explanations student-friendly and easy to understand
- Use simple language, avoid complex terminology unless necessary
- Show ALL working steps - don't skip any calculation
- Double-check calculations for accuracy
- For multiple questions, solve each one separately with clear numbering

ANSWER LENGTH:
- Be detailed but not overly lengthy
- Focus on clarity and understanding
- Include all necessary steps
- Provide context where needed'''

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = '🎓 HSC Doubt Solver Bot\n\n'
    msg += 'আমি তোমার HSC সমস্যার বিস্তারিত সমাধান দেব!\n'
    msg += 'I will provide detailed solutions to your HSC problems!\n\n'
    msg += '✨ Features:\n'
    msg += '• Step-by-step solutions\n'
    msg += '• Detailed explanations\n'
    msg += '• Proper math/science formatting\n'
    msg += '• Bangla & English support\n'
    msg += '• Works in groups\n\n'
    msg += '📖 How to use:\n\n'
    msg += '1️⃣ Text Question:\n'
    msg += '/doubt solve x² + 5x + 6 = 0\n\n'
    msg += '2️⃣ Image Question:\n'
    msg += 'Send image with caption:\n'
    msg += '/doubt solve Q no 5\n'
    msg += '/doubt explain this diagram\n'
    msg += '/doubt solve all questions\n\n'
    msg += '3️⃣ Subjects: Math, Physics, Chemistry, Biology\n\n'
    msg += 'Type /help for more details!'
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
            msg = '⚠️ Please provide instruction with the image!\n\n'
            msg += 'ছবির সাথে নির্দেশনা দাও!\n\n'
            msg += 'Examples:\n'
            msg += '/doubt solve Q no 5\n'
            msg += '/doubt explain this\n'
            msg += '/doubt solve all questions\n'
            msg += '/doubt গণিত সমাধান করো'
            await update.message.reply_text(msg)
            return
        
        await process_image_doubt(update, context, instruction)
    
    elif update.message.reply_to_message and update.message.reply_to_message.photo:
        if not instruction:
            msg = '⚠️ Please provide instruction!\n\n'
            msg += 'Example: /doubt solve Q no 3'
            await update.message.reply_text(msg)
            return
        
        await process_image_doubt(update, context, instruction, reply=True)
    
    elif instruction:
        await process_text_doubt(update, instruction)
    
    else:
        msg = '⚠️ Usage / ব্যবহার:\n\n'
        msg += '📝 For text questions:\n'
        msg += '/doubt solve x² + 5x + 6 = 0\n'
        msg += '/doubt ফটোসিন্থেসিস ব্যাখ্যা করো\n\n'
        msg += '📸 For image questions:\n'
        msg += 'Send image with caption:\n'
        msg += '/doubt solve Q no 5\n'
        msg += '/doubt এই প্রশ্ন সমাধান করো'
        await update.message.reply_text(msg)

async def process_text_doubt(update: Update, question_text: str):
    try:
        await update.message.chat.send_action(action='typing')
        
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        prompt = SYSTEM_PROMPT + '\n\nStudent Question: ' + question_text + '\n\nProvide a detailed step-by-step solution with proper formatting.'
        response = model.generate_content(prompt)
        
        answer = response.text
        
        # Split long messages if needed
        if len(answer) > 4000:
            parts = split_message(answer)
            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_text('📚 Solution (Part ' + str(i+1) + '):\n\n' + part)
                else:
                    await update.message.reply_text('Part ' + str(i+1) + ':\n\n' + part)
        else:
            await update.message.reply_text('📚 Solution:\n\n' + answer)
        
    except Exception as e:
        logger.error('Error: ' + str(e))
        await update.message.reply_text('❌ Sorry, an error occurred. Please try again.\n\nদুঃখিত, একটি সমস্যা হয়েছে। আবার চেষ্টা করো।')

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
        prompt += '\n\nAnalyze the image carefully. Pay special attention to any marked, circled, or highlighted portions. Provide a detailed step-by-step solution with proper mathematical/scientific formatting.'
        
        response = model.generate_content([prompt, image])
        
        answer = response.text
        
        # Split long messages if needed
        if len(answer) > 4000:
            parts = split_message(answer)
            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_text('📚 Solution (Part ' + str(i+1) + '):\n\n' + part)
                else:
                    await update.message.reply_text('Part ' + str(i+1) + ':\n\n' + part)
        else:
            await update.message.reply_text('📚 Solution:\n\n' + answer)
        
    except Exception as e:
        logger.error('Error: ' + str(e))
        await update.message.reply_text('❌ Sorry, could not process the image. Please try again.\n\nদুঃখিত, ছবি প্রসেস করতে পারিনি। আবার চেষ্টা করো।')

def split_message(text, max_length=4000):
    """Split long messages into smaller parts"""
    parts = []
    while len(text) > max_length:
        # Find last newline before max_length
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        parts.append(text[:split_pos])
        text = text[split_pos:].strip()
    parts.append(text)
    return parts

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = '🆘 Help - HSC Doubt Solver\n'
    msg += 'সাহায্য - HSC সমস্যা সমাধানকারী\n\n'
    msg += '📋 Commands / কমান্ড:\n'
    msg += '/start - Start the bot / বট শুরু করো\n'
    msg += '/doubt - Ask a question / প্রশ্ন করো\n'
    msg += '/help - Show this help / সাহায্য দেখো\n\n'
    msg += '📖 How to ask / কিভাবে জিজ্ঞাসা করবে:\n\n'
    msg += '1️⃣ Text Questions / টেক্সট প্রশ্ন:\n'
    msg += '/doubt solve x² + 5x + 6 = 0\n'
    msg += '/doubt explain photosynthesis\n'
    msg += '/doubt ফটোসিন্থেসিস ব্যাখ্যা করো\n\n'
    msg += '2️⃣ Image Questions / ছবি প্রশ্ন:\n'
    msg += 'Send image with caption:\n'
    msg += '/doubt solve Q no 5\n'
    msg += '/doubt solve all questions\n'
    msg += '/doubt explain the diagram\n'
    msg += '/doubt এই সমস্যা সমাধান করো\n\n'
    msg += '3️⃣ Reply to Image / ছবিতে রিপ্লাই:\n'
    msg += 'Reply to any image with:\n'
    msg += '/doubt solve Q no 3\n\n'
    msg += '✨ Features / বৈশিষ্ট্য:\n'
    msg += '• Step-by-step solutions / ধাপে ধাপে সমাধান\n'
    msg += '• Detailed explanations / বিস্তারিত ব্যাখ্যা\n'
    msg += '• Proper math symbols / সঠিক গণিত চিহ্ন\n'
    msg += '• All HSC subjects / সব HSC বিষয়\n'
    msg += '• Works in groups / গ্রুপে কাজ করে\n\n'
    msg += '📚 Subjects / বিষয়:\n'
    msg += 'Math, Physics, Chemistry, Biology, English, Bangla\n'
    msg += 'গণিত, পদার্থবিজ্ঞান, রসায়ন, জীববিজ্ঞান, ইংরেজি, বাংলা\n\n'
    msg += '💡 Tips / টিপস:\n'
    msg += '• Be specific (Q no 5)\n'
    msg += '• Circle important parts in images\n'
    msg += '• Ask in Bangla or English\n'
    msg += '• Mention if you want all questions solved'
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
