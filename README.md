# ☕ Cafe AI Chatbot

### An Intelligent Cafe Ordering Assistant Built with Python, PyTorch & NLP

<p align="center">
  <strong>Order smarter. Chat naturally. Enjoy your coffee.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10">
  <img src="https://img.shields.io/badge/PyTorch-Deep%20Learning-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch">
  <img src="https://img.shields.io/badge/NLP-Intent%20Classification-8A2BE2?style=for-the-badge" alt="NLP">
  <img src="https://img.shields.io/badge/Status-Active%20Development-2EA44F?style=for-the-badge" alt="Active Development">
</p>

---

## 📌 Overview

**Cafe AI Chatbot** is a Python-based conversational ordering assistant designed to simplify the cafe ordering experience through natural language interaction.

Powered by a PyTorch neural network and Natural Language Processing (NLP), the chatbot identifies customer intents, recognizes menu items, manages a shopping cart, calculates order totals, and guides customers through a simulated checkout process.

The project combines machine learning-based intent classification with rule-based order processing to create a practical, beginner-friendly AI application.

## ✨ Key Features

| Feature | Description |
|---|---|
| 🧠 Intent Classification | Predicts customer intent using a trained PyTorch neural network. |
| ☕ Interactive Menu | Displays cafe products with item names and prices. |
| 🛒 Smart Cart Management | Adds menu items and manages requested quantities. |
| 🔢 Quantity Extraction | Supports numeric quantities and common number words. |
| 🧾 Bill Calculation | Calculates item subtotals and the total order amount. |
| 🗑️ Item Removal | Removes items or reduces their quantities in the cart. |
| ✅ Checkout Flow | Requests confirmation before finalizing an order. |
| 🆔 Order Identification | Generates a unique order reference for each completed checkout. |
| 💬 Conversational Interface | Accepts supported natural language requests and direct commands. |

## 🛠️ Technology Stack

- **Language:** Python 3.10
- **Machine Learning:** PyTorch
- **Natural Language Processing:** NLTK
- **Text Processing:** Tokenization and Bag-of-Words feature extraction
- **Model Architecture:** Feed-forward neural network for intent classification
- **Data Format:** JSON-based intent definitions
- **Version Control:** Git and GitHub

## 🏗️ Project Architecture

```text
Customer Message
       |
       v
Text Preprocessing
(NLTK Tokenization)
       |
       v
Intent Classification
(PyTorch Neural Network)
       |
       v
Conversation Controller
       |
       +---------------------+
       |                     |
       v                     v
Intent-Based Replies    Cafe Order Logic
                             |
                 +-----------+-----------+
                 |           |           |
                 v           v           v
                Menu        Cart       Checkout
                             |
                             v
                     Bill Calculation
                             |
                             v
                       Order Summary
```

**Hybrid approach:** Explicit menu and cart commands are handled directly by application logic, while other supported conversational requests can use the trained intent classifier. This improves reliability for structured ordering operations.

## 📂 Project Structure

```text
Cafe-AI-Chatbot/
│
├── chat.py             # Chatbot interface and order processing
├── train.py            # Neural network training script
├── model.py            # Neural network architecture
├── nltk_utils.py       # Tokenization and Bag-of-Words utilities
├── intents.json        # Training patterns and response definitions
├── data.pth            # Trained model checkpoint
├── .gitignore          # Files excluded from version control
└── README.md           # Project documentation
```

*The structure above reflects the core files used by this project. Update it if you add tests, configuration files, or additional modules.*

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/Cafe-AI-Chatbot.git
cd Cafe-AI-Chatbot
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create a virtual environment

**Windows PowerShell**

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the Python executable inside `.venv` directly instead of changing your system execution policy.

### 3. Install dependencies

```powershell
python -m pip install torch nltk numpy
```

Use a PyTorch installation compatible with your system if the default installation does not work.

### 4. Download NLTK resources

```powershell
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

### 5. Train the model

If you modify `intents.json`, retrain the model so the vocabulary and intent labels match the updated data:

```powershell
python train.py
```

This generates or updates `data.pth`, which the chatbot loads during execution.

### 6. Start the chatbot

```powershell
python chat.py
```

**Note:** The repository must include a compatible `data.pth` checkpoint, or users must train the model locally before running the chatbot.

## ☕ Available Cafe Menu

The application currently uses a sample menu with configurable prices.

| Menu Item | Price (INR) |
|---|---:|
| Espresso | ₹80 |
| Cappuccino | ₹120 |
| Cold Coffee | ₹140 |
| Masala Tea | ₹40 |
| Hot Chocolate | ₹130 |
| Veg Sandwich | ₹100 |
| Grilled Sandwich | ₹150 |
| Veg Burger | ₹120 |
| French Fries | ₹90 |
| Brownie | ₹100 |

Prices are demo values and can be changed in the menu configuration in `chat.py`.

## 💬 Example Conversation

```text
Bot: Hello! Welcome to Cafe AI.

Bot: Here is our menu.

You: menu

Bot: [Displays cafe menu and prices]

You: Veg Sandwich

Bot: Added 1 x Veg Sandwich.

YOUR CART
Veg Sandwich x 1 = Rs. 100
TOTAL: Rs. 100

You: 2 cappuccino

Bot: Added 2 x Cappuccino.

YOUR CART
Veg Sandwich x 1 = Rs. 100
Cappuccino x 2 = Rs. 240
TOTAL: Rs. 340

You: checkout

Bot: Confirm your order? (yes/no): yes
Bot: Enter your name: Customer

******************************************
               ORDER PLACED!
Order ID : CAFE-XXXXXXXX
Customer : Customer
Veg Sandwich x 1 = Rs. 100
Cappuccino x 2 = Rs. 240
TOTAL AMOUNT: Rs. 340

Thank you for visiting Cafe AI!
******************************************
```

*Illustrative example: actual responses and formatting depend on the current implementation.*

## 🧠 How Intent Classification Works

The chatbot uses a supervised learning workflow:

1. **Training data:** `intents.json` contains example phrases grouped by intent tags.
2. **Tokenization:** NLTK splits input text into tokens.
3. **Feature extraction:** Bag-of-Words converts tokens into a numerical vector based on the training vocabulary.
4. **Prediction:** The trained PyTorch neural network produces scores for available intent classes.
5. **Response handling:** The application uses the predicted intent to select a response or trigger a supported action.

### Example intents

| Intent | Example user message |
|---|---|
| `greeting` | Hello! |
| `show_menu` | Show me the menu |
| `add_to_cart` | I want a veg burger |
| `view_cart` | Show my cart |
| `remove_from_cart` | Remove the brownie |
| `checkout` | Place my order |
| `cancel_order` | Clear my cart |
| `goodbye` | Bye! |

Menu recognition and cart operations are handled by explicit application logic where implemented; not every order operation depends on the neural network prediction.

## 🔐 Current Scope and Limitations

This is a local, console-based prototype intended for learning and demonstration.

- Orders and cart contents are stored in memory and reset when the application exits.
- Checkout generates a local order reference; it does not submit an order to a real cafe.
- No database, authentication, payment gateway, or live inventory integration is currently included.
- Intent classification accuracy depends on the quality and coverage of training examples.
- Menu items and prices are configured locally.

**No real payment is processed, and no order is transmitted to a business.**

## 🚀 Future Enhancements

- [ ] Persistent cart and order history using SQLite or MySQL
- [ ] FastAPI backend for order management
- [ ] REST APIs for menu, cart, and checkout
- [ ] Web-based interface using React or Angular
- [ ] Improved entity extraction for menu items and quantities
- [ ] Automated unit and integration tests
- [ ] Database-backed order IDs and status tracking
- [ ] Optional multilingual conversational support
- [ ] Integration with a real ordering platform after adding appropriate validation and security

## 🧪 Testing Ideas

Important scenarios to validate before extending the project:

- Add one item and multiple quantities.
- Add multiple different items in a single message.
- Remove an item that exists in the cart.
- Attempt to remove an item that is not in the cart.
- Checkout with an empty cart.
- Cancel checkout and verify that the cart remains unchanged.
- Enter an invalid menu number.
- Verify order totals for different quantities.

## 🎯 Learning Outcomes

This project demonstrates practical experience with:

- Python application development
- Fundamental NLP preprocessing techniques
- Supervised intent classification
- PyTorch model training and inference
- JSON-based configuration
- Rule-based entity and quantity extraction
- Cart management and checkout workflows
- Git version control and incremental project development

## 👨‍💻 Author

**Surendra Patidar**

Aspiring Java Full Stack Developer | Backend Developer & AI Engineer

- GitHub: [SurendraPatidar1](https://github.com/SurendraPatidar1)
- LinkedIn: [Surendra Patidar](https://www.linkedin.com/in/surendra-patidar-0b2555228/)

## 📄 License

A license has not yet been specified. Add a `LICENSE` file if you want to distribute the project under a particular open-source license. Also verify the original repository's licensing terms before redistributing or relicensing any inherited code.

---

<p align="center">
  <strong>Built to explore the intersection of conversational AI, NLP, and practical software engineering.</strong>
</p>
