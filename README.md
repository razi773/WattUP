# Enerlytics Backend

This project is part of the *Enerlytics* platform, a smart energy monitoring and prediction system designed for industrial use.  


## Overview

Enerlytics is a **real-time energy monitoring and prediction system** that helps factories reduce costs, optimize efficiency, and ensure equipment reliability.  
The system combines IoT-enabled devices with a centralized dashboard, anomaly detection, consumption forecasting, and defect recognition via AI models.

It is deployed as a **backend-first architecture** that integrates:
- Smart meters connected to sub-distribution boards  
- A backend pipeline for real-time data ingestion and anomaly detection  
- A web dashboard for managers and admins  
- Optional CSV-based offline analysis for factories without IoT setups  

## Features

- ⚡ Real-time energy consumption monitoring (updates every 5 seconds)  
- 📈 Consumption & cost prediction (forecast next month in kWh & DT)  
- 🚨 Anomaly detection & reporting with probable causes  
- 📲 SMS notifications for abnormal consumption alerts  
- 🖼️ Image defect detection (upload photo to detect defective/good equipment)  
- 📂 CSV file analysis for offline usage  
- 🔔 Threshold & alert configuration by Admins  
- 📊 Dashboard with reports, trends, and peak usage visualization  

## Tech Stack

- **Backend**: Python (Flask/FastAPI)  
- **IoT Integration**: Carlo Gavazzi EM500 Series Smart Meter (Modbus TCP/IP, Wi-Fi)  
- **Database**: MySQL / SQL-based storage  
- **AI/ML**: TensorFlow & PyTorch (prediction, anomaly & defect detection models)  
- **Infrastructure**: Docker, Docker Compose (multi-service setup)  
- **Other Tools**: Postman, Jupyter Notebooks, Twilio (SMS alerts)  

## Directory Structure
root/
│
├── backend/ # Core API & IoT data pipeline
│ ├── anomaly_detection/ # ML models for anomaly detection
│ ├── prediction/ # Consumption & cost forecasting
│ ├── defect_detection/ # Image defect analysis
│ └── ...
│
├── dashboard/ # Frontend web interface
├── database/ # Schemas & SQL scripts
├── docker-compose.yml # Runs backend + dashboard + DB services
└── README.md

## Acknowledgments

This project was developed as part of PESTGM6.0 Technical Challenge - IEEE IAS/IES/PES ESPRIT STUDENT BRANCH JOINT CHAPTER .

Special thanks to our team members for their collaboration:

- Ons Nagara
- Sabaa Mellit
- Firas Salhi
- Fatma Lajmi
- Amel Mediuouni
- Youssef Kaabachi
- Razi Sniha

## Topics

- artificial-intelligence
- machine-learning
- energy-efficiency
- industrial-IoT

