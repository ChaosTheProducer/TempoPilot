# TempoPilot

TempoPilot is a modern, AI-powered schedule management tool built with PyQt6. It provides users with a dynamic daily schedule view, personalized activity recommendations, and navigation assistance—all in a sleek and interactive UI.

## 🚀 Features

* 🗓 **Daily Schedule View** with interactive timeline
* 🔍 **Event Management**: add, edit, delete events with custom time, color, and place
* 🧠 **Recommendation Panel**: generate activity suggestions based on location and interest (powered by Deepseek LLM)
* 📍 **Map Navigation**: in-app route planning using Google Maps
* 🌙 **Dark Mode**: enabled via qdarktheme
* 📌 **Persistence**: SQLite-backed storage for events
* 🎨 **Custom Event Appearance**: adjust color and transparency
* 🖱️ **Right-click Menu**: modify time, place, name, or delete an event

## 💻 Installation

### 1. Clone the repository

```bash
git clone https://github.com/ChaosTheProducer/TempoPilot
cd tempopilot
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Configure Deepseek API Key

Open the existing `config.json` file in the root directory and edit the value of the `deepseek_api_key` field:

```json
{
  "deepseek_api_key": "your-deepseek-api-key-here"
}
```

This key is required to generate activity recommendations.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the application

```bash
python main.py
```

## 📦 Dependencies

Major packages:

* `PyQt6`
* `PyQt6-WebEngine`
* `qdarktheme`
* `qfluentwidgets`
* `qframelesswindow`
* `openai`

All dependencies are listed in [`requirements.txt`](./requirements.txt).

## 🧑‍💻 Team Members (Group 6 - JC3510 @ SCNU)

* Yingjie Lei
* Yefei Pan
* Ziyan Chen
* Zishen He
* Zirui Zhu
* Ruyuan Ge

## 🌐 Resources

* **Course**: JC3510 Software Engineering
* **Institution**: South China Normal University, Aberdeen Institute of Data Science and Artificial Intelligence

## 📄 License

This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).

> This application was developed based on the open-source project [Tempus](https://github.com/rohankishore/Tempus) by Rohan Kishore. We acknowledge and thank the original author for the foundation upon which this work was built.

---

For issues, suggestions, or contributions, feel free to open a PR or issue on GitHub.
