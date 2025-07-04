# CFG to CNF Converter

This project provides a simple Streamlit interface for converting context-free grammars (CFG) into Chomsky Normal Form (CNF).

## Installation

Use pip to install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

This will open a browser window where you can paste your CFG and view the CNF conversion steps.

## Example CFG Format

Enter productions one per line using `->` (or `→`) and separate alternatives with `|`.
Epsilon (the empty string) can be written as `ε` or `E`.

```
S -> AB | a
A -> aA | ε
B -> b
```

After entering your grammar, click **Convert to CNF** to see the transformed grammar and the step-by-step process.

