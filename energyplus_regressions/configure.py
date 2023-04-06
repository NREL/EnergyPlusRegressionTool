from plan_tools.entry_point import EntryPoint


def configure_cli() -> None:
    source_dir = "energyplus_regressions"
    name = "energyplus_regression_runner"
    description = "An EnergyPlus test suite utility"
    nice_name = "EnergyPlus Regression Tool"
    s = EntryPoint(source_dir, name, nice_name, description, name)
    s.run()
