from plan_tools.entry_point import EntryPoint


def configure_cli() -> None:
    source_dir = "energyplus_regressions"
    name = "energyplus_regression_runner"
    nice_name = "EnergyPlus Regression Tool"
    s = EntryPoint(source_dir, name, nice_name, "An EnergyPlus test suite utility", name)
    s.run()
