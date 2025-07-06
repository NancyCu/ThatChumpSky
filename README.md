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
Selecting the "Show Steps tab will list all the conversion steps as show below:

# Chomsky Normal Form (CNF) Conversion Walk-Through  

---

## 1  Add a New Start Symbol
```cfg
S0 → S
S  → A S A | a B
A  → B | S
B  → b | ε
```

---

## 2  Remove ε-Productions
```cfg
S0 → S
S  → A S A | S A | A S | S | a B | a
A  → B | S
B  → b
```

---

## 3  Remove Unit Productions
```cfg
S0 → A S A | S A | A S | a B | a
S  → A S A | S A | A S | a B | a
A  → b | A S A | S A | A S | a B | a
B  → b
```

---

## 4  Remove Useless Symbols
```cfg
S0 → A S A | S A | A S | a B | a
S  → A S A | S A | A S | a B | a
A  → b | A S A | S A | A S | a B | a
B  → b
```

---

## 5  Final Chomsky Normal Form
```cfg
A1 → S A
S0 → A A1 | S A | A S | U B | a
S  → A A1 | S A | A S | U B | a
A  → b | A A1 | S A | A S | U B | a
B  → b
U  → a
```


