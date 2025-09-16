Enerlytics Backend

This project is part of the Enerlytics platform, a smart energy monitoring and prediction system designed for industrial use.
It was developed as part of the coursework for ESE.INFIA0010 - AI Project at Esprit School of Engineering.

<div align="center"> <img src="assets/enerlytics_architecture.jpeg" height="550" alt="enerlytics_architecture"> </div>
Overview

Enerlytics is a real-time energy monitoring and prediction system that helps factories reduce costs, optimize efficiency, and ensure equipment reliability.
The system combines IoT-enabled devices with a centralized dashboard, anomaly detection, consumption forecasting, and defect recognition via AI models.

It is deployed as a backend-first architecture that integrates:

Smart meters connected to sub-distribution boards

A backend pipeline for real-time data ingestion and anomaly detection

A web dashboard for managers and admins

Optional CSV-based offline analysis for factories without IoT setups

Features

Real-time energy consumption monitoring (updates every 5 seconds)

Consumption & cost prediction (forecast next month in kWh & DT)

Anomaly detection & reporting with probable causes

SMS notifications for abnormal consumption alerts

Image defect detection (upload photo to detect defective/good equipment)

CSV file analysis for offline usage

Role-based user management (Admins, Managers, Workers)

Threshold & alert configuration by Admins

Dashboard with reports, trends, and peak usage visualization

Tech Stack

Backend: Python (Flask/FastAPI)

IoT Integration: Carlo Gavazzi EM500 Series Smart Meter (Modbus TCP/IP, Wi-Fi)

Database: MySQL / SQL-based storage for consumption, anomalies, users

AI/ML: TensorFlow & PyTorch (prediction, anomaly & defect detection models)

Infrastructure: Docker, Docker Compose (multi-service setup)

Other Tools: Postman (API testing), Jupyter Notebooks (ML experiments), Twilio (SMS alerts)

Directory Structure
root/
│
├── backend/                # Core API & IoT data pipeline
│   ├── anomaly_detection/  # ML models for anomaly detection
│   ├── prediction/         # Consumption & cost forecasting
│   ├── defect_detection/   # Image defect analysis
│   └── ...
│
├── dashboard/              # Frontend web interface for managers/admins
├── database/               # Schemas & SQL scripts
├── docker-compose.yml      # Runs backend + dashboard + DB services
└── README.md

Getting Started

Clone the repository

git clone https://github.com/your-org/enerlytics.git
cd enerlytics


Build and run all services

docker-compose up --build


Access the dashboard
Open http://localhost:5000 in your browser.

Use the API Gateway
Send API requests via Postman or cURL.

Usage

Managers & admins can log in via username/password or face recognition.

Dashboard shows monthly energy consumption, real vs predicted usage, and cost forecast.

Admins configure thresholds and alert rules.

Workers receive SMS notifications when anomalies occur.

Optional: Upload CSV files or images for offline analysis.

Contributing

Please check CONTRIBUTING.md for guidelines before submitting pull requests.

Acknowledgments

This project was developed as part of ESE.INFIA0010 - AI Project at Esprit School of Engineering.

Special thanks to our team members for their collaboration:

Ons Nagara

Sabaa Mellit

Firas Salhi

Fatma Lajmi

Amel Mediuouni

Youssef Kaabachi

Topics

artificial-intelligence

machine-learning

energy-efficiency

anomaly-detection

industrial-IoT

python

flask

docker

containerization

smart-metering
