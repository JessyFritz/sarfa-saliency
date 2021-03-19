"""
contains original code of SARFA authors https://github.com/nikaashpuri/sarfa-saliency
added file handling in order to save puzzles' outputs into a folder
"""

from tkinter import END
import numpy as np
from scipy.stats import entropy


def your_softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()


def cross_entropy(dictP, dictQ, original_action):
    """
    This function calculates normalized cross entropy (KL divergence) of Q-values of state Q wrt state P.
    Input :
        dictP : Q-value dictionary of perturbed state
        dictQ : Q-value dictionary of original state
    Output : p = policy[:best_move+1]
             p = np.append(p, policy[best_move+1:])
             K: normalized cross entropy
    """
    Q_p = [] # values of moves in dictP^dictQ wrt P
    Q_q = [] # values of moves in dictP^dictQ wrt Q
    for move in dictP:
        if move == original_action:
            # print('skipping original action for KL-Divergence')
            continue
        if move in dictQ:
            Q_p.append(dictP[move])
            Q_q.append(dictQ[move])
    # converting Q-values into probability distribution
    if len(Q_p) > 0 and len(Q_q) > 0:
        Q_p = your_softmax(np.asarray(Q_p))
        Q_q = your_softmax(np.asarray(Q_q))
        KL = entropy(Q_q, Q_p)
        return 1./(KL + 1.)
    return None


def computeSaliencyUsingSarfa(original_action, dict_q_vals_before_perturbation, dict_q_vals_after_perturbation, file=None, text=None):
    answer = 0

    # probability of original move in perturbed state
    q_value_action_perturbed_state = dict_q_vals_after_perturbation[original_action] # Q(s',â)
    q_value_action_original_state = dict_q_vals_before_perturbation[original_action] # Q(s,â)
    if text is None:
        file.write("perturbed reward Q(s\',â): {}, original reward Q(s,â): {}\n".format(q_value_action_perturbed_state, q_value_action_original_state))
    else:
        text.insert(END, "perturbed reward Q(s\',â): {}, original reward Q(s,â): {}\n".format(q_value_action_perturbed_state, q_value_action_original_state))

    q_values_after_perturbation = np.asarray(list(dict_q_vals_after_perturbation.values())) # Q(s',a)
    q_values_before_perturbation = np.asarray(list(dict_q_vals_before_perturbation.values())) # Q(s,a)
    
    # P(s',â) = exp(Q(s',â))/Σexp(Q(s',a))
    probability_action_perturbed_state = np.exp(q_value_action_perturbed_state) / np.sum(np.exp(q_values_after_perturbation)) 
    # P(s,â) = exp(Q(s,â))/Σexp(Q(s,a))
    probability_action_original_state = np.exp(q_value_action_original_state) / np.sum(np.exp(q_values_before_perturbation))
    
    # K = 1/(1+DKL),        DKL = Prem(s',a)||Prem(s,a),        Prem(s,a) = exp(Q(s,a))/Σexp(Q(s,a'))
    K = cross_entropy(dict_q_vals_after_perturbation, dict_q_vals_before_perturbation, original_action)

    # ∆p = P(s,â) - P(s',â)
    dP = probability_action_original_state - probability_action_perturbed_state

    if probability_action_perturbed_state < probability_action_original_state: # harmonic mean
        answer = 2*dP*K/(dP + K)     
        
    QmaxAnswer = computeSaliencyUsingQMaxChange(original_action, dict_q_vals_before_perturbation, dict_q_vals_after_perturbation)
    action_gap_before_perturbation, action_gap_after_perturbation = computeSaliencyUsingActionGap(dict_q_vals_before_perturbation, dict_q_vals_after_perturbation)

    return answer, dP, K, QmaxAnswer, action_gap_before_perturbation, action_gap_after_perturbation


def computeSaliencyUsingQMaxChange(original_action, dict_q_vals_before_perturbation, dict_q_vals_after_perturbation):
    answer = 0

    best_action = None 
    best_q_value = 0

    for move, q_value in dict_q_vals_after_perturbation.items():
        if best_action is None:
            best_action = move
            best_q_value = q_value
        elif q_value > best_q_value:
           best_q_value = q_value
           best_action = move 

    if best_action != original_action:
        answer = 1
    
    return answer


def computeSaliencyUsingActionGap(dict_q_vals_before_perturbation, dict_q_vals_after_perturbation):
    if len(dict_q_vals_before_perturbation) > 1 and len(dict_q_vals_after_perturbation) > 1:
        q_vals_before_perturbation = sorted(dict_q_vals_before_perturbation.values())
        q_vals_after_perturbation = sorted(dict_q_vals_after_perturbation.values())
        action_gap_before_perturbation = q_vals_before_perturbation[-1] - q_vals_before_perturbation[-2]
        action_gap_after_perturbation = q_vals_after_perturbation[-1] - q_vals_after_perturbation[-2]

        return action_gap_before_perturbation, action_gap_after_perturbation
    return None, None

