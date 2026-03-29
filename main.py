import json
import sqlite3
import os
import sys
import random
import getpass
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import termios
import tty

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'data.db')
QUESTIONS_FILE = os.path.join(BASE_DIR, 'questions.json')

ph = PasswordHasher()

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            return 'esc'
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_input_with_esc(prompt=""):
    print(prompt, end='', flush=True)
    chars = []
    while True:
        ch = getch()
        if ch == 'esc':
            return 'esc'
        elif ch in ('\r', '\n'):
            print()
            return ''.join(chars)
        elif ch == '\x7f' or ch == '\b':  # Backspace
            if chars:
                chars.pop()
                print('\b \b', end='', flush=True)
        elif len(ch) == 1 and ch.isprintable():
            chars.append(ch)
            print(ch, end='', flush=True)

def get_password_with_esc(prompt=""):
    print(prompt, end='', flush=True)
    chars = []
    while True:
        ch = getch()
        if ch == 'esc':
            return 'esc'
        elif ch in ('\r', '\n'):
            print()
            return ''.join(chars)
        elif ch == '\x7f' or ch == '\b':  # Backspace
            if chars:
                chars.pop()
                print('\b \b', end='', flush=True)
        elif len(ch) == 1 and ch.isprintable():
            chars.append(ch)
            print('*', end='', flush=True)

def print_header():
    print("=" * 50)
    print(" " * 15 + "PYTHON QUIZZER")
    print("=" * 50)
    print()

def print_menu():
    clear_screen()
    print_header()
    print("MENU")
    print("=" * 20)
    print("How to answer questions:")
    print(" - Multiple Choice: Press 1-9 to select an option")
    print(" - True/False: Press 1 for True, 2 for False")
    print(" - Short Answer: Type your answer and press Enter")
    print("\nFeedback after questions:")
    print(" - Press 1 if the question was good")
    print(" - Press 2 if you disliked the topic")
    print(" - Press 3 if you disliked the type")
    print(" - Press 4 if you disliked both")
    print("\nPress any key to return...")
    getch()

def check_files():
    missing_db = not os.path.exists(DB_FILE)
    missing_q = not os.path.exists(QUESTIONS_FILE)
    
    if missing_db or missing_q:
        clear_screen()
        print_header()
        print("INFO: Missing files detected.")
        if missing_db:
            print(f" - Database file '{DB_FILE}' is missing. A new one will be created.")
        if missing_q:
            print(f" - Questions file '{QUESTIONS_FILE}' is missing.")
        
        print("\nPress Enter to continue...")
        input()
        
        if missing_q:
            sys.exit(1)

def get_db_connection():
    return sqlite3.connect(DB_FILE)

def load_questions():
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('questions', [])
    except (json.JSONDecodeError, IOError):
        clear_screen()
        print_header()
        print("ERROR: Invalid questions file format.")
        sys.exit(1)

def login(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, score INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS disliked_topics (username TEXT, topic TEXT, PRIMARY KEY(username, topic))")
    cursor.execute("CREATE TABLE IF NOT EXISTS disliked_types (username TEXT, q_type TEXT, PRIMARY KEY(username, q_type))")
    conn.commit()

    while True:
        clear_screen()
        print_header()
        print("LOGIN / REGISTER\n")
        print("(Press ESC at any time to open menu)\n")
        
        username = get_input_with_esc("Username: ").strip()
        if username == 'esc':
            print_menu()
            continue
        if not username:
            continue
            
        password = get_password_with_esc("Password: ")
        if password == 'esc':
            print_menu()
            continue
        
        cursor.execute("SELECT password_hash, score FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if result:
            password_hash, score = result
            try:
                if ph.verify(password_hash, password):
                    print(f"\nWelcome back, {username}! Current score: {score}")
                    input("Press Enter to continue...")
                    return username, score
            except VerifyMismatchError:
                print("\nIncorrect password.")
                print("1. Try again")
                print("2. Create new account")
                choice = get_input_with_esc("Choice: ").strip()
                if choice == 'esc':
                    print_menu()
                continue
        else:
            print("\nUser not found. Creating new account...")
            
            hashed_password = ph.hash(password)
            cursor.execute("INSERT OR REPLACE INTO users (username, password_hash, score) VALUES (?, ?, 0)", 
                          (username, hashed_password))
            conn.commit()
            print(f"\nAccount created for {username}!")
            input("Press Enter to continue...")
            return username, 0

def play_quiz(conn, username, current_score, questions):
    cursor = conn.cursor()
    score = current_score
    if score > 0:
        streak = int(round((score - 1) ** 0.5))
    else:
        streak = 0
    
    cursor.execute("SELECT topic FROM disliked_topics WHERE username = ?", (username,))
    disliked_topics = set(row[0] for row in cursor.fetchall())
    
    cursor.execute("SELECT q_type FROM disliked_types WHERE username = ?", (username,))
    disliked_types = set(row[0] for row in cursor.fetchall())
    
    while True:
        clear_screen()
        print_header()
        
        available_questions = [
            q for q in questions 
            if q.get('category', 'General') not in disliked_topics 
            and q.get('type') not in disliked_types
        ]
        
        if not available_questions:
            if not questions:
                print("\nThere are no questions available in the question bank. Exiting...")
                sys.exit(1)
            print("\nYou have disliked all available questions! Resetting preferences so you can keep playing.")
            disliked_topics.clear()
            disliked_types.clear()
            cursor.execute("DELETE FROM disliked_topics WHERE username = ?", (username,))
            cursor.execute("DELETE FROM disliked_types WHERE username = ?", (username,))
            conn.commit()
            available_questions = questions
            input("Press Enter to continue...")
            continue
            
        q = random.choice(available_questions)
        q_type = q.get('type')
        q_text = q.get('question')
        topic = q.get('category', 'General')
        
        print(f"Category: {topic}")
        print(f"User: {username} | Score: {score} | Streak: {streak}")
        print("-" * 50)
        print(f"\nQuestion: {q_text}\n")
        
        user_answer = None
        is_correct = False
        
        if q_type == 'multiple_choice':
            options = q.get('options', [])
            for i, opt in enumerate(options, 1):
                print(f"{i}. {opt}")
            
            print("\nPress 1-9 to select (or ESC for menu):")
            while True:
                ch = getch()
                if ch == 'esc':
                    print_menu()
                    clear_screen()
                    print_header()
                    print(f"Category: {topic}")
                    print(f"User: {username} | Score: {score} | Streak: {streak}")
                    print("-" * 50)
                    print(f"\nQuestion: {q_text}\n")
                    for i, opt in enumerate(options, 1):
                        print(f"{i}. {opt}")
                    print("\nPress 1-9 to select (or ESC for menu):")
                elif ch.isdigit() and 1 <= int(ch) <= len(options):
                    idx = int(ch) - 1
                    user_answer = options[idx]
                    is_correct = (user_answer == q.get('answer'))
                    break
                else:
                    print(f"\rInvalid input. Press 1-{len(options)} or ESC.       ", end='', flush=True)
            
            if user_answer is None:
                continue
            
        elif q_type == 'true_false':
            print("1. True")
            print("2. False")
            
            print("\nPress 1 or 2 (or ESC for menu):")
            while True:
                ch = getch()
                if ch == 'esc':
                    print_menu()
                    clear_screen()
                    print_header()
                    print(f"Category: {topic}")
                    print(f"User: {username} | Score: {score} | Streak: {streak}")
                    print("-" * 50)
                    print(f"\nQuestion: {q_text}\n")
                    print("1. True")
                    print("2. False")
                    print("\nPress 1 or 2 (or ESC for menu):")
                elif ch == '1':
                    user_answer = 'true'
                    is_correct = (user_answer.lower() == str(q.get('answer')).lower())
                    break
                elif ch == '2':
                    user_answer = 'false'
                    is_correct = (user_answer.lower() == str(q.get('answer')).lower())
                    break
                else:
                    print(f"\rInvalid input. Press 1, 2, or ESC.       ", end='', flush=True)
            
            if user_answer is None:
                continue
            
        elif q_type == 'short_answer':
            print("Type your answer and press Enter (or press ESC for menu):")
            while True:
                ans = get_input_with_esc("> ").strip()
                if ans == 'esc':
                    print_menu()
                    clear_screen()
                    print_header()
                    print(f"Category: {topic}")
                    print(f"User: {username} | Score: {score} | Streak: {streak}")
                    print("-" * 50)
                    print(f"\nQuestion: {q_text}\n")
                    print("Type your answer and press Enter (or press ESC for menu):")
                else:
                    user_answer = ans
                    is_correct = (user_answer.lower() == str(q.get('answer')).lower())
                    break
            
        if is_correct:
            streak += 1
            score = 1 + (streak ** 2)
            print(f"\nCORRECT! The answer was {q.get('answer')}.")
            print(f"Your score is now {score}.")
        else:
            streak = 0
            score = 1 + (streak ** 2)
            print(f"\nINCORRECT. The correct answer was: {q.get('answer')}")
            print("Streak reset to 0. Score is now 1.")
            
        print(f"Current Score: {score}")
        
        cursor.execute("UPDATE users SET score = ? WHERE username = ?", (score, username))
        conn.commit()
        
        print("\nFeedback:")
        print("1 - Good question")
        print("2 - Disliked topic")
        print("3 - Disliked type")
        print("4 - Disliked both")
        print("ESC - Menu")
        print("Q - Quit")
        
        while True:
            ch = getch()
            if ch in ['1', '2', '3', '4']:
                if ch == '2' or ch == '4':
                    disliked_topics.add(topic)
                    cursor.execute("INSERT OR IGNORE INTO disliked_topics (username, topic) VALUES (?, ?)", (username, topic))
                
                if ch == '3' or ch == '4':
                    disliked_types.add(q_type)
                    cursor.execute("INSERT OR IGNORE INTO disliked_types (username, q_type) VALUES (?, ?)", (username, q_type))
                    
                conn.commit()
                break
            elif ch == 'esc':
                print_menu()
                clear_screen()
                print_header()
                print("\nFeedback:")
                print("1 - Good question")
                print("2 - Disliked topic")
                print("3 - Disliked type")
                print("4 - Disliked both")
                print("ESC - Menu")
                print("Q - Quit")
            elif ch.lower() == 'q':
                return

def main():
    clear_screen()
    print_header()
    
    check_files()
    
    while True:
        clear_screen()
        print_header()
        print("Press esc to open menu or any other key to start")
        ch = getch()
        if ch == 'esc':
            print_menu()
        else:
            break
            
    db_conn = get_db_connection()
    questions = load_questions()
    
    username, score = login(db_conn)
    play_quiz(db_conn, username, score, questions)
    
    print("\nThanks for playing!")
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print("\nExiting...")
        sys.exit(0)
