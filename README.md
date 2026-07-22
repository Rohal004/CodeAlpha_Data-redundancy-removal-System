# CodeAlpha_Data-redundancy-removal-System

This project provides a lightweight redundancy-removal system for cloud data ingestion.

## Features
- Classifies incoming data as `unique`, `redundant`, or `false_positive`
- Validates each new entry against existing cloud database records
- Prevents duplicate records using normalization + database uniqueness
- Appends only verified unique entries to the database
- Keeps database accurate and efficient by avoiding redundancy at write time

## Usage
```bash
python dedup_system.py
```

## Run tests
```bash
python -m unittest -v
```
