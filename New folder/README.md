# 🚀 CDAZZDEV MLE Assessment: Zero-Empathy Jira Signal Extractor

**Candidate:** Tirush  
**Role:** Machine Learning Engineer  
**Target Organization:** Ceylon Dazzling Dev Holding (Pvt.) Ltd. (CDAZZDEV)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](INSERT_YOUR_COLAB_LINK_HERE)

---

## 📌 1. The Business Problem
In modern software development lifecycles, there is a massive translation gap between customer support and engineering. Customer support tickets are inherently **noisy, unstructured, and emotionally charged**. 

When these raw communications are passed directly to engineering teams, it creates cognitive overhead. Developers must waste time parsing through anger, frustration, and non-technical filler to isolate the core system failure. The challenge is to build an automated layer that successfully strips human emotion ("Noise") and extracts only the objective, reproducible technical variables ("Signal").

## 💡 2. The Solution
I engineered an automated **Production-Grade Supervised Fine-Tuning (SFT) Pipeline**. This pipeline takes unstructured user complaints and translates them into rigid, highly objective Markdown-formatted Jira Bug Reports. 

The system acts as a "Zero-Empathy Data Extractor"—it does not apologize, it does not converse, and it does not hallucinate. It functions as a strict data processor that bridges the gap between frustrated users and highly technical engineering boards.

---

## 🧠 3. Model Selection: GPT-3.5-Turbo vs. Llama-2
The assessment requested a choice between fine-tuning `gpt-3.5-turbo` and `Llama-2`. I elected to build the pipeline around **GPT-3.5-Turbo** for the following architectural and business reasons:

1. **Instruction & Schema Adherence:** The goal of this task is strict Markdown formatting (extracting specific Jira headers). GPT-3.5-Turbo inherently possesses a stronger baseline for instruction following and complex format adherence compared to a base 7B Llama-2 model.
2. **Infrastructure Reliability:** Fine-tuning a 7B parameter open-source model on a standard cloud GPU (like a Google Colab T4) often introduces severe hardware bottlenecks, such as Out-of-Memory (OOM) crashes and prolonged setup times involving quantization (QLoRA) and gradient accumulation matching. 
3. **Time-to-Deployment:** Utilizing OpenAI’s managed infrastructure allows for rapid iteration and deployment, shifting the engineering focus from *infrastructure debugging* to *data quality optimization*, which drives higher business value.

---

## ⚙️ 4. Fine-Tuning Methodology (The "How")

The core philosophy of this project is that **"Fine-tuning is a data engineering problem, not just an API call."** To ensure a production-ready model, I implemented a 4-stage pipeline:

### Stage A: Few-Shot Synthetic Data Generation (SDG)
To overcome the "politeness bias" inherent in standard base models, I utilized **GPT-4o** as a highly capable Teacher Model. I engineered a strict prompt using "Few-Shot Anchoring"—providing the teacher model with hand-crafted, perfect templates. This forced GPT-4o to generate 50 complex, edge-case training samples encompassing compound bugs, vague inputs, and high user emotion.

### Stage B: Programmatic Sanitization (The Guardrail)
Even with strict prompting, LLMs can occasionally leak conversational filler (e.g., "I'm sorry to hear that", or "Fix it ASAP"). Before the data reached the `.jsonl` training file, it passed through a custom Python sanitization layer. This programmatic logic gate forcibly sliced the generated text, guaranteeing that **0% of conversational drift** entered the training corpus. 

### Stage C: Hyperparameter Optimization
The sanitized dataset was uploaded to OpenAI for fine-tuning. I specifically configured the training job to run for **4 Epochs** (above the standard default). This decision was made to actively "lock" or "over-index" the model into the rigid Markdown schema required for Jira, preventing format degradation during edge-case inference.

### Stage D: System Prompting at Inference
During execution, the model is initialized with a "Headless Engine" system message: *(“You are a headless Jira data extraction engine. Output ONLY structured Markdown. No greetings, no empathy…”)*. Furthermore, inference temperature is set to `0.0` to eliminate randomness and guarantee deterministic schema output.

---

## 📊 5. Quantitative Evaluation (LLM-as-a-Judge)

To quantitatively prove model readiness and avoid subjective human bias, I engineered an automated **Batch Evaluation Script**. 

The script runs a suite of 10 complex "Stress Test" emails through the fine-tuned model. These emails contain deliberate typos, missing environment variables, and extreme frustration. I then utilized GPT-4o as an automated judge, programmed to output a JSON evaluation heavily penalizing any conversational leakage or missing Markdown headers.

### Final Metrics:
* **Total Score:** `89 / 100`
* **Average Accuracy:** `8.9 / 10.0`
* **Behavioral Observation:** The fine-tuned model successfully learned to ignore extreme customer frustration, synthesize logical 'Steps to Reproduce', and extract only the relevant environment variables and priorities.

---

## ❓ Technical Q&A: Architectural Justifications

**Q1: Why did you choose to fine-tune GPT-3.5-Turbo over Llama-2?**
> **A:** While Llama-2 is a powerful open-weights model, fine-tuning a 7B model for strict Markdown formatting requires significant infrastructure overhead (GPU memory management, QLoRA quantization, etc.). GPT-3.5-Turbo offers a vastly superior baseline for complex instruction adherence and formatting. By using OpenAI's managed infrastructure, I optimized for **Time-to-Value** and **Format Reliability**, which are critical in a production business environment.

**Q2: Why use Synthetic Data Generation (SDG) instead of manually writing the dataset?**
> **A:** Manual data entry is slow and prone to human bias. By using **GPT-4o** as a teacher model with a "Few-Shot" prompt, I was able to rapidly generate 50 highly diverse edge-cases (e.g., compound bugs, missing environment variables, extreme emotion). This ensures the student model (GPT-3.5-Turbo) is trained on a robust, comprehensive dataset that mimics unpredictable real-world user behavior.

**Q3: LLMs naturally want to be "helpful." How did you stop the model from acting like a customer service agent?**
> **A:** This was the primary engineering challenge. I solved it using a two-layered defense:
> 1. **Prompt Engineering:** I applied *Negative Constraints* in the teacher model's prompt, explicitly banning words like "Sorry", "ASAP", and "Hello".
> 2. **Data Engineering:** I built a custom Python sanitization script that programmatically sliced the text to guarantee 0% conversational drift entered the `.jsonl` training file.

**Q4: Why did you override the default fine-tuning parameters and force 4 Epochs?**
> **A:** Standard fine-tuning defaults are usually optimized for conversational tone or general knowledge extraction. Because this use-case requires strict adherence to a rigid Jira Markdown schema, I increased the epoch count to 4. This actively "over-indexes" the model onto the structural formatting, practically eliminating the risk of schema hallucination during inference.

**Q5: How did you validate that the fine-tuned model actually performs better?**
> **A:** To avoid subjective human bias, I implemented an automated **LLM-as-a-Judge** pipeline. I fed 10 highly complex, never-before-seen "Stress Test" emails into the fine-tuned model. I then used GPT-4o (configured with a strict JSON grading schema) to score the outputs based on header presence and emotional neutrality. The model achieved an 89% accuracy score, proving its production readiness.

---

## 🔍 6. How to Review the Code
The entire pipeline is documented in a sequential, interactive Google Colab notebook. 
1. Click the **"Open in Colab"** badge at the top of this README.
2. The notebook is broken down into Phases (1 through 5), with Markdown cells explaining the business logic behind each code block.
3. You can view the final **Batch Evaluation metrics** at the bottom of the notebook, or run the **Interactive Inference** cell to test the model dynamically with your own input.