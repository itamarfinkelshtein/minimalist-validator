# Minimalist Program Syntax Engine & LF Validator

An interactive, full-stack computational engine that operationalizes generative syntax under Noam Chomsky's **Minimalist Program**. 

The application translates abstract syntactic operations into formal graph-theoretic algorithms. Users construct syntactic derivations via an interactive drag-and-drop workspace, inspect bottom-up tree generation, execute probe-goal feature valuing, perform internal merge with trace preservation, and validate whether derivations converge at **Logical Form (LF)**.

---

## Theoretical Foundations & Architecture

The engine bridges formal linguistic theory with computer science data structures:

* **Syntactic Objects as Graphs**: Trees are modeled as binary Directed Acyclic Graphs (DAGs) using a custom `Node` class.
* **External Merge**: Merges two independent roots into a binary branching structure. Selectional features (e.g., `[uD]`, `[uv]`, `[uC]`) are evaluated and checked strictly under sisterhood conditions.
* **Internal Merge / Move**: Clones an extraction goal into the root's Specifier position. The base copy is replaced with an inert structural trace (`_t`) that retains its categorical identity for selection while shedding A-position features to prevent intervention effects.
* **Agree & C-Command Traversal**: Probes initiate a Depth-First Search (DFS) strictly over their c-command domain (sister's descendants). The traversal enforces strict structural hierarchy: Specifiers precede Complements to preserve Relativized Minimality.
* **Feature Percolation**: Models Determiner Phrases (DPs) where interpretable $\varphi$-features on lexical nouns percolate up to the maximal projection of $D$ to be visible for higher agreement probes.
* **LF Convergence**: Traverses the derived tree to ensure the Principle of Full Interpretation holds: derivations converge if and only if all uninterpretable features (`uF`) are checked.

---

## Tech Stack

* **Backend**: Python 3, Flask, Flask-CORS
* **Frontend**: Vanilla HTML5, CSS3 (Flexbox architecture), Vanilla JavaScript (Drag and Drop API, Fetch API)
* **Serialization & Export**: Recursive JSON tree encoder/decoder preserving specifier/complement branch geometry, alongside a Pre-Order Traversal LaTeX generator that maps visual objects directly to `forest`/TikZ syntax.

---

## Project Structure

```text
minimalist-validator/
│
├── backend/
│   ├── app.py              # Flask REST API endpoints & tree reconstruction
│   ├── lexicon.py          # Feature and LexicalItem data structures
│   ├── operations.py       # Core generative operations (Merge, Agree, Move)
│   ├── tree.py             # Binary Node graph logic & C-command domain computation
│   └── validator.py        # LF convergence inspection algorithm
│
├── frontend/
│   ├── index.html          # Interactive derivation workspace & collapsible lexicon
│   ├── script.js           # DOM manipulation, API callers, JSON/LaTeX exporters
│   └── styles.css          # Flexbox layout, horizontal tree scaffolding, UI styling
│
└── README.md
```

---

## Setup & Local Run

### Prerequisites
* Python 3.10+
* Modern web browser (Chrome, Firefox, Edge)

### 1. Start the Flask Backend
```bash
# Navigate to the backend directory
cd backend

# Install dependencies if not already installed
pip install flask flask-cors

# Run the API server
python app.py
```
The backend server runs locally on `http://127.0.0.1:5000`.

### 2. Launch the Frontend
Open `frontend/index.html` directly in your browser, or serve it via a simple static file server.

---

## Example Derivations

### Transitive Clause with Light $v$ Shell
*Sentence: "John ate apples"*
1. Merge `V [uD]` with `DP [3sg]` $\rightarrow$ Forms `VP`.
2. Merge `v [uV, uD]` with `VP` $\rightarrow$ Checks `[uV]`, leaves `[uD]`.
3. Merge `DP [3sg]` (Subject) with `vP` $\rightarrow$ Forms full transitive `vP`.
4. Merge `T [uφ, uv]` with `vP` $\rightarrow$ Forms `TP`.
5. Run **Agree** on `T` $\rightarrow$ Probes down, values $\varphi$-features against the subject in SPEC `vP`.
6. Run **Internal Merge** on the subject $\rightarrow$ Elevates subject to Spec-TP, leaving a trace `DP_t`.
7. **Validate LF** $\rightarrow$ Converges.

### Recursive Complementizer Embedding
*Sentence: "I know that John ate apples"*
1. Construct embedded `TP` as above.
2. Merge `C [uT]` with embedded `TP` $\rightarrow$ Forms embedded `CP`.
3. Merge matrix `V [uC]` with the embedded `CP` $\rightarrow$ Forms matrix `VP`.
4. Construct matrix `vP` shell with subject `DP [1sg]`, merge matrix `T`, execute matrix **Agree** and **Move**.
5. **Validate LF** $\rightarrow$ Validates matrix clause and embedded clause simultaneously.
