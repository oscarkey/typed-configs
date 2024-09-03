# typed-configs
A simple config system where you define your config using dataclasses with defaults, and then can specify overrides on the command line.

There are lots of existing options for this (e.g. [typed-argument-parser](https://github.com/swansonk14/typed-argument-parser), [Hydra](https://hydra.cc/docs/tutorials/structured_config/intro/)). None of them were quite right for me, so I wrote my own.


## Features
- Very simple
- Statically type checkable
- Convert the parsed config to a dict using `dataclasses.asdict()` to pass it to e.g. [Weights & Biases](https://wandb.ai/)

Future plans:
- Allow defining multiple sets of default values

## Usage
```
@dataclass
class Config:
    subconfig: SubConfig = SubConfig()
    option1: int = 3
    option2: Optional[str] = None

@dataclass
class SubConfig:
    option: tuple[int, int] = (3, 5)

def main(config: Config) -> None:
    ...

if __name__ == "__main__":
    main(typed_configs.parse(Config))
```

Then, you can override options on the command line: `python script.py option1=5 subconfig.option=(1,2)`


## Dev
- Set up environment by installing [Poetry](https://python-poetry.org/) and running `poetry install`
- Format with `black **/*.py`, `isort **/*.py`
- Run type checker with `mypy -p typed_configs`
- Run tests with `pytest`
