# 🚀 Portialabs AI

> **Developed during [Encode AI London Hackathon 2025](https://luma.com/AI-London-2025)**

---

Portialabs AI is an automated agent designed to proactively check public-facing services for the latest vulnerabilities—pulled in real-time from [Sploitus](https://sploitus.com)—based on IP address and domain.  
By leveraging the [portiaai SDK](https://github.com/portialabs/portiaai-sdk), AWS Lambda, and a cloud-native stack, the agent helps automate vulnerability detection at scale, with a focus on rapid response as threats emerge.

---

## 🧠 How It Works

- **Weekly Vulnerability Sync:**  
  The agent fetches the latest vulnerabilities from Sploitus once per week.

- **Target Selection:**  
  It queries the service database for assets matching known vulnerable tech stacks.

- **Automated Check Generation:**  
  For each candidate, it generates a tailored AWS Lambda function to test the service for the specific vulnerability (most checks work via HTTP requests).

- **Deployment & Execution:**  
  Lambda functions are deployed and executed to confirm (or clear) potential vulnerabilities.

---

## 🛠 Installation

**From source:**
```bash
git clone https://github.com/rendizi/portialabs-ai
cd portialabs-ai
pip install -r requirements.txt
uvicorn main:app
```

**Or with Docker:**
```bash
docker build -t ai_agent .
docker run ai_agent
```

---

## 💡 Technologies Used

- Python & FastAPI  
- MongoDB  
- AWS Lambda  
- Portialabs AI SDK  
- OpenAI  
- next.js & TypeScript

---

## 📸 Project Showcase

### Sploitus Exploits  
<img src="/assets/sploitus.png" alt="Sploitus" width="500px">

### Home Page  
<img src="/assets/home.png" alt="Home page" width="500px">

### Login Page  
<img src="/assets/login.png" alt="Login page" width="500px">

### Dashboard Page  
<img src="/assets/dashboard.png" alt="Dashboard page" width="500px">

### AWS Lambda Function  
<img src="/assets/aws.png" alt="AWS Lambda function" width="500px">
