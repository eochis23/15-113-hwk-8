##Goal
Write a command-line quizzer to help a student learn about Python. It should meet all of the following specifications and use all of the functions described, additionally it should be written in Python.

##User-facing Behavior
When the user runs the Python function, it should print a simple home-screen like message to start the user off. Then it should say "Press esc to open menu or any other key to start" If they open the menu (this should be possible at any other time too) it should show  them that they can use the number keys 1-9 for multiple choice questions, 1-2 for true or false questions, and they may type their answer for short answer questions. If they choose to start, then they should be prompted to log in by first entering their username and then their password. Use argon2 to hash their password to verify that it is correct (see database for what to verify it against). After a successful password attempt for their account, they are logged in. Then they will be asked questions from a question bank. They will answer using the controls listed above, and after answering the correct answer and whether they were correct is displayed, along with their score. The score should be 1+ the square of the number of correct questions they have answered in a row. They should then press 1 if the question was good, 2 if they disliked the topic, 3 if they disliked the type, and 4 if they disliked both. After this, another question comes up and the process repeats.

###Potential errors
If the json file with questions or the database to store progress is missing, the app should present the user with this info in the same style as the rest of the command line interface. If the user's input type is not right for the type of question they are answering, prompt them to try again or open the menu without recording their answer as wrong. If they enter the wrong password, prompt them to try again or create a new account.

##File Structure
main.py - stores the main looping logic. 
data.db - stores user scores and the hash values of passwords
questions.json - stores questions as described in the question session below.

##Question examples
{
  "questions": [
    {
      "question": "What keyword is used to define a function in Python?",
      "type": "multiple_choice",
      "options": ["func", "define", "def", "function"],
      "answer": "def",
      "category": "Python Basics"
    },
    {
      "question": "A list in Python is immutable.",
      "type": "true_false",
      "answer": "false",
      "category": "Data Structures"
    },
    {
      "question": "What built-in function returns the number of items in a list?",
      "type": "short_answer",
      "answer": "len",
      "category": "Python Basics"
    }
  ]
}


###Checklist
Running main.py with a missing required file prints an error
The menu is always visible
The format of the print statements makes it easy for a person to play
Someone can figure out how to use the app by just running main.py and nothing else
People can play and stop seeing questions they dislike
Scores are tracked and maintained, tied to accounts
Password are never stored