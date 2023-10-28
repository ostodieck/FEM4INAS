import numpy as np
import jax.numpy as jnp
import jax
from jax import jit, lax
from fem4inas.preprocessor import configuration
from functools import partial

###############################
# Exponential map integration #
###############################

@jit
def tilde(vector3: jnp.ndarray):
    """Compute matrix that yields the cross product.

    Parameters
    ----------
    vector3 : jnp.ndarray
      Vector of length 3

    """
    tilde = jnp.array([[0.,    -vector3[2], vector3[1]],
                       [vector3[2],  0.,       -vector3[0]],
                       [-vector3[1], vector3[0], 0.]])
    return tilde

@jit
def H0(Itheta: float, Ipsi: jnp.ndarray):

    I3 = jnp.eye(3)
    # TODO: move 1e-9 to settings
    cond = jnp.abs(Itheta) > 1e-9 # if not true,
    # local-x is almost parallel to global-z, z direction parallel to global y
    y = lax.select(cond,
                   (I3 + jnp.sin(Itheta) / Itheta * tilde(Ipsi)
                   + (1 - jnp.cos(Itheta)) / Itheta**2 * jnp.matmul(tilde(Ipsi),
                                                                    tilde(Ipsi))),
                   I3)
    return y

@jit
def H1(Itheta: float, Ipsi: jnp.ndarray, ds: float):

    I3 = jnp.eye(3)
    cond = jnp.abs(Itheta) > 1e-9 # if not true,
    # local-x is almost parallel to global-z, z direction parallel to global y
    y = lax.select(cond,
                   ds * (I3 + (1 - jnp.cos(Itheta)) / Itheta**2 * tilde(Ipsi)
                        + (Itheta - jnp.sin(Itheta)) / (Itheta**3) * jnp.matmul(tilde(Ipsi),
                                                                                tilde(Ipsi))),
                   ds * I3)
    return y

@jit
def H0_t(Itheta: jnp.ndarray, Ipsi: jnp.ndarray):

    tn = len(Itheta)
    I3 = jnp.broadcast_to(jnp.eye(3), (tn, 3, 3)).T
    f_tilde = jax.vmap(tilde, in_axes=1, out_axes=2)
    f_tilde2 = jax.vmap(lambda u: u @ u, in_axes=2, out_axes=2)
    tilde_Ipsi = f_tilde(Ipsi)  # 3x3xNt
    tilde_Ipsi_square = f_tilde2(tilde_Ipsi) # 3x3xNt
    # TODO: move 1e-9 to settings
    cond = jnp.abs(Itheta) > 1e-9 # if not true,
    # local-x is almost parallel to global-z, z direction parallel to global y
    cond_broadcast = jnp.broadcast_to(cond, (3, 3, tn))
    y = lax.select(cond_broadcast,
                   (I3 + jnp.sin(Itheta) / Itheta * tilde_Ipsi
                    + (1 - jnp.cos(Itheta)) / Itheta**2 * tilde_Ipsi_square),
                   I3)
    return y

@jit
def H1_t(Itheta: float, Ipsi: jnp.ndarray, ds: float):

    tn = len(Itheta)
    I3 = jnp.broadcast_to(jnp.eye(3), (tn, 3, 3)).T
    f_tilde = jax.vmap(tilde, in_axes=1, out_axes=2)
    f_tilde2 = jax.vmap(lambda u: u @ u, in_axes=2, out_axes=2)
    tilde_Ipsi = f_tilde(Ipsi)  # 3x3xNt
    tilde_Ipsi_square = f_tilde2(tilde_Ipsi) # 3x3xNt
    # TODO: move 1e-9 to settings
    cond = jnp.abs(Itheta) > 1e-9 # if not true,
    cond_broadcast = jnp.broadcast_to(cond, (3, 3, tn))
    # local-x is almost parallel to global-z, z direction parallel to global y
    y = lax.select(cond_broadcast,
                   ds * (I3 + (1 - jnp.cos(Itheta)) / Itheta**2 * tilde_Ipsi
                        + (Itheta - jnp.sin(Itheta)) / (Itheta**3) * tilde_Ipsi_square),
                   ds * I3) #3x3xNt
    return y

@jit
def H01_t(Itheta: jnp.ndarray, Ipsi: jnp.ndarray):

    I3 = jnp.eye(3).reshape(3, 3, 1)
    f_tilde = jax.vmap(tilde, in_axes=1, out_axes=2)
    f_tilde2 = jax.vmap(lambda u: u @ u, in_axes=2, out_axes=2)
    tilde_Ipsi = f_tilde(Ipsi)  # 3x3xNt
    tilde_Ipsi_square = f_tilde2(tilde_Ipsi) # 3x3xNt
    # TODO: move 1e-9 to settings
    cond = jnp.abs(Itheta) > 1e-9 # if not true,
    # local-x is almost parallel to global-z, z direction parallel to global y
    y = lax.select(cond,
                   (I3 + jnp.sin(Itheta) / Itheta * tilde_Ipsi
                    + (1 - jnp.cos(Itheta)) / Itheta**2 * tilde_Ipsi_square),
                   I3)
    return y

@jit
def L1(x1: jnp.ndarray):

    L1 = jnp.zeros((6, 6))
    v = x1[0:3]
    w = x1[3:6]

    L1 = L1.at[0:3, 0:3].set(tilde(w))
    L1 = L1.at[3:6, 3:6].set(tilde(w))
    L1 = L1.at[3:6, 0:3].set(tilde(v))
    return L1

def tilde_np(vector3: np.ndarray):
    """Compute matrix that yields the cross product.

    Parameters
    ----------
    vector3 : jnp.ndarray
      Vector of length 3

    """
    tilde = np.array([[0.,    -vector3[2], vector3[1]],
                      [vector3[2],  0.,       -vector3[0]],
                      [-vector3[1], vector3[0], 0.]])
    return tilde

def L1_np(x1: np.ndarray):

    L1 = np.zeros((6, 6))
    v = x1[0:3]
    w = x1[3:6]

    L1[0:3, 0:3] = (tilde_np(w))
    L1[3:6, 3:6] = (tilde_np(w))
    L1[3:6, 0:3] = (tilde_np(v))
    return L1

@jit
def L2(x2: jnp.ndarray):

    L2 = jnp.zeros((6, 6))
    f = x2[0:3]
    m = x2[3:6]

    L2 = L2.at[0:3, 3:6].set(tilde(f))
    L2 = L2.at[3:6, 3:6].set(tilde(m))
    L2 = L2.at[3:6, 0:3].set(tilde(f))
    return L2

@partial(jit, static_argnames=['config'])
def compute_C0ab(X_diff: jnp.ndarray, X_xdelta: jnp.ndarray,
                 config: configuration.Config) -> jnp.ndarray:

    x = X_diff / X_xdelta #Nn
    x = x.at[:, 0].set(jnp.array([1, 0, 0])) # WARNING: this says the first node FoR at time 0
    # aligns with the global reference frame.
    # TODO: check this works when x_local = [0,0,1]
    cond = (jnp.linalg.norm(x - jnp.array([[0,0,1]]).T) >
            config.fem.Cab_xtol) # if not true,
    # local-x is almost parallel to global-z, z direction parallel to global y
    y = lax.select(cond,
                   jnp.cross(jnp.array([0, 0, 1]), x, axisb=0, axisc=0),
                   jnp.cross(jnp.array([0, 1, 0]), x, axisb=0, axisc=0))
    y /= jnp.linalg.norm(y, axis=0)
    z = jnp.cross(x, y, axisa=0, axisb=0, axisc=0)
    C0ab = jnp.stack([x, y, z], axis=1)
    return C0ab

@partial(jit, static_argnames=["precision"])
def coordinate_transform(u1: jnp.ndarray,
                         v1: jnp.ndarray,
                         precision) -> jnp.ndarray:
    """Applies a coordinate transformation

    to the 6-element component (dim=1) of a 3rd order tensor

    Parameters
    ----------
    u1 : jnp.ndarray
        Tensor to transform coordinates
    v1 : jnp.ndarray
        Node by node transpose transformation matrix:
    v1=Cab(6x6xNn) effectively does Cba.u1 along the Nn dimension


    """
    f = jax.vmap(lambda u, v: jnp.matmul(u, v, precision=precision), in_axes=(2, 2), out_axes=2)
    fuv = f(u1, v1)
    return fuv

def label_generator(label_table: dict):

    prime_numbers = [2, 3, 5, 7, 11, 13,
                     17, 19, 23, 29, 31,
                     37, 41, 43, 47, 53,
                     59, 61, 67, 71, 73,
                     79, 83, 89, 97]
    label = label_table[0]
    prod = 1
    for i, li in enumerate(label_table[1:]):
        prod *= prime_numbers[i] ** int(li)
    label += str(prod)
    return label
