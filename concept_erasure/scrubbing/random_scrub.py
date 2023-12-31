from contextlib import contextmanager
from functools import partial
from typing import TYPE_CHECKING

import torch
from torch import Tensor, nn

if (
    TYPE_CHECKING
):  # Don't import this unless we're type checking, since it's slow to import
    from transformers import PreTrainedModel

from ..utils import is_norm_layer


@contextmanager
def random_scrub(model: "PreTrainedModel", subspace_dim: int):
    """Add hooks to the model which erase a random subspace during `forward`."""
    d = model.config.hidden_size

    u = torch.empty(d, subspace_dim, device=model.device, dtype=model.dtype)
    nn.init.orthogonal_(u)

    def random_erase(_, __, x: Tensor, u: Tensor) -> Tensor:
        return x - u @ (u.T @ x)

    handles = [
        mod.register_forward_hook(partial(random_erase, u=u))
        for mod in model.modules()
        if is_norm_layer(mod)
    ]

    try:
        yield
    finally:
        # Make sure to remove the hooks even if an exception is raised
        for handle in handles:
            handle.remove()
