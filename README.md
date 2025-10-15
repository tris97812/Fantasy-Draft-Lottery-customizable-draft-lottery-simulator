# Fantasy-Draft-Lottery-customizable-simulator
A customizable and interactive NBA-style draft lottery simulator built with Streamlit.
Designed for fantasy basketball leagues, this tool allows commissioners and fans to simulate the draft lottery — either automatically or with manual number draws, just like in the real NBA lottery.

### 🚀 Features

##### 🧩 Custom League Setup
- Choose your league name and draft year
- Define any number of teams
- Assign custom ticket odds (e.g., 400 + 300 + 200 + 100 = 1000 total)
- Automatically generate 1,000 lottery combinations distributed according to ticket odds

##### 🎯 Manual or Auto Draw Mode
- Manually input drawn combinations (like in a live lottery ceremony)
- Or let the system automatically generate random combinations from the remaining pool
- Each pick updates in real time, showing:

##### Lottery ceremony 🎉
- Their original odds and simulated probability 📊
- Their movement vs. seed (up, down, unchanged) 🔼🔽⏺️

##### 📦 Data Management
- Export or inspect all assigned combinations
- Track awarded picks and remove drawn combinations automatically

### 🖥️ Installation
##### 1. Clone this repository
git clone https://github.com/YOUR-USERNAME/fantasy-draft-lottery-simulator.git
cd fantasy-draft-lottery-simulator

##### 2. Install dependencies
Create a virtual environment (optional) and install required packages:
pip install -r requirements.txt

##### 3. Run the app
streamlit run fantasylottery(EN).py

The app will open automatically in your browser (usually at http://localhost:8501).

### 📋 Requirements

Your requirements.txt should include:
streamlit
pandas
numpy
reportlab

(You can remove reportlab if you don’t plan to use PDF exports.)

### 🏆 Example Workflow

Go to “Setup & Simulation” tab
→ Enter your league name, draft year, teams, and ticket odds
→ Click “Apply Team List”
→ (Optional) Run 10,000 simulations to generate pick probabilities

Switch to “Live Draft Ceremony” tab
→ Watch the lottery unfold pick by pick!
→ Choose between manual input (for physical draws) or auto-generate.
→ See live commentary and statistical insights for each selection.

### 🏀 Credits

Developed by tris from FlensballersFantasy League as a fun project!
Inspired by the thrill of the NBA Draft Lottery, adapted for fantasy basketball leagues worldwide.
