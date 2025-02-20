import logging
import os

import matplotlib.pyplot as plt
import numpy as np

from algorithms.kmeans import KMeans
from utils.plotting import get_colors


class FuzzyCMeans(KMeans):
    def __init__(self, m: int, epsilon=0.01, **kwargs):
        """

        :param m: Degree of fuzziness (1 - crisp)
        """
        self.m = m
        self.epsilon = epsilon

        super().__init__(**kwargs)

    def _init_centroids(self):
        """Initialize centroids (V) and c-partition matrix U"""
        super()._init_centroids()
        self._init_u()

    def _init_u(self):
        """Initialize matrix U (K, n) with random values such that each column adds up to 1."""
        u = np.random.random(size=(self.K, self.X.shape[0]))
        self.u = u / u.sum(axis=0)[None, :]

    def _compute_centroids(self, *args):
        """
        Update c-partition matrix U and centroids (centers of gravity) V.
        :param args: Ignored for inheritance interface design.
        """
        self._update_v()
        logging.debug(f'({self.it:3}/{self.max_it}) Loss after updating V: {self._loss():.6f}')

        self._update_u()
        logging.debug(f'({self.it:3}/{self.max_it}) Loss after updating U: {self._loss():.6f}')

    def _update_v(self):
        """
        Update centroids (centers of gravity) V.
        v_k = ∑_i ((U_ki ^ m) * x_i) / ∑_i (U_ki ^ m)
        """
        u_pow_m = self.u ** self.m
        n_term = u_pow_m @ self.X
        d_term = u_pow_m.sum(axis=1, keepdims=True)
        self.centroids = n_term / d_term

    def _loss(self):
        """

        :return:
        """
        # TODO: Vectorize
        res = 0
        for i in range(self.X.shape[0]):
            for k in range(self.K):
                res += (self.u[k, i] ** self.m) * np.linalg.norm(self.X[i] - self.centroids[k]) ** 2
        return res

    def _update_u(self):
        # TODO: Vectorize
        for k in range(self.K):
            for i in range(self.X.shape[0]):
                u_ki = 0
                num = np.linalg.norm(self.X[i, :] - self.centroids[k])
                for j in range(self.u.shape[0]):
                    den = np.linalg.norm(self.X[i, :] - self.centroids[j])
                    u_ki += (num / den) ** (2 / (self.m - 1))
                u_ki **= -1
                self.u[k, i] = u_ki

        self.u = self.u / self.u.sum(axis=0)[None, :]

    def _check_convergence(self, previous_centroids):
        if self.it >= self.max_it:
            return True
        if previous_centroids is not None:
            return np.linalg.norm(self.centroids - previous_centroids, ord=1) < self.epsilon
        return False

    def _display_iteration(self, X, nearest_idx):
        if self.vis_dims == 0:
            return

        f, ax = plt.subplots(self.K, 1, figsize=(self.K, 6))

        colors = get_colors(self.K)
        ax[0].set_title('Membership Functions')

        for idx in range(self.K):
            ax[idx].plot(self.u[idx, :], c=colors[idx])
            ax[idx].tick_params(labelsize=6)
            ax[idx].set_ylim((0, 1))

        if self.fig_save_path is None:
            plt.show()
        else:
            directory = os.path.join(self.fig_save_path, self.__class__.__name__)
            if not os.path.exists(directory):
                os.mkdir(directory)
            plt.savefig(os.path.join(directory, f'{self.name}_K{self.K}_{self.it}.png'))
        plt.close()

    def predict(self, X: np.ndarray):
        # TODO: What if predict with different data
        return self.u, self.centroids

    def crisp_predict(self, X: np.ndarray):
        return super().predict(X)
