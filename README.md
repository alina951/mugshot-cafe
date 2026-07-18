## ☕ Mugshot Coffee – Cloud ETL Pipeline
## Project Summary

Mugshot Coffee is a cloud-native ETL (Extract, Transform, Load) pipeline built on Amazon Web Services (AWS). The solution automates the processing of coffee shop sales transactions by extracting raw CSV files, transforming and cleaning the data, loading it into Amazon Redshift, and presenting business insights through Grafana dashboards.

The project demonstrates modern Data Engineering practices including serverless computing, event-driven architecture, cloud data warehousing, Infrastructure as Code (CloudFormation), monitoring, and automated data pipelines..

## Business Problem

Coffee shops generate thousands of sales transactions every day. Analysing CSV files manually is time-consuming, repetitive and prone to human error.

The aim of this project was to automate the entire analytics workflow so that sales data could be processed in near real time, providing business owners with reliable dashboards for monitoring revenue, customer trends and operational performance.

## 🚀 Solution Overview

The ETL pipeline is built using a cloud-native, event-driven architecture on Amazon Web Services (AWS). Each stage of the pipeline is responsible for processing the data efficiently, securely and automatically.

| **ETL Stage** | **AWS Service** | **Purpose** |
|---------------|-----------------|-------------|
| **Extract** | **Amazon S3** | Stores raw CSV transaction files and automatically triggers the ETL pipeline when new data is uploaded. |
| **Transform** | **AWS Lambda (ExtractTransform)** | Reads the CSV file, removes sensitive information, cleans and validates the data, restructures customer orders and prepares it for loading. |
| **Queue** | **Amazon SQS** | Decouples the transformation and loading stages, ensuring reliable message delivery and improving scalability and fault tolerance. |
| **Load** | **AWS Lambda (Load)** | Retrieves transformed data from the SQS queue and loads it into the Amazon Redshift data warehouse. |
| **Storage** | **Amazon Redshift** | Stores structured, analytics-ready data using a relational schema optimised for reporting and business intelligence. |
| **Monitoring** | **Amazon CloudWatch** | Collects Lambda execution logs and performance metrics used to monitor the health of the ETL pipeline. |
| **Visualisation** | **Grafana** | Connects to Amazon Redshift and CloudWatch to provide interactive business dashboards and operational monitoring. |
| **Infrastructure** | **AWS CloudFormation** | Deploys and manages the AWS infrastructure using Infrastructure as Code (IaC), ensuring consistent and repeatable deployments. |


![Grafana visualisations](https://github.com/agi-chan/mugshot-coffee/blob/main/visualisations.png?raw=true)
![Grafana monitoring](https://github.com/agi-chan/mugshot-coffee/blob/main/monitoring.png?raw=true)

## Team members

- Liam D <a href="https://www.github.com/Liam-Dignum" target="_blank">@Liam-Dignum</a>
- Alina A <a href="https://www.github.com/alina951" target="_blank">@alina951</a>
- Colvin S <a href="https://www.github.com/csrs42" target="_blank">@csrs42</a>
- Alex H <a href="https://www.github.com/agi-chan" target="_blank">@agi-chan</a>
  
## Project overview

Our ETL pipeline processes data through the following stages:

1. Extract: Retrieve data from CSV files which are uploaded to an S3 bucket
2. Transform: Normalise and clean the data in ExtractTransform Lambda.
3. Load: Data is sent to Load Lambda, which is then sent to a Redshift database
4. Visualise: Present insights through Grafana dashboards

## Architecture

![architecture](https://github.com/agi-chan/mugshot-cafe/blob/main/graph%20crop.png?raw=true)

![AWS architecture](https://github.com/agi-chan/mugshot-cafe/blob/main/aws.png?raw=true)

Our solution utilizes the following AWS components:

- S3: For storing raw CSV files
- Lambda: For ETL processing
- Redshift: As our data warehouse
- Cloudformation: To initialise infrastructure (bucket and Lambda) from .YAML template
- EC2

## Repository structure

```
Mugshot-Coffee/
├── .github/
│   └── workflows/
│       └── action.yml
├── Data/
│   ├── leeds_09-05-2023_09-00-00.csv
│   └── test_data.csv
├── lambda-layer/
│   └── lambda-layer.zip
├── .env
├── mugshot_lambda.py
├── load_lambda.py
├── extracttransform_lambda.py
├── README.md
├── connect_db.py
├── database.sql
├── docker-compose.yml
├── lambdatemplate.yaml
├── test_unit_tests.py
```
### Folder/Files Description

 - .github/: GitHub workflows and actions
 - .vscode/: Visual Studio Code settings.
 - Data/: Contains raw and sample data files
 - lambda-layer/: Python libraries for Lambda functions.
 - .env: Environment variables configuration.
 - Main.py: Main entry point of the application.
 - config.py: Configuration settings.
 - connect.py: Database connection utilities.
 - database.ini: Database configuration file.
 - database.sql: SQL scripts for database setup.
 - docker-compose.yml: Docker Compose configuration.
 - lambda.py: Lambda function code.
 - lambdatemplate.yaml: AWS CloudFormation template for Lambda functions.
 - test_unit_tests.py: Unit tests for the application.
 - transactions_data.csv: Sample transaction data.

## Getting Started

### Prerequisites

- Docker
- AWS CLI
- Python 3.12+

### Local setup

1. Clone the repository
   - git clone https://github.com/agi-chan/mugshot-coffee.git
   - cd Mugshot-Coffee
2. Set up envirnment variables
3. Install dependecies.
   - pip install -r requirements.txt
4. Run docker compose
   - docker-compose up
5. Deploy infrastructure (use aws cloudformation )
   - aws cloudformation create-stack --stack-name mugshot-coffee --template-body file://lambdatemplate.yaml
6. Run the application
   - python Main.py

### License
This project is licensed under the MIT License. See the LICENSE file for details.
