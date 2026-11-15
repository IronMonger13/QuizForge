from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from quizzes.models import Category, Quiz, Question, Choice, QuizAttempt

User = get_user_model()


SAMPLE_QUIZZES = [
    {
        "title": "Python Programming Fundamentals",
        "category": "Programming",
        "description": "Test your knowledge of Python syntax, data types, operators, loops, functions, data structures and object-oriented programming.",
        "time_limit": 15,
        "questions": [
            {
                "question_text": "Which keyword is used to define a function in Python?",
                "marks": 1,
                "choices": [
                    {"choice_text": "function", "is_correct": False},
                    {"choice_text": "def", "is_correct": True},
                    {"choice_text": "define", "is_correct": False},
                    {"choice_text": "fun", "is_correct": False},
                ],
            },
            {
                "question_text": "Which of the following data types is immutable in Python?",
                "marks": 1,
                "choices": [
                    {"choice_text": "List", "is_correct": False},
                    {"choice_text": "Dictionary", "is_correct": False},
                    {"choice_text": "Set", "is_correct": False},
                    {"choice_text": "Tuple", "is_correct": True},
                ],
            },
            {
                "question_text": "What is the output of print(2 ** 3)?",
                "marks": 1,
                "choices": [
                    {"choice_text": "6", "is_correct": False},
                    {"choice_text": "8", "is_correct": True},
                    {"choice_text": "9", "is_correct": False},
                    {"choice_text": "5", "is_correct": False},
                ],
            },
            {
                "question_text": "Which operator is used to check whether two values are equal?",
                "marks": 1,
                "choices": [
                    {"choice_text": "=", "is_correct": False},
                    {"choice_text": "!=", "is_correct": False},
                    {"choice_text": "==", "is_correct": True},
                    {"choice_text": ">=", "is_correct": False},
                ],
            },
            {
                "question_text": "What does the len() function return?",
                "marks": 1,
                "choices": [
                    {"choice_text": "The data type of an object", "is_correct": False},
                    {
                        "choice_text": "The number of elements in an object",
                        "is_correct": True,
                    },
                    {
                        "choice_text": "The memory address of an object",
                        "is_correct": False,
                    },
                    {
                        "choice_text": "The largest element in an object",
                        "is_correct": False,
                    },
                ],
            },
            {
                "question_text": "Which statement is used to handle exceptions in Python?",
                "marks": 1,
                "choices": [
                    {"choice_text": "try-except", "is_correct": True},
                    {"choice_text": "if-else", "is_correct": False},
                    {"choice_text": "for-while", "is_correct": False},
                    {"choice_text": "def-return", "is_correct": False},
                ],
            },
            {
                "question_text": "What is the output of print(list(range(1, 5)))?",
                "marks": 1,
                "choices": [
                    {"choice_text": "[1, 2, 3, 4, 5]", "is_correct": False},
                    {"choice_text": "[0, 1, 2, 3, 4]", "is_correct": False},
                    {"choice_text": "[1, 2, 3, 4]", "is_correct": True},
                    {"choice_text": "[2, 3, 4, 5]", "is_correct": False},
                ],
            },
            {
                "question_text": "Which collection stores key-value pairs in Python?",
                "marks": 1,
                "choices": [
                    {"choice_text": "List", "is_correct": False},
                    {"choice_text": "Tuple", "is_correct": False},
                    {"choice_text": "Set", "is_correct": False},
                    {"choice_text": "Dictionary", "is_correct": True},
                ],
            },
            {
                "question_text": "What is the purpose of the __init__() method in a Python class?",
                "marks": 1,
                "choices": [
                    {"choice_text": "To delete an object", "is_correct": False},
                    {
                        "choice_text": "To initialise a newly created object",
                        "is_correct": True,
                    },
                    {"choice_text": "To import a module", "is_correct": False},
                    {"choice_text": "To terminate a program", "is_correct": False},
                ],
            },
            {
                "question_text": "Which keyword is used to create an anonymous function in Python?",
                "marks": 1,
                "choices": [
                    {"choice_text": "lambda", "is_correct": True},
                    {"choice_text": "anonymous", "is_correct": False},
                    {"choice_text": "yield", "is_correct": False},
                    {"choice_text": "map", "is_correct": False},
                ],
            },
        ],
    },
    {
        "title": "Cybersecurity Fundamentals",
        "category": "Technology",
        "description": "Explore cybersecurity fundamentals, including encryption, authentication, malware, network security and common cyber threats.",
        "time_limit": 15,
        "questions": [
            {
                "question_text": "Which protocol is primarily used to secure communication between a browser and a website?",
                "marks": 1,
                "choices": [
                    {"choice_text": "HTTP", "is_correct": False},
                    {"choice_text": "HTTPS", "is_correct": True},
                    {"choice_text": "FTP", "is_correct": False},
                    {"choice_text": "Telnet", "is_correct": False},
                ],
            },
            {
                "question_text": "What is the primary purpose of a firewall?",
                "marks": 1,
                "choices": [
                    {"choice_text": "To increase internet speed", "is_correct": False},
                    {
                        "choice_text": "To store encrypted passwords",
                        "is_correct": False,
                    },
                    {
                        "choice_text": "To monitor and control network traffic",
                        "is_correct": True,
                    },
                    {"choice_text": "To remove duplicate files", "is_correct": False},
                ],
            },
            {
                "question_text": "Which type of malware encrypts a victim's files and demands payment for their recovery?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Spyware", "is_correct": False},
                    {"choice_text": "Adware", "is_correct": False},
                    {"choice_text": "Rootkit", "is_correct": False},
                    {"choice_text": "Ransomware", "is_correct": True},
                ],
            },
            {
                "question_text": "What is phishing?",
                "marks": 1,
                "choices": [
                    {
                        "choice_text": "A technique used to trick people into revealing sensitive information",
                        "is_correct": True,
                    },
                    {
                        "choice_text": "A method of encrypting network traffic",
                        "is_correct": False,
                    },
                    {
                        "choice_text": "A technique for backing up databases",
                        "is_correct": False,
                    },
                    {
                        "choice_text": "A method of improving wireless signals",
                        "is_correct": False,
                    },
                ],
            },
            {
                "question_text": "Which of the following is an example of multi-factor authentication?",
                "marks": 1,
                "choices": [
                    {
                        "choice_text": "Using two different passwords",
                        "is_correct": False,
                    },
                    {
                        "choice_text": "Using a password and a fingerprint",
                        "is_correct": True,
                    },
                    {
                        "choice_text": "Using the same password twice",
                        "is_correct": False,
                    },
                    {
                        "choice_text": "Changing a username regularly",
                        "is_correct": False,
                    },
                ],
            },
            {
                "question_text": "Which encryption method uses the same secret key for encryption and decryption?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Asymmetric encryption", "is_correct": False},
                    {"choice_text": "Hashing", "is_correct": False},
                    {"choice_text": "Symmetric encryption", "is_correct": True},
                    {"choice_text": "Digital signing", "is_correct": False},
                ],
            },
            {
                "question_text": "Which port is commonly associated with SSH?",
                "marks": 1,
                "choices": [
                    {"choice_text": "21", "is_correct": False},
                    {"choice_text": "22", "is_correct": True},
                    {"choice_text": "25", "is_correct": False},
                    {"choice_text": "80", "is_correct": False},
                ],
            },
            {
                "question_text": "What is the primary purpose of hashing in password storage?",
                "marks": 1,
                "choices": [
                    {
                        "choice_text": "To convert passwords into reversible ciphertext",
                        "is_correct": False,
                    },
                    {"choice_text": "To make passwords shorter", "is_correct": False},
                    {
                        "choice_text": "To allow passwords to be viewed by administrators",
                        "is_correct": False,
                    },
                    {
                        "choice_text": "To produce a fixed-length digest that can be used for verification",
                        "is_correct": True,
                    },
                ],
            },
            {
                "question_text": "What does a Distributed Denial-of-Service (DDoS) attack attempt to do?",
                "marks": 1,
                "choices": [
                    {
                        "choice_text": "Overwhelm a service with traffic from multiple sources",
                        "is_correct": True,
                    },
                    {
                        "choice_text": "Steal a user's browsing history",
                        "is_correct": False,
                    },
                    {
                        "choice_text": "Encrypt files on a single computer",
                        "is_correct": False,
                    },
                    {
                        "choice_text": "Replace a website's domain name",
                        "is_correct": False,
                    },
                ],
            },
            {
                "question_text": "Which security principle grants users only the permissions necessary to perform their tasks?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Defense in depth", "is_correct": False},
                    {"choice_text": "Open access", "is_correct": False},
                    {"choice_text": "Principle of least privilege", "is_correct": True},
                    {"choice_text": "Security through obscurity", "is_correct": False},
                ],
            },
        ],
    },
    {
        "title": "Mathematics & Logical Reasoning",
        "category": "Mathematics",
        "description": "Challenge yourself with numerical patterns, arithmetic, percentages, algebra, probability and logical reasoning problems.",
        "time_limit": 15,
        "questions": [
            {
                "question_text": "Find the next number in the sequence: 2, 6, 12, 20, ?",
                "marks": 1,
                "choices": [
                    {"choice_text": "28", "is_correct": False},
                    {"choice_text": "30", "is_correct": True},
                    {"choice_text": "32", "is_correct": False},
                    {"choice_text": "36", "is_correct": False},
                ],
            },
            {
                "question_text": "What is 25% of 240?",
                "marks": 1,
                "choices": [
                    {"choice_text": "40", "is_correct": False},
                    {"choice_text": "50", "is_correct": False},
                    {"choice_text": "60", "is_correct": True},
                    {"choice_text": "80", "is_correct": False},
                ],
            },
            {
                "question_text": "If 3x + 5 = 20, what is the value of x?",
                "marks": 1,
                "choices": [
                    {"choice_text": "3", "is_correct": False},
                    {"choice_text": "5", "is_correct": True},
                    {"choice_text": "7", "is_correct": False},
                    {"choice_text": "10", "is_correct": False},
                ],
            },
            {
                "question_text": "A product costs ₹800 and is sold at a 10% discount. What is its selling price?",
                "marks": 1,
                "choices": [
                    {"choice_text": "₹700", "is_correct": False},
                    {"choice_text": "₹710", "is_correct": False},
                    {"choice_text": "₹720", "is_correct": True},
                    {"choice_text": "₹780", "is_correct": False},
                ],
            },
            {
                "question_text": "What is the average of 10, 20, 30, 40 and 50?",
                "marks": 1,
                "choices": [
                    {"choice_text": "25", "is_correct": False},
                    {"choice_text": "30", "is_correct": True},
                    {"choice_text": "35", "is_correct": False},
                    {"choice_text": "40", "is_correct": False},
                ],
            },
            {
                "question_text": "A fair six-sided die is rolled once. What is the probability of getting an even number?",
                "marks": 1,
                "choices": [
                    {"choice_text": "1/6", "is_correct": False},
                    {"choice_text": "1/3", "is_correct": False},
                    {"choice_text": "1/2", "is_correct": True},
                    {"choice_text": "2/3", "is_correct": False},
                ],
            },
            {
                "question_text": "Find the next number in the sequence: 3, 9, 27, 81, ?",
                "marks": 1,
                "choices": [
                    {"choice_text": "162", "is_correct": False},
                    {"choice_text": "189", "is_correct": False},
                    {"choice_text": "216", "is_correct": False},
                    {"choice_text": "243", "is_correct": True},
                ],
            },
            {
                "question_text": "A car travels 150 kilometres in 3 hours at a constant speed. What is its average speed?",
                "marks": 1,
                "choices": [
                    {"choice_text": "40 km/h", "is_correct": False},
                    {"choice_text": "45 km/h", "is_correct": False},
                    {"choice_text": "50 km/h", "is_correct": True},
                    {"choice_text": "60 km/h", "is_correct": False},
                ],
            },
            {
                "question_text": "If the ratio of boys to girls in a class is 2:3 and there are 25 students, how many are girls?",
                "marks": 1,
                "choices": [
                    {"choice_text": "10", "is_correct": False},
                    {"choice_text": "12", "is_correct": False},
                    {"choice_text": "15", "is_correct": True},
                    {"choice_text": "18", "is_correct": False},
                ],
            },
            {
                "question_text": "A number is increased by 20% and becomes 120. What was the original number?",
                "marks": 1,
                "choices": [
                    {"choice_text": "90", "is_correct": False},
                    {"choice_text": "96", "is_correct": False},
                    {"choice_text": "100", "is_correct": True},
                    {"choice_text": "110", "is_correct": False},
                ],
            },
        ],
    },
    {
        "title": "General Science",
        "category": "Science",
        "description": "Test your understanding of fundamental concepts in physics, chemistry, biology, human anatomy and the natural world.",
        "time_limit": 15,
        "questions": [
            {
                "question_text": "Which organelle is primarily responsible for producing energy in a eukaryotic cell?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Nucleus", "is_correct": False},
                    {"choice_text": "Ribosome", "is_correct": False},
                    {"choice_text": "Mitochondrion", "is_correct": True},
                    {"choice_text": "Golgi apparatus", "is_correct": False},
                ],
            },
            {
                "question_text": "What is the chemical symbol for gold?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Ag", "is_correct": False},
                    {"choice_text": "Au", "is_correct": True},
                    {"choice_text": "Gd", "is_correct": False},
                    {"choice_text": "Go", "is_correct": False},
                ],
            },
            {
                "question_text": "What is the approximate speed of light in a vacuum?",
                "marks": 1,
                "choices": [
                    {"choice_text": "3 × 10^6 m/s", "is_correct": False},
                    {"choice_text": "3 × 10^7 m/s", "is_correct": False},
                    {"choice_text": "3 × 10^8 m/s", "is_correct": True},
                    {"choice_text": "3 × 10^9 m/s", "is_correct": False},
                ],
            },
            {
                "question_text": "Which gas do plants primarily absorb from the atmosphere during photosynthesis?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Oxygen", "is_correct": False},
                    {"choice_text": "Nitrogen", "is_correct": False},
                    {"choice_text": "Carbon dioxide", "is_correct": True},
                    {"choice_text": "Hydrogen", "is_correct": False},
                ],
            },
            {
                "question_text": "What is the pH value of pure water at approximately 25°C?",
                "marks": 1,
                "choices": [
                    {"choice_text": "5", "is_correct": False},
                    {"choice_text": "6", "is_correct": False},
                    {"choice_text": "7", "is_correct": True},
                    {"choice_text": "9", "is_correct": False},
                ],
            },
            {
                "question_text": "Which part of the human brain is primarily responsible for balance and coordination?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Cerebrum", "is_correct": False},
                    {"choice_text": "Cerebellum", "is_correct": True},
                    {"choice_text": "Medulla oblongata", "is_correct": False},
                    {"choice_text": "Hypothalamus", "is_correct": False},
                ],
            },
            {
                "question_text": "What is the SI unit of electric current?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Volt", "is_correct": False},
                    {"choice_text": "Watt", "is_correct": False},
                    {"choice_text": "Ohm", "is_correct": False},
                    {"choice_text": "Ampere", "is_correct": True},
                ],
            },
            {
                "question_text": "Which blood cells are primarily responsible for transporting oxygen?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Red blood cells", "is_correct": True},
                    {"choice_text": "White blood cells", "is_correct": False},
                    {"choice_text": "Platelets", "is_correct": False},
                    {"choice_text": "Plasma cells", "is_correct": False},
                ],
            },
            {
                "question_text": "Which of the following is the hardest naturally occurring mineral?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Quartz", "is_correct": False},
                    {"choice_text": "Diamond", "is_correct": True},
                    {"choice_text": "Topaz", "is_correct": False},
                    {"choice_text": "Corundum", "is_correct": False},
                ],
            },
            {
                "question_text": "Which planet in our solar system has the largest number of confirmed moons as of the mid-2020s?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Jupiter", "is_correct": False},
                    {"choice_text": "Uranus", "is_correct": False},
                    {"choice_text": "Saturn", "is_correct": True},
                    {"choice_text": "Neptune", "is_correct": False},
                ],
            },
        ],
    },
    {
        "title": "Database & SQL Fundamentals",
        "category": "Technology",
        "description": "Test your knowledge of relational databases, SQL queries, joins, keys, constraints and database management concepts.",
        "time_limit": 15,
        "questions": [
            {
                "question_text": "Which SQL command is used to retrieve data from a database table?",
                "marks": 1,
                "choices": [
                    {"choice_text": "INSERT", "is_correct": False},
                    {"choice_text": "UPDATE", "is_correct": False},
                    {"choice_text": "SELECT", "is_correct": True},
                    {"choice_text": "DELETE", "is_correct": False},
                ],
            },
            {
                "question_text": "Which key uniquely identifies each record in a database table?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Foreign key", "is_correct": False},
                    {"choice_text": "Primary key", "is_correct": True},
                    {"choice_text": "Composite index", "is_correct": False},
                    {"choice_text": "Default key", "is_correct": False},
                ],
            },
            {
                "question_text": "Which SQL clause is used to filter rows based on a condition?",
                "marks": 1,
                "choices": [
                    {"choice_text": "ORDER BY", "is_correct": False},
                    {"choice_text": "GROUP BY", "is_correct": False},
                    {"choice_text": "WHERE", "is_correct": True},
                    {"choice_text": "SELECT", "is_correct": False},
                ],
            },
            {
                "question_text": "Which SQL function counts the number of rows in a result set?",
                "marks": 1,
                "choices": [
                    {"choice_text": "SUM()", "is_correct": False},
                    {"choice_text": "AVG()", "is_correct": False},
                    {"choice_text": "MAX()", "is_correct": False},
                    {"choice_text": "COUNT()", "is_correct": True},
                ],
            },
            {
                "question_text": "What is the purpose of a foreign key?",
                "marks": 1,
                "choices": [
                    {
                        "choice_text": "To link records between related tables",
                        "is_correct": True,
                    },
                    {"choice_text": "To encrypt database records", "is_correct": False},
                    {
                        "choice_text": "To sort records alphabetically",
                        "is_correct": False,
                    },
                    {
                        "choice_text": "To automatically delete duplicate databases",
                        "is_correct": False,
                    },
                ],
            },
            {
                "question_text": "Which SQL statement is used to modify existing records in a table?",
                "marks": 1,
                "choices": [
                    {"choice_text": "ALTER", "is_correct": False},
                    {"choice_text": "UPDATE", "is_correct": True},
                    {"choice_text": "INSERT", "is_correct": False},
                    {"choice_text": "CREATE", "is_correct": False},
                ],
            },
            {
                "question_text": "Which JOIN returns only rows that have matching values in both tables?",
                "marks": 1,
                "choices": [
                    {"choice_text": "LEFT JOIN", "is_correct": False},
                    {"choice_text": "RIGHT JOIN", "is_correct": False},
                    {"choice_text": "INNER JOIN", "is_correct": True},
                    {"choice_text": "CROSS JOIN", "is_correct": False},
                ],
            },
            {
                "question_text": "Which SQL constraint prevents a column from containing NULL values?",
                "marks": 1,
                "choices": [
                    {"choice_text": "UNIQUE", "is_correct": False},
                    {"choice_text": "DEFAULT", "is_correct": False},
                    {"choice_text": "CHECK", "is_correct": False},
                    {"choice_text": "NOT NULL", "is_correct": True},
                ],
            },
            {
                "question_text": "Which SQL clause is used to group rows that have the same values in specified columns?",
                "marks": 1,
                "choices": [
                    {"choice_text": "GROUP BY", "is_correct": True},
                    {"choice_text": "ORDER BY", "is_correct": False},
                    {"choice_text": "WHERE", "is_correct": False},
                    {"choice_text": "DISTINCT", "is_correct": False},
                ],
            },
            {
                "question_text": "Which ACID property ensures that a transaction is completed entirely or not at all?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Consistency", "is_correct": False},
                    {"choice_text": "Isolation", "is_correct": False},
                    {"choice_text": "Atomicity", "is_correct": True},
                    {"choice_text": "Durability", "is_correct": False},
                ],
            },
        ],
    },
    {
        "title": "General Knowledge",
        "category": "General Knowledge",
        "description": "Explore questions covering geography, history, science, international organisations, literature and world knowledge.",
        "time_limit": 15,
        "questions": [
            {
                "question_text": "Which organisation is responsible for publishing the Human Development Report?",
                "marks": 1,
                "choices": [
                    {"choice_text": "World Bank", "is_correct": False},
                    {
                        "choice_text": "United Nations Development Programme",
                        "is_correct": True,
                    },
                    {"choice_text": "World Health Organization", "is_correct": False},
                    {"choice_text": "International Monetary Fund", "is_correct": False},
                ],
            },
            {
                "question_text": "What is the capital city of Australia?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Sydney", "is_correct": False},
                    {"choice_text": "Melbourne", "is_correct": False},
                    {"choice_text": "Canberra", "is_correct": True},
                    {"choice_text": "Perth", "is_correct": False},
                ],
            },
            {
                "question_text": "Who was the first person to walk on the Moon?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Yuri Gagarin", "is_correct": False},
                    {"choice_text": "Buzz Aldrin", "is_correct": False},
                    {"choice_text": "Michael Collins", "is_correct": False},
                    {"choice_text": "Neil Armstrong", "is_correct": True},
                ],
            },
            {
                "question_text": "Which is the largest ocean on Earth?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Atlantic Ocean", "is_correct": False},
                    {"choice_text": "Pacific Ocean", "is_correct": True},
                    {"choice_text": "Indian Ocean", "is_correct": False},
                    {"choice_text": "Arctic Ocean", "is_correct": False},
                ],
            },
            {
                "question_text": "In which year did India gain independence from British rule?",
                "marks": 1,
                "choices": [
                    {"choice_text": "1945", "is_correct": False},
                    {"choice_text": "1946", "is_correct": False},
                    {"choice_text": "1947", "is_correct": True},
                    {"choice_text": "1950", "is_correct": False},
                ],
            },
            {
                "question_text": "Who wrote the play Romeo and Juliet?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Charles Dickens", "is_correct": False},
                    {"choice_text": "William Shakespeare", "is_correct": True},
                    {"choice_text": "Jane Austen", "is_correct": False},
                    {"choice_text": "George Orwell", "is_correct": False},
                ],
            },
            {
                "question_text": "Which country is home to the ancient city of Petra?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Egypt", "is_correct": False},
                    {"choice_text": "Greece", "is_correct": False},
                    {"choice_text": "Jordan", "is_correct": True},
                    {"choice_text": "Turkey", "is_correct": False},
                ],
            },
            {
                "question_text": "What is the currency of Japan?",
                "marks": 1,
                "choices": [
                    {"choice_text": "Won", "is_correct": False},
                    {"choice_text": "Yuan", "is_correct": False},
                    {"choice_text": "Ringgit", "is_correct": False},
                    {"choice_text": "Yen", "is_correct": True},
                ],
            },
            {
                "question_text": "Which Indian scientist is widely known as the Missile Man of India?",
                "marks": 1,
                "choices": [
                    {"choice_text": "C. V. Raman", "is_correct": False},
                    {"choice_text": "A. P. J. Abdul Kalam", "is_correct": True},
                    {"choice_text": "Homi J. Bhabha", "is_correct": False},
                    {"choice_text": "Vikram Sarabhai", "is_correct": False},
                ],
            },
            {
                "question_text": "Which international organisation has its headquarters in New York City and was founded in 1945?",
                "marks": 1,
                "choices": [
                    {"choice_text": "World Trade Organization", "is_correct": False},
                    {"choice_text": "International Monetary Fund", "is_correct": False},
                    {"choice_text": "United Nations", "is_correct": True},
                    {
                        "choice_text": "North Atlantic Treaty Organization",
                        "is_correct": False,
                    },
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Load sample quizzes into the database"

    def validate_sample_quizzes(self):
        quiz_titles = [quiz["title"] for quiz in SAMPLE_QUIZZES]

        if len(quiz_titles) != len(set(quiz_titles)):
            raise ValueError("Sample quiz titles must be unique.")

        for sample_quiz in SAMPLE_QUIZZES:
            if len(sample_quiz["questions"]) == 0:
                raise ValueError(
                    f"Quiz '{sample_quiz['title']}' must contain at least one question."
                )

            for question in sample_quiz["questions"]:
                if len(question["choices"]) != 4:
                    raise ValueError(
                        f"Question in '{sample_quiz['title']}' must have exactly four choices."
                    )
                correct_answers = sum(
                    choice["is_correct"] for choice in question["choices"]
                )

                if correct_answers != 1:
                    raise ValueError(
                        f"Question in '{sample_quiz['title']}' must have exactly one correct answer."
                    )

                if question["marks"] < 1:
                    raise ValueError(
                        f"Question in '{sample_quiz['title']}' must have at least one mark."
                    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.validate_sample_quizzes()
        self.stdout.write("Sample quiz data validation passed.")

        sample_user, user_created = User.objects.get_or_create(
            username="quizforge",
            defaults={
                "email": "quizforge@example.com",
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
        )

        if user_created:
            self.stdout.write(self.style.SUCCESS("Created sample quiz owner."))
        else:
            self.stdout.write("Sample quiz owner already exists.")

        self.stdout.write("Preparing sample quiz categories...")
        categories = {}

        for sample_quiz in SAMPLE_QUIZZES:
            category_name = sample_quiz["category"]
            category, category_created = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    "description": f"Sample quizzes covering {category_name.lower()}.",
                },
            )
            categories[category_name] = category

            if category_created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created category: {category_name}")
                )

        self.stdout.write("Creating sample quizzes...")
        for sample_quiz in SAMPLE_QUIZZES:
            category = categories[sample_quiz["category"]]
            quiz, quiz_created = Quiz.objects.get_or_create(
                title=sample_quiz["title"],
                owner=sample_user,
                defaults={
                    "description": sample_quiz["description"],
                    "category": category,
                    "time_limit": sample_quiz["time_limit"],
                    "status": Quiz.Status.PUBLISHED,
                    "is_sample": True,
                },
            )

            if not quiz_created and QuizAttempt.objects.filter(quiz=quiz).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped updating '{quiz.title}' because it has existing attempts."
                    )
                )
                continue

            if not quiz_created:
                quiz.description = sample_quiz["description"]
                quiz.category = category
                quiz.time_limit = sample_quiz["time_limit"]
                quiz.status = Quiz.Status.PUBLISHED
                quiz.is_sample = True
                quiz.save()

            if quiz_created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created sample quiz: {quiz.title}")
                )
            else:
                self.stdout.write(f"Sample quiz already exists: {quiz.title}")

            # Create or update questions and their choices
            for question_order, question_data in enumerate(
                sample_quiz["questions"], start=1
            ):
                question, question_created = Question.objects.update_or_create(
                    quiz=quiz,
                    order=question_order,
                    defaults={
                        "question_text": question_data["question_text"],
                        "marks": question_data["marks"],
                    },
                )

                for choice_order, choice_data in enumerate(
                    question_data["choices"], start=1
                ):
                    Choice.objects.update_or_create(
                        question=question,
                        order=choice_order,
                        defaults={
                            "choice_text": choice_data["choice_text"],
                            "is_correct": choice_data["is_correct"],
                        },
                    )

                if question_created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created question for: {quiz.title}")
                    )
