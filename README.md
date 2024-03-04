# Tour de France Historic Stages Analysis

## Overview

This GitHub repository contains an analysis of historic Tour de France stages, along with calculations for estimating power requirements for cyclists during these stages. The analysis incorporates slope, weight, velocity, and stage profile to provide rough insights into the power demands of various Tour de France routes.

## Data

The dataset used for this analysis includes historical information about Tour de France stages, including details such as elevation, slope, distance, and rider performance. The data is organized to facilitate exploration and analysis of different aspects of the stages.

## Power Calculation

To estimate the power requirements for cyclists during Tour de France stages, a formule from [omnicalculator](https://www.omnicalculator.com/sports/cycling-wattage) is used. These formula take into account gravitational force, rolling resistance, aerodynamic drag, and stage profile. The power calculations are a VERY rough estimate for the power required for the GC rider of each year (or someone with similar weight) to complete each stage. These calculations dont take drafting into account and don't have the exact profile of each stage, the calculations for each type of stage can be found in [power_helper](power_helper.py).

## Usage

### Option 1: Build Docker Container

1. Clone the repository:
   ```bash
   git clone https://github.com/ToonElewaut/TDF.git
   ```

2. Navigate to the project directory:
   ```bash
   cd TDF
   ```

3. Build the Docker container:
   ```bash
   docker build -t tdf .
   ```

4. Run the Docker container:
   ```bash
   docker run -p 8050:8050 tdf
   ```

5. Open your web browser and visit [http://localhost:8050](http://localhost:8050) to access the application.

### Option 2: Run app.py in the src directory

1. Clone the repository:
   ```bash
   git clone https://github.com/ToonElewaut/TDF.git
   ```

2. Navigate to the project directory:
   ```bash
   cd TDF/src
   ```

3. Install dependencies (assuming you have Python and pip installed):
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your web browser and visit [http://localhost:8050](http://localhost:8050) to access the application.
