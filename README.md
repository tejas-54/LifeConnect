# 🌐 LifeConnect

**Decentralized, AI-Powered Organ Donation Matching & Transparency Platform**  
_"Every second counts. Every match saves lives."_

---

## 🚨 Problem

India faces a critical organ donation gap — outdated matching systems, zero transparency, logistics failures, and lack of public incentives. LifeConnect addresses this with a unified AI + Blockchain infrastructure.

---

## 💡 Solution

LifeConnect combines AI, Blockchain, and Geospatial logistics to ensure secure, transparent, and intelligent organ donation and transplant coordination.

---

## ⚙ Key Features

- 🔗 **Blockchain Consent & Tracking** – Immutable records of donor consent, health status, and organ custody (Ethereum + IPFS).
- 🧠 **AI Matching Engine** – Uses Gemini API to match based on viability, proximity, survival prediction, etc.
- 📦 **Smart Logistics Routing** – Fastest delivery planning via Mapbox + OR-Tools.
- 📊 **Dynamic HealthCards** – Auto-updated organ eligibility with blockchain verification.
- 🎁 **LifeToken Incentives** – Rewards for donors and families (health, insurance, tax perks).
- 🏥 **Stakeholder Dashboards** – Hospitals, regulators, and families get live updates.

---

## 🧠 Tech Stack

| Layer       | Technology                            |
|-------------|----------------------------------------|
| AI/ML       | Gemini API, Python, Scikit-learn       |
| Blockchain  | Ethereum, Solidity, IPFS               |
| Geospatial  | Mapbox, OR-Tools                       |
| Frontend    | React.js, Tailwind, MetaMask           |
| Backend     | Node.js, FastAPI, MongoDB              |
| Contracts   | Truffle, Web3.js, OpenZeppelin         |

---

## 🛠 Prerequisites

- Python 3.12+
- Node.js (with npm)
- MongoDB Community Server
- Ganache (Ethereum local node)
- Truffle Suite

---

## 🚀 Quick Setup

### 1. Clone the Repository

```
git clone https://github.com/your-org/LifeConnect.git
cd LifeConnect
```
### 1. Clone the Repository

```
git clone https://github.com/your-org/LifeConnect.git
cd LifeConnect
```
Initialize Hardhat project (only once if not done)  
```
npx hardhat
```
Compile smart contracts  
```
npx hardhat compile
```
Run local blockchain node
```
npx hardhat node
```

Deploy contracts to local network
```
npx hardhat run scripts/deploy.js --network localhost
```

### 3. AI Engine
```
cd ../ai_engine
```
Create a virtual environemnt
```
python -m venv venv
venv\Scripts\activate  # Windows
```
Install the requirements.txt
```
pip install -r requirements.txt
```
Start the ai server
```
python src/app.py
```

### 4. Backend API

```
cd ../backend
```
Install the requirements.txt
```
pip install -r requirements.txt
```
Run the Backend server
```
npm run dev
```
### 5. Frontend
```
cd ../frontend
```
```
set NODE_OPTIONS=--openssl-legacy-provider
```
Intialize and Install React app in frontend directory
```
npm install
```
Run the frontent react app
```
npm start
```


📄 License
Licensed under the MIT License.

🤝 Contribute
Open to contributions! Fork the repo and submit your PR.
