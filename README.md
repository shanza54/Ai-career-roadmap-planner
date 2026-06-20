# 🗺️ AI Career & Skill Path Planner
Live Demo:https://shanzaejaz-roadmap-generator.hf.space

An interactive, AI-powered roadmap generation engine designed to build highly customized learning and career progression tracks. Driven by **LLaMA 3.3 70B** via the **Groq API**, this application structures complex domains into weekly milestones, maps topics, provides concrete mini-projects, and aggregates real-world learning resources.

## 🚀 Features

* **Customized Track Planning:** Generates multi-month schedules adjusted dynamically based on your domain choice, current expertise tier, and daily available study hours.
* **Interactive HTML Timeline:** Renders a clean, responsive CSS/JS timeline featuring expandable breakdown cards, category-coded chips, and concrete mini-project scopes.
* **Live Progress Tracking:** Features a state-driven checklist where marking milestones instantly recalculates and fills a gradient progress indicator.
* **On-Demand PDF Compilation:** Bundles complete roadmap details, projects, topic hierarchies, and learning resource hyper-links into a downloadable PDF document using `fpdf`.

---

## 🛠️ Tech Stack

* **Frontend Framework:** Gradio (Python)
* **Inference Engine:** Groq API (`llama-3.3-70b-versatile`)
* **Document Generation:** FPDF
* **Data Structure:** JSON Schema Validation Regex parsing

---

## 📦 Installation & Local Setup

To run this application locally on your machine, follow these steps:

### 1. Clone the Repository
```bash
git clone https://github.com/shanza54/Ai-career-roadmap-planner.git
cd Ai-career-roadmap-planner
```
