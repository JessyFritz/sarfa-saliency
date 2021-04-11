# Interpreting Chess Evaluation Functions

### SARFA
Link to the original SARFA paper - [SARFA paper](https://arxiv.org/abs/1912.12191) 

Link to the SARFA project https://github.com/nikaashpuri/sarfa-saliency

### My Contributions
All executions and evaluations can be called from the [databaseHandler](databaseHandler.py).
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
       positions in FEN notation with solution moves and ground truth analysis can be found [here](chess_saliency_databases\bratko-kopec)  
       engines' executed puzzles can be found [here](evaluation\bratko-kopec)
     - endgames  
       positions in PGN notation can be found [here](chess_saliency_databases\endgames\endgames.pgn)  
       engines' executed puzzles can be found [here](evaluation\endgames)
2. Improvement suggestions
   - increasing saliency based on Δp and K  
     implemented in [chess_saliency_combination.py](chess_saliency_combination.py)
   - introducing chess specific cases  
     implemented in [chess_saliency_chessSpecific.py](chess_saliency_chessSpecific.py)
   - adaptation for Leela  
     implemented in [chess_saliency_leela.py](chess_saliency_leela.py)
3. Graphical User Interface
   - I designed a GUI app based on my chess specific improvements for Windows and Linux. It can be accessed at https://1drv.ms/u/s!AlDdfpwNjFy8ugvC4tlZxOXgi8L6?e=8dRWNa.
     Just download the correct folder and unzip it anywhere you want. They come preinstalled with at least 4 engines, but you can add engines of your own choice.

### Dependencies
1. Python3
2. Packages listed in requirements.txt

### Using Saliency Maps to Interpret Chess Boards
1. Clone Repository
    ```
    git clone https://github.com
    ```
2. Navigage to cloned repository
    ```
    cd sarfa-saliency
    ```
3. Install all dependencies using pip
    ```
    pip install -r requirements.txt
    ```
