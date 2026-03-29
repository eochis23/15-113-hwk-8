Here is a review of the code against the specifications provided in SPEC.md, along with analysis of potential bugs, security concerns, and code quality issues.

1. [PASS] Written in Python & Homescreen UI
Location: main.py, lines 265-276 (main() function)
Details: The program is correctly written in Python. When executed, it prints a clean header/homescreen interface and prompts the user to "Press esc to open menu or any other key to start", fulfilling the startup interface requirement.
2. [PASS] Password Hashing & Verification
Location: main.py, lines 100-105, 118-120
Details: The app correctly uses argon2.PasswordHasher to securely hash user passwords and verify them upon login. It also stores these hashes properly in the SQLite database rather than plain text.
3. [PASS] Question Feedback & Flow
Location: main.py, lines 218-231 (scoring feedback), lines 233-255 (disliking topics/types)
Details: When a user completes a question, the correct answer, the points earned, and the cumulative score are displayed. Furthermore, the 1-4 feedback system is perfectly implemented, successfully saving "disliked" topics/types to the database and filtering them from future questions.
4. [FAIL] Critical Security Vulnerability / Logic Error in Login
Location: main.py, lines 106-120
Details: If an existing user enters the wrong password, they are given a prompt to "1. Try again" or "2. Create new account". If they select 2, the code calls pass, breaks out of the if/else block, and proceeds to execute an INSERT OR REPLACE INTO users statement using the same username and the incorrect password they just provided. This is a severe account takeover vulnerability that allows anyone to reset another user's password and erase their score simply by failing a login attempt.
5. [FAIL] Homescreen Menu Flow
Location: main.py, lines 271-276
Details: The specification says "Press esc to open menu or any other key to start". However, if the user presses esc, the program calls print_menu(), and as soon as the menu returns, the code unconditionally drops into db_conn = get_db_connection() and begins the login sequence. Opening the menu from the home screen essentially forces the game to start immediately after, rather than looping back to the initial homescreen state.
6. [FAIL] Inconsistent Menu Access
Location: main.py, lines 202-207, 252-253
Details: The spec explicitly requires that opening the menu "should be possible at any other time too".
During the short_answer prompt, input() blocks key captures, meaning the user cannot press esc. The developer worked around this by asking the user to type :menu instead.
At the login screen, esc cannot be used at all.
At the feedback selection screen (line 252), pressing esc actually executes return to exit the quiz and quit the app completely, rather than opening the menu.
7. [WARN] Discarding Current Question upon Menu Open
Location: main.py, lines 159-164, 185-188
Details: If the user opens the menu while answering a Multiple Choice or True/False question, the inner loop breaks, and the code continues the outer loop. This honors the requirement of "without recording their answer as wrong," but it abruptly discards the current question entirely and pulls a brand-new question from the bank, which is poor UX for a user who simply wanted to double-check the menu controls.
8. [WARN] Infinite Loop on Empty Question Bank
Location: main.py, lines 145-155
Details: If all questions are filtered out by user dislikes, the program gracefully resets preferences. However, if the questions.json file's question array is completely empty to begin with, resetting preferences and setting available_questions = questions will leave available_questions empty. The program will continuously trigger the continue statement, resulting in an infinite loop printing "You have disliked all available questions!".
9. [WARN] Ambiguous Score Calculation
Location: main.py, lines 220-222
Details: The spec mandates: "The score should be 1+ the square of the number of correct questions they have answered in a row." The code implements this by making the points awarded per question equal to 1 + (streak ** 2), which is then added to a cumulative score. While a cumulative score behaves more naturally for a database-backed game, it conflicts with a literal reading of the spec (which implies the total score itself should equal 1 + streak²).
10. [WARN] Database File Check Prevents Startup
Location: main.py, lines 46-56
Details: The check_files() function enforces the requirement to show an error message if the database is missing. However, because it immediately executes sys.exit(1), it prevents sqlite3.connect() from exhibiting its default behavior (which is to seamlessly create the missing database file). A user cloning this project fresh cannot run it unless they manually run touch data.db first.
11. [WARN] Hardcoded Relative File Paths
Location: main.py, lines 13-14
Details: DB_FILE and QUESTIONS_FILE are set to raw relative paths ('data.db'). If the user runs the script from any location other than the exact root directory containing the script (e.g. python 15-113-hwk-8/main.py), it will fail to locate questions.json and exit. Using os.path.join(os.path.dirname(__file__), 'data.db') would resolve this code quality issue.