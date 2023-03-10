"""
Libraries

"""

import torch
import torch.nn.functional as F

"""
Setting hyperparameters for the IMSAT algorithm 

"""

# Trade-off parameter for mutual information and smooth regularization
lam: float = 0.1
        
"""
...

"""

def mariginal_distribution(conditionals: torch.Tensor) -> torch.Tensor:
    """
    Approximates the mariginal probability according to Eq (15).
    
    Args:
        conditionals: conditional probabilities

    Returns
        An approximation of mariginal probabilities.
    """

    # Calculate the sums for each columns.
    return torch.sum(conditionals, dim=0) / conditionals.shape[0]

def shannon_entropy(probabilities: torch.Tensor) -> float:
    """
    Calculates the Shannon entropy of a set of probabilities.
    
    Args:
        probabilities:
    
    Returns:
        The Shannon entropy (float)
    """

    if probabilities.dim() == 1:
        return -torch.sum(probabilities * torch.log(probabilities))
    
    else:
        return -torch.sum(probabilities * torch.log(probabilities)) / probabilities.shape[0]


def mutual_information(mariginals: torch.Tensor, conditionals: torch.Tensor) -> float:
    """
    Calculate the mutual information between two discrete random variables. According to Eq. (7).
    
    Args:
        mariginals: Mariginal probabilities of X.
        conditionals: Conditional probabilities, X|Y.
    
    Returns:
        The mutual information between the two random variables.
    """
    
    marginal_entropy    = shannon_entropy(mariginals)
    conditional_entropy = shannon_entropy(conditionals)

    return marginal_entropy - conditional_entropy

def self_augmented_training(model, X: torch.Tensor, Y: torch.Tensor, eps: float = 1.0, ksi: float = 1e0, num_iters: int = 1) -> float:
    """
    Self Augmented Training by Virtual Adversarial Perturbation.
    
    Args:
        model: multi-output probabilistic classifier. 
        X: Input samples.
        Y: output when applying model on X.
        eps: Magnitude of perturbation.
        ksi: A small constant used for computing the finite difference approximation of the KL divergence.
        num_iters: The number of iterations to use for computing the perturbation.

    Returns:
        The total loss (sum of cross-entropy loss on original input and perturbed input) for the batch.

    """

    """
    Generate Virtual Adversarial Perturbation

    """

    #TODO Consider removing without breaking code
    y_pred = model(X)
    
    # Generate random unit tensor for perturbation direction
    d = torch.randn_like(X, requires_grad=True)
    d = F.normalize(d, p=2, dim=1)
    
    # Use finite difference method to estimate adversarial perturbation
    for _ in range(num_iters):
        # Forward pass with perturbation
        y_perturbed = model(X + ksi * d)
        
        # Calculate the KL divergence between the predictions with and without perturbation
        kl_div = F.kl_div(F.log_softmax(y_perturbed, dim=1), F.softmax(y_pred, dim=1), reduction='batchmean')
        
        # Calculate the gradient of the KL divergence w.r.t the perturbation
        grad = torch.autograd.grad(kl_div, d)[0]
        
        # Update the perturbation
        d = grad
        d = F.normalize(d, p=2, dim=1)
        d.requires_grad_()

    """
    Apply Perturbation and calculate the Kullback-Leibler divergence Loss

    """
    Y_p = F.softmax(model(X + eps * d), dim=1)

    loss = F.kl_div(Y.log(), Y_p, reduction='batchmean')
    
    return loss

def regularized_information_maximization(model, X: torch.Tensor, Y: torch.Tensor) -> float():
    """
    Computes the loss using regularized information maximization.

    Args:
        model: multi-output probabilistic classifier. 
        X: Input samples.
        Y: output when applying model on x.

    Returns:
        The loss given by mutual information and the regularization penalty.
    """

    conditionals = Y
    mariginals   = mariginal_distribution(conditionals)

    I = mutual_information(mariginals, conditionals)

    R_sat = self_augmented_training(model, X, Y)

    return R_sat - lam * I