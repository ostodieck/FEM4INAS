from fem4inas.drivers.driver import Driver

import fem4inas.simulations
from fem4inas.preprocessor import solution, configuration


class IntrinsicDriver(Driver, cls_name="intrinsic"):
    """Driver for the modal intrinsic theory

    Creates simulation, systems and solution data objects and calls
    the pre-simulation and the simulation public methods

    Parameters
    ----------
    config : config.Config
         Configuration object

    Attributes
    ----------
    _config : see Parameters
    simulation :
    sol :
    systems :

    """

    def __init__(self, config: configuration.Config):
        """

        Parameters
        ----------
        config : config.Config
            Configuration object

        """

        self._config = config
        self.simulation = None
        self.sol = None
        self.systems = None
        self.num_systems = 0
        self._set_systems()
        self._set_simulation()
        self._set_sol()

    def pre_simulation(self):
        # TODO: here the RFA for aerodynamics should be included
        # TODO: condensation methods of K and M should be included
        if self._config.driver.compute_presimulation:
            self._compute_modalshapes()
            self._compute_modalcouplings()
        else:
            self._load_modalshapes()
            self._load_modalcouplings()

    def run_case(self):
        if self.num_systems == 0:
            print("no systems in the simulation")
        else:
            self.simulation.trigger()

    def _set_simulation(self):
        # Configure the simulation
        if hasattr(self._config, "simulation"):
            cls_simulation = fem4inas.simulations.factory(
                self._config.simulation.typeof
            )
            self.simulation = cls_simulation(
                self.systems, self.sol, self._config.simulation
            )
        else:
            print("no simulation settings")

    def _set_systems(self):
        self.systems = dict()
        if hasattr(self._config, "systems"):
            for k, v in self._config.systems.sys.items():
                cls_sys = fem4inas.systems.factory(v.typeof)
                self.systems[k] = cls_sys(k, v, self._config.fem, self.sol)
        self.num_systems = len(self.systems)

    def _set_sol(self):
        # Configure the simulation
        self.sol = solution.IntrinsicSolution(self._config.driver.solution_path)

    def _compute_modalshapes(self):
        # if self._config.numlib == "jax":
        import fem4inas.intrinsic.modes as modes

        # elif self._config.numlib == "numpy":
        #    import fem4inas.intrinsic.modes_np as modes

        modal_analysis = modes.shapes(
            self._config.fem.X.T, self._config.fem.Ka, self._config.fem.Ma, self._config
        )
        modal_analysis_scaled = modes.scale(*modal_analysis)
        modes.check_alphas(
            *modal_analysis_scaled, tolerance=self._config.jax_np.allclose
        )
        self.sol.add_container("Modes", *modal_analysis_scaled)

    def _compute_modalcouplings(self):
        # if self._config.numlib == "jax":
        import fem4inas.intrinsic.couplings as couplings

        # elif self._config.numlib == "numpy":
        #    import fem4inas.intrinsic.couplings_np as couplings

        gamma1 = couplings.f_gamma1(self.sol.data.modes.phi1,
                                    self.sol.data.modes.psi1)
        gamma2 = couplings.f_gamma2(
            self.sol.data.modes.phi1ml,
            self.sol.data.modes.phi2,
            self.sol.data.modes.psi2l,
            self.sol.data.modes.X_xdelta,
        )

        self.sol.add_container("Couplings", gamma1, gamma2)

    def _load_modalshapes(self):
        self.sol.load_container("Modes")

    def _load_modalcouplings(self):
        self.sol.load_container("Couplings")