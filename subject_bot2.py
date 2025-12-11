import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration and Data Structures ---

# Replace with your actual bot token
BOT_TOKEN = "8187294338:AAGlAoyXcRWEQ51WoR8M8FdvUERBuX6LyQY"

# Subject map: Short Code -> Full Subject Title
SUBJECTS_MAP = {
    "S1": "Vers un système de détection d'intrusion interprétable pour les environnements Edge",
    "S2": "Intelligent framework for telehealth",
    "S3": "Développement d un système intelligent de surveillance et de prédiction du torchage pour la réduction des émissions dans les unités de traitement",
    "S4": "Système de gestion de la chaîne d’approvisionnement avec Blockchain",
    "S5": "Contrôle d’un agent intelligent à l’aide de l’apprentissage par renforcement pour l’optimi-sation des décisions dans un environnement dynamique",
    "S6": "Détection de spam dans les emails",
    "S7": "Ordonnancement dynamique multi-objectif d’ateliers flexibles",
    "S8": "Détection d’Anomalies dans les Réseaux IoT par Apprentissage Machine Quantique Simulé sur Cirq/qsim de Google.",
    "S9": "Interface sécurisée des données médicales",
    "S10": "Patient virtuel dans la plateforme UroHome",
    "S11": "Système de paiement quantique sécurisé.",
    "S12": "Conception et intégration d’un schéma de signature numérique post-quantique (Dilithium/Falcon) dans une blockchain pour la sécurisation des transactions.",
    "S13": "Conception et implémentation d’un système de chiffrement post-quantique hybride basé sur l’algorithme Kyber.",
}
SUBJECT_CODES = list(SUBJECTS_MAP.keys())
SUBJECT_TITLES = list(SUBJECTS_MAP.values())

# Capacity for each subject
SUBJECT_CAPACITY = 1  # Assuming 13 subjects with capacity 1 for 15 students (2 students will be unassigned)

# Student data storage:
# {telegram_user_id: {"rank": int, "preferences": list[str], "assigned_subject": str}}
STUDENT_DATA = {}

# Hardcoded student rankings (using the user's provided IDs)
STUDENT_RANKINGS = {
    5457723492: 1,
    2099937670: 2,
    5501139093: 3,
    5745878439: 4,
    5735612198: 5,
    6809101195: 6,
    5958929528: 7,
    6337456979: 8,
    2141365728: 9,
    7866144404: 10,
    1685920520: 11,
    6269414527: 12,
    5521395263: 13,
    2052467344: 14,
    1781861302: 15,
}

# Initialize STUDENT_DATA with rankings
for user_id, rank in STUDENT_RANKINGS.items():
    STUDENT_DATA[user_id] = {"rank": rank, "preferences": [], "assigned_subject": None}

# --- Core Assignment Logic ---

def run_assignment():
    """
    Assigns subjects to students based on their rank and preferences.
    Highest rank (lowest number) gets priority.
    """
    logger.info("Starting subject assignment process.")

    # 1. Reset current assignments and subject counts
    for data in STUDENT_DATA.values():
        data["assigned_subject"] = None

    subject_counts = {title: 0 for title in SUBJECT_TITLES}

    # 2. Get students sorted by rank (1, 2, 3, ...)
    sorted_students = sorted(
        STUDENT_DATA.items(), key=lambda item: item[1]["rank"]
    )

    # 3. Iterate through students and assign subjects
    for user_id, data in sorted_students:
        preferences = data["preferences"]
        
        # Only process students who have set their preferences
        if not preferences:
            continue

        for preferred_subject_title in preferences:
            if preferred_subject_title in SUBJECT_TITLES:
                # Check if the subject has capacity
                if subject_counts[preferred_subject_title] < SUBJECT_CAPACITY:
                    data["assigned_subject"] = preferred_subject_title
                    subject_counts[preferred_subject_title] += 1
                    logger.info(f"Assigned student {user_id} (Rank {data['rank']}) to {preferred_subject_title}")
                    break  # Move to the next student

    logger.info("Subject assignment complete.")
    logger.info(f"Final subject counts: {subject_counts}")

# --- Helper Functions ---

def get_available_subject_codes(current_preferences_titles):
    """Returns subject codes for subjects that haven't been selected yet."""
    available_codes = []
    for code, title in SUBJECTS_MAP.items():
        if title not in current_preferences_titles:
            available_codes.append(code)
    return available_codes

def create_subject_keyboard(available_codes, current_user_id):
    """
    Creates an inline keyboard with available subjects.
    Adds a visual indicator if a subject is assigned to a higher-ranked student.
    """
    current_user_rank = STUDENT_DATA[current_user_id]["rank"]
    
    # Get current assignments and the rank of the assigned student
    assigned_subjects_by_rank = {}
    for data in STUDENT_DATA.values():
        if data["assigned_subject"]:
            assigned_subjects_by_rank[data["assigned_subject"]] = data["rank"]

    keyboard = []
    for code in available_codes:
        title = SUBJECTS_MAP[code]
        button_text = title
        
        # Check if the subject is assigned
        if title in assigned_subjects_by_rank:
            assigned_rank = assigned_subjects_by_rank[title]
            
            # Check if the assigned student has a higher priority (lower rank number)
            if assigned_rank < current_user_rank:
                # Add indicator for higher priority student
                button_text = f"⚠️ HIGH PRIORITY: {title}"
            elif assigned_rank == current_user_rank:
                # Add indicator for same rank student (optional, for clarity)
                button_text = f"🟡 SAME RANK: {title}"
            # If assigned_rank > current_user_rank, the current user has higher priority, no warning needed.
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_{code}")])
        
    return InlineKeyboardMarkup(keyboard)

# --- Bot Commands and Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and checks if the user is a registered student."""
    user_id = update.effective_user.id
    
    if user_id not in STUDENT_RANKINGS:
        await update.message.reply_text(
            "Welcome! You are not registered as one of the 15 students for subject selection. "
            "Please contact the administrator if you believe this is an error."
        )
        return

    student_data = STUDENT_DATA[user_id]
    rank = student_data["rank"]
    
    message = (
        f"Welcome to the Subject Selection Bot! Your priority rank is **{rank}** (1 is highest priority).\n\n"
        "You need to select and rank your top 5 subjects from the list of 13 available subjects.\n\n"
        "Use the /set_preferences command to begin or modify your choices.\n"
        "Use the /view_assignment command to see your current assigned subject."
    )
    await update.message.reply_text(message)

async def set_preferences_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts the preference selection process with buttons."""
    user_id = update.effective_user.id
    
    if user_id not in STUDENT_RANKINGS:
        await update.message.reply_text("You are not a registered student.")
        return

    # Run assignment before starting selection to get the most up-to-date status
    run_assignment()

    # Initialize the preference selection
    context.user_data["preferences_list"] = [] # Stores full subject titles
    context.user_data["current_preference_step"] = 1
    
    available_codes = get_available_subject_codes([])
    keyboard = create_subject_keyboard(available_codes, user_id)
    
    await update.message.reply_text(
        f"Please select your **1st** preferred subject by tapping on one of the buttons below:\n\n"
        "⚠️ **HIGH PRIORITY** subjects are currently assigned to a student with a better rank than you.",
        reply_markup=keyboard
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button presses for subject selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in STUDENT_RANKINGS:
        await query.edit_message_text("You are not a registered student.")
        return
    
    # Parse the callback data
    if not query.data.startswith("select_"):
        return
    
    selected_code = query.data.replace("select_", "")
    selected_subject_title = SUBJECTS_MAP.get(selected_code)
    
    if not selected_subject_title:
        await query.edit_message_text("Error: Invalid subject selected. Please restart with /set_preferences.")
        return
    
    # Get current preferences
    if "preferences_list" not in context.user_data:
        await query.edit_message_text("Please start again with /set_preferences")
        return
    
    preferences_list = context.user_data["preferences_list"]
    step = context.user_data["current_preference_step"]
    
    # Add the selected subject title
    preferences_list.append(selected_subject_title)
    
    # Check if we need more preferences
    if step < 5:
        context.user_data["current_preference_step"] += 1
        available_codes = get_available_subject_codes(preferences_list)
        
        # Run assignment again to get the most up-to-date status for the next step
        run_assignment()
        
        keyboard = create_subject_keyboard(available_codes, user_id)
        
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(context.user_data["current_preference_step"], "th")
        
        summary = "Your selections so far:\n"
        for i, subj in enumerate(preferences_list, 1):
            summary += f"{i}. {subj}\n"
        summary += f"\nNow, please select your **{context.user_data['current_preference_step']}{suffix}** preferred subject:"
        
        await query.edit_message_text(summary, reply_markup=keyboard)
    else:
        # All 5 preferences collected
        STUDENT_DATA[user_id]["preferences"] = preferences_list
        
        # Run the assignment logic one last time
        run_assignment()
        
        # Notify user
        assigned_subject = STUDENT_DATA[user_id]["assigned_subject"]
        
        message = (
            "✅ Thank you! Your top 5 preferences have been saved:\n"
            f"1. {preferences_list[0]}\n"
            f"2. {preferences_list[1]}\n"
            f"3. {preferences_list[2]}\n"
            f"4. {preferences_list[3]}\n"
            f"5. {preferences_list[4]}\n\n"
            "The system has automatically run the assignment based on all current preferences and your rank.\n"
        )
        
        if assigned_subject:
            message += f"🎯 Your current assigned subject is: **{assigned_subject}**."
        else:
            message += "⚠️ Unfortunately, no subject could be assigned to you with your current preferences."
            
        message += "\n\nYou can run /set_preferences again at any time to modify your choices."
        
        # Clean up user_data
        del context.user_data["preferences_list"]
        del context.user_data["current_preference_step"]
        
        await query.edit_message_text(message)

async def view_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the student's current preferences and assigned subject."""
    user_id = update.effective_user.id
    
    if user_id not in STUDENT_RANKINGS:
        await update.message.reply_text("You are not a registered student.")
        return

    data = STUDENT_DATA[user_id]
    preferences = data["preferences"]
    assigned = data["assigned_subject"]
    
    message = f"📊 Your Rank: **{data['rank']}**\n\n"
    
    if preferences:
        message += "Your current preferences are:\n"
        for i, subject in enumerate(preferences, 1):
            message += f"{i}. {subject}\n"
    else:
        message += "You have not set your preferences yet. Use /set_preferences to begin."
        
    message += "\n"
    
    if assigned:
        message += f"🎯 Your current assigned subject is: **{assigned}**."
    else:
        message += "⚠️ You have not been assigned a subject yet (or no subject could be assigned based on your preferences and rank)."
        
    await update.message.reply_text(message)

async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    (Admin-only command) Displays the current assignment status for all students.
    For simplicity, we'll allow anyone to run this for now, but in a real bot, 
    you would restrict this to a specific admin user ID.
    """
    
    # Run assignment one last time to ensure data is fresh
    run_assignment()
    
    # Get students sorted by rank
    sorted_students = sorted(
        STUDENT_DATA.items(), key=lambda item: item[1]["rank"]
    )
    
    report = "📋 --- Subject Assignment Status ---\n\n"
    
    # Subject Summary
    subject_counts = {title: 0 for title in SUBJECT_TITLES}
    for data in STUDENT_DATA.values():
        if data["assigned_subject"]:
            subject_counts[data["assigned_subject"]] += 1
            
    report += "Subject Capacity Summary:\n"
    for subject, count in subject_counts.items():
        report += f"- {subject}: {count}/{SUBJECT_CAPACITY} assigned\n"
        
    report += "\n--- Student Details (Sorted by Rank) ---\n"
    
    for user_id, data in sorted_students:
        rank = data["rank"]
        assigned = data["assigned_subject"] if data["assigned_subject"] else "UNASSIGNED"
        preferences = "\n".join([f"{i}. {p}" for i, p in enumerate(data["preferences"], 1)]) if data["preferences"] else "Not Set"
        
        report += (
            f"Rank {rank} (ID: {user_id}):\n"
            f"  Assigned: {assigned}\n"
            f"  Preferences:\n{preferences}\n"
            "----------------------------------\n"
        )
        
    await update.message.reply_text(report)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_preferences", set_preferences_start))
    application.add_handler(CommandHandler("view_assignment", view_assignment))
    application.add_handler(CommandHandler("admin_status", admin_status))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Run the bot until the user presses Ctrl-C
    print("Bot is running. Press Ctrl-C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Initial assignment run (optional, but good for initialization)
    run_assignment()
    main()
