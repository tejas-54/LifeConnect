# 🌐 LifeConnect

**LifeConnect: Reinventing Organ Donation with Trust, Intelligence & Transparency**  
_"Every second counts. Every match saves lives."_

---

## ❗ The Challenge

India’s organ transplant system is in urgent need of transformation:

- 🧍‍♂️ 300,000+ patients are on transplant waiting lists.  
- 💔 20+ people die daily due to logistics failures and mismatched systems.  
- 📉 India's organ donation rate is just 0.52 per million — far below global benchmarks like Spain (49.6).  

But the root causes go beyond low donation rates:

- **🧬 Legacy Matching Algorithms** — Relying solely on blood and HLA type, ignoring critical data like viability windows, comorbidities, or distance.
- **🔒 Zero Transparency** — No traceability of organs post-consent. No feedback to donor families. Limited oversight.
- **🚧 Inefficient Transport** — Delays, lost organs, and cold-chain breaches due to outdated routing and customs clearance.
- **🧾 Static Records** — Donor health may change after registration; current systems can't track or predict declining organ viability.
- **🙈 No Incentives or Awareness** — Lack of motivation and information keeps potential donors disengaged.

---

## 💡 The LifeConnect Solution

**LifeConnect** is a decentralized, AI-powered platform that completely redefines how organ donations are matched, transported, and tracked. It ensures:

✅ Ethical, consent-driven workflows  
✅ AI-assisted matching with real-time prioritization  
✅ Blockchain-secured medical records and permissions  
✅ Efficient and transparent organ logistics  

---

## 🚀 Key Components

### 🧠 1. Gemini-AI Matching Intelligence

- Integrates Google Gemini API to move beyond basic blood/HLA typing.
- Uses machine learning to analyze:
  - Age, medical condition, recipient urgency
  - Graft rejection risk, proximity to organ location
  - Cold ischemia time, transplant outcome prediction
- Outputs a **live-ranked recipient list** to hospitals.

---

### 🔗 2. Ethereum + IPFS Blockchain Layer

- **Donor Consent + Group Rules** are secured with **Solidity smart contracts**.
- Organ status, approvals, and ownership changes are **immutably logged on Ethereum**.
- Medical history and dynamic HealthCards stored on **IPFS** (with CID hashed on-chain).
- Smart contracts govern:
  - Data access permissions
  - Consent enforcement
  - Tokenized rewards (Life Tokens)
  - Chain-of-custody validation

---

### 🩺 3. Dynamic HealthCard System

- Continuously updated organ eligibility per donor.
- Links disease history (e.g., diabetes, cancer) with organ viability predictions.
- Ensures **only medically safe and active donations** are considered.
- HealthCards can be viewed by stakeholders with permission via blockchain validation.

---

### 📦 4. Real-Time Smart Logistics Engine

Powered by **Mapbox + OR-Tools**:

- Automatically identifies fastest and safest air/ground routes based on:
  - Traffic, weather, airport customs, and route viability
- Determines recipient ranking **based on delivery ETA + organ viability**
- Auto-generates:
  - Cold-chain documents
  - Customs clearance forms
  - Permit certificates
- Each checkpoint is logged and time-stamped on-chain.

---

### 📊 5. Multi-Stakeholder Portals

| Stakeholder      | Features                                                                 |
|------------------|--------------------------------------------------------------------------|
| 🏥 Hospitals       | View AI-ranked matches, organ status, transport ETA, graft scores       |
| 🏛 Regulators/NGOs | Access audit logs, rule compliance, fairness metrics                    |
| 👨‍👩‍👧 Donor Families | See anonymized feedback, real-time transplant updates, impact dashboard |

---

### 🎁 6. LifeToken Rewards System

To promote altruism and long-term engagement:

- LifeTokens can be redeemed for:
  - 🩺 Free health screenings
  - 🛡 Discounts on insurance plans
  - 💸 Income tax exemptions
  - 🎗 Event-based donor campaigns

---

## 🛠 Tech Stack

| Layer              | Technology                                                   |
|--------------------|--------------------------------------------------------------|
| AI/ML              | Google Gemini API, Python, Scikit-learn                      |
| Blockchain         | Ethereum, Solidity, Web3.js                                  |
| Decentralized File | IPFS (medical records, documents, HealthCards)               |
| Smart Contracts    | Solidity (consent, tokenization, access control, tracking)   |
| Geospatial         | Mapbox, OR-Tools                                              |
| Frontend           | React.js, TailwindCSS, MetaMask                              |
| Backend/API        | Node.js, FastAPI, MongoDB                                    |
| Notifications      | WebSockets, Twilio, Email APIs                               |

---

## 🔁 Workflow Overview

1. Donor pledge and consent are verified and logged via smart contracts.
2. When an organ becomes available, Gemini-AI ranks recipients.
3. Blockchain verifies access and updates custody.
4. Logistics engine plans the delivery route and generates permits.
5. All updates are visible in real-time to hospitals, families, and authorities.
6. Post-transplant, impact is reported back to donor family. LifeTokens are issued.

---

## 💻 System Requirements

- Python 3.12+
- Node.js + npm
- MongoDB Community Server
- Ganache (Ethereum local blockchain)
- Truffle (for smart contract development)

---

## 🧰 Installation & Setup

### Step 1: Clone Repository

```
git clone https://github.com/your-org/LifeConnect.git
cd LifeConnect
```


