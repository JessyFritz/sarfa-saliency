# Interpreting Chess Evaluation Functions

### SARFA
Link to the original SARFA paper - [SARFA paper](https://arxiv.org/abs/1912.12191)

Link to the SARFA project https://github.com/nikaashpuri/sarfa-saliency

### Our Contributions
Conference on Games 2021 [Proceeding](https://ieee-cog.org/2021/assets/papers/paper_180.pdf), written by Jessica Fritz & Johannes Fürnkranz

All executions and evaluations can be called from the [main.py](main.py).
1. [Original SARFA implementation](chess_saliency_original.py) evaluation on Windows with
   - different chess engines (see [engines](engines) folder)
     - Fruit 2.2.1
     - Komodo 12.1.1
     - Lc0 v0.26.3 (had to be removed from the commit because the files were too large)
     - Octochess r5190
     - Rybka 2.3.2a
     - Stockfish 11
     - Stockfish 12  
   - different puzzle types (see [databases](chess_saliency_databases) folder)
     - strategic vs tacical positions: Bratko-Kopec Test  
       positions in FEN notation with solution moves and ground truth analysis can be found [here](https://github.com/JessyFritz/sarfa-saliency/tree/master/chess_saliency_databases/bratko-kopec)  
       engines' executed puzzles can be found [here](https://github.com/JessyFritz/sarfa-saliency/tree/master/evaluation/bratko-kopec)
     - endgames  
       positions in PGN notation can be found [here](https://github.com/JessyFritz/sarfa-saliency/tree/master/chess_saliency_databases/endgames/endgames.pgn)  
       engines' executed puzzles can be found [here](https://github.com/JessyFritz/sarfa-saliency/tree/master/evaluation/endgames)
2. Improvement suggestions
   - introducing chess specific cases  
     implemented in [chess_saliency_chessSpecific.py](chess_saliency_chessSpecific.py)
   - increasing saliency based on Δp and K  
     implemented in [chess_saliency_combination.py](chess_saliency_combination.py)
3. Chess Saliency Map Graphical User Interface
   - can be downloaded [here](https://github.com/JessyFritz/sarfa-saliency/releases)

### Dependencies
1. Python3
2. Packages listed in requirements.txt

### Using Saliency Maps to Interpret Chess Boards
1. Clone Repository
    ```
    git clone https://github.com/JessyFritz/sarfa-saliency
    ```
2. Navigage to cloned repository
    ```
    cd sarfa-saliency
    ```
3. Install all dependencies using pip
    ```
    pip install -r requirements.txt
    ```
