from tqdm.auto import tqdm


class ProgressBar:
    def __init__(
        self,
        total: int,
        desc: str = "Processing",
        color: str = "green",
        unit: str = "item",
    ) -> None:
        self._bar = tqdm(total=total, desc=desc, colour=color, unit=unit)

        self._total = total
        self._counter = 0

    def update(self):
        self._bar.set_postfix_str(f"{self._counter} / {self._total}")
        self._bar.update(1)

    def close(self):
        self._bar.close()