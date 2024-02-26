# Tour de France Historic Stages Analysis

## Overview

This GitHub repository contains an analysis of historic Tour de France stages, along with calculations for estimating power requirements for cyclists during these stages. The analysis incorporates slope, weight, velocity, and stage profile to provide rough insights into the power demands of various Tour de France routes.

## Data

The dataset used for this analysis includes historical information about Tour de France stages, including details such as elevation, slope, distance, and rider performance. The data is organized to facilitate exploration and analysis of different aspects of the stages.

## Power Calculation

To estimate the power requirements for cyclists during Tour de France stages, a formule from [omnicalculator](https://www.omnicalculator.com/sports/cycling-wattage) is used. These formula take into account gravitational force, rolling resistance, aerodynamic drag, and stage profile. The power calculations are a VERY rough estimate for the power required for the GC rider of each year (or someone with similar weight) to complete each stage. These calculations dont take drafting into effect and don't have the exact profile of each stage, the calculations for each type of stage can be found in [power_helper](power_helper.py).

## Usage

Create_dataset.ipynb is used to update the dataset if needed.
Stage_analysis.ipynb has some graphs comparing power and speed numbers over the years.