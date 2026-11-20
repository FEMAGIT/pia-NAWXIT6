"""Caricamento e accesso alla configurazione YAML."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


class Settings:
    """Contenitore della configurazione letta da `settings.yaml`.

    * il file YAML si modifica senza toccare codice Python;
    * una sezione mancante genera un errore chiaro all'avvio.

    Ogni sezione viene restituita come copia: chi la riceve può modificarla
    senza alterare la configurazione condivisa.
    """

    REQUIRED_SECTIONS = ("run", "evaluation", "model", "tiling", "roi", "recognition", "input", "logging", "export")

    def __init__(self, raw_config: dict[str, Any], base_dir: Path = Path(".")):
        """
        Args:
            raw_config: Contenuto del file YAML.
            base_dir: Cartella rispetto a cui si risolvono i percorsi relativi.

        Raises:
            KeyError: Se manca una delle sezioni obbligatorie.
        """
        missing = [s for s in self.REQUIRED_SECTIONS if s not in raw_config]
        if missing:
            raise KeyError(f"Sezioni mancanti nel file di configurazione: {missing}")
        self._config = raw_config
        self.base_dir = Path(base_dir)

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "Settings":
        """Legge la configurazione da un file YAML."""
        config_path = Path(config_path)
        with config_path.open("r", encoding="utf-8") as handle:
            return cls(yaml.safe_load(handle) or {}, base_dir=config_path.parent)

    def section(self, name: str) -> Any:
        """Copia di una sezione (o di un valore) della configurazione."""
        return copy.deepcopy(self._config[name])

    def path(self, value: str | None) -> Path | None:
        """Percorso del file YAML risolto rispetto alla sua cartella (None resta None)."""
        return None if value is None else self.base_dir / value
